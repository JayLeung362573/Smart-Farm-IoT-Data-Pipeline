import os
import uuid

import psycopg2
import pytest
from psycopg2.extras import RealDictCursor


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
                    ROUND(AVG(mv.avg_moisture)::numeric, 2) AS avg_moisture,
                    ROUND(AVG(mv.avg_temperature)::numeric, 2) AS avg_temp
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