import os
import uuid

import psycopg2
import pytest
from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient


pytestmark = pytest.mark.integration


def _db_params():
    return {
        "host": os.getenv("DB_HOST", "db"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "smart_farm"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "3221"),
    }


def _require_integration_enabled():
    if os.getenv("RUN_DB_INTEGRATION") != "1":
        pytest.skip("Set RUN_DB_INTEGRATION=1 to run database-backed integration tests.")


def test_insert_sensor_reading_refresh_view_and_query_summary():
    _require_integration_enabled()

    event_id = str(uuid.uuid4())

    conn = psycopg2.connect(**_db_params())
    conn.autocommit = True

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*) AS count FROM sensors;")
            sensor_count = cur.fetchone()["count"]
            assert sensor_count >= 500

            cur.execute(
                """
                INSERT INTO sensor_data (sensor_id, moisture, temperature, event_id)
                VALUES (%s, %s, %s, %s);
                """,
                (1, 42.5, 21.0, event_id),
            )

            cur.execute("REFRESH MATERIALIZED VIEW hourly_sensor_stats;")

            cur.execute(
                """
                SELECT sensor_id, moisture, temperature, event_id
                FROM sensor_data
                WHERE event_id = %s;
                """,
                (event_id,),
            )
            inserted = cur.fetchone()

            assert inserted is not None
            assert inserted["sensor_id"] == 1
            assert inserted["moisture"] == 42.5
            assert inserted["temperature"] == 21.0
            assert str(inserted["event_id"]) == event_id

            cur.execute(
                """
                SELECT
                    f.name AS field_name,
                    SUM(mv.sample_count) AS total_readings,
                    ROUND(
                        (SUM(mv.sum_moisture) / NULLIF(SUM(mv.sample_count), 0))::numeric,
                        2
                    ) AS avg_moisture,
                    ROUND(
                        (SUM(mv.sum_temperature) / NULLIF(SUM(mv.sample_count), 0))::numeric,
                        2
                    ) AS avg_temp
                FROM fields f
                JOIN sensors s ON f.field_id = s.field_id
                JOIN hourly_sensor_stats mv ON s.sensor_id = mv.sensor_id
                WHERE f.field_id = %s
                GROUP BY f.name;
                """,
                (1,),
            )
            summary = cur.fetchone()

            assert summary is not None
            assert summary["field_name"] == "North Field"
            assert summary["total_readings"] >= 1
            assert summary["avg_moisture"] is not None
            assert summary["avg_temp"] is not None

    finally:
        conn.close()

@pytest.mark.parametrize(
    "groups, expected_moisture, expected_temperature",
    [
        pytest.param(
            [(1, 20.0, 10.0), (9, 60.0, 30.0)],
            56.0,
            28.0,
            id="unequal-sample-counts",
        ),
        pytest.param(
            [(2, 20.004, 10.004), (1, 20.014, 10.014)],
            20.01,
            10.01,
            id="round-only-final-average",
        ),
    ],
)
def test_field_summary_uses_unrounded_sums(
    monkeypatch, groups, expected_moisture, expected_temperature
):
    _require_integration_enabled()

    import src.api as api

    conn = psycopg2.connect(**_db_params())

    # Reuse this real connection so the endpoint can see the
    # test's uncommitted data. SQL execution is not mocked.
    database_pool = MagicMock()
    database_pool.getconn.return_value = conn
    monkeypatch.setattr(api, "db_pool", database_pool, raising=False)

    field_name = f"summary_{uuid.uuid4().hex}"
    reading_time = datetime(2026, 3, 15, 12, tzinfo=timezone.utc)

    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO fields (name) VALUES (%s) RETURNING field_id;",
                (field_name,),
            )
            field_id = cur.fetchone()[0]

            for count, moisture, temperature in groups:
                cur.execute(
                    """
                    INSERT INTO sensors (field_id)
                    VALUES (%s)
                    RETURNING sensor_id;
                    """,
                    (field_id,),
                )
                sensor_id = cur.fetchone()[0]

                cur.executemany(
                    """
                    INSERT INTO sensor_data (
                        sensor_id, moisture, temperature,
                        created_at, event_id
                    )
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    [
                        (
                            sensor_id,
                            moisture,
                            temperature,
                            reading_time,
                            str(uuid.uuid4()),
                        )
                        for _ in range(count)
                    ],
                )

            cur.execute(
                "REFRESH MATERIALIZED VIEW hourly_sensor_stats;"
            )

        with TestClient(api.app) as client:
            response = client.get(f"/fields/{field_id}/summary")

        assert response.status_code == 200
        summary = response.json()

        assert summary["field_name"] == field_name
        assert summary["total_readings"] == sum(
            count for count, _, _ in groups
        )
        assert summary["avg_moisture"] == pytest.approx(
            expected_moisture
        )
        assert summary["avg_temp"] == pytest.approx(
            expected_temperature
        )
        database_pool.putconn.assert_called_once_with(conn)

    finally:
        # Undo the inserted data and materialized-view refresh.
        try:
            conn.rollback()
        finally:
            conn.close()