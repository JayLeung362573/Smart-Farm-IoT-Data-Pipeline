from datetime import datetime, timezone
from unittest.mock import MagicMock

import psycopg2
import pytest
from fastapi.testclient import TestClient
import src.api as api


client = TestClient(api.app)


@pytest.fixture
def mock_database(monkeypatch):
    database_pool = MagicMock()
    connection = database_pool.getconn.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    monkeypatch.setattr(api, "db_pool", database_pool, raising=False)
    return database_pool, connection, cursor


def test_health_check_returns_online_status():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "online",
        "message": "Smart Farm API is responding"
    }


def test_latest_reading_returns_404_when_no_reading_exists(mock_database):
    database_pool, connection, cursor = mock_database
    cursor.fetchone.return_value = None

    response = client.get("/sensors/42/latest")

    assert response.status_code == 404
    assert response.json() == {"detail": "No data found for sensor 42"}
    database_pool.putconn.assert_called_once_with(connection)


def test_latest_reading_returns_existing_reading(mock_database):
    database_pool, connection, cursor = mock_database
    cursor.fetchone.return_value = {
        "sensor_id": 42,
        "moisture": 45.5,
        "temperature": 21.0,
        "created_at": datetime(2026, 10, 16, 12, 0, tzinfo=timezone.utc),
    }

    response = client.get("/sensors/42/latest")

    assert response.status_code == 200
    assert response.json() == {
        "sensor_id": 42,
        "moisture": 45.5,
        "temperature": 21.0,
        "created_at": "2026-10-16T12:00:00+00:00",
    }
    database_pool.putconn.assert_called_once_with(connection)


def test_latest_reading_returns_500_when_database_query_fails(mock_database):
    database_pool, connection, cursor = mock_database
    cursor.execute.side_effect = psycopg2.DatabaseError("database query failed")

    response = client.get("/sensors/42/latest")

    assert response.status_code == 500
    assert response.json() == {"detail": "database query failed"}
    database_pool.putconn.assert_called_once_with(connection)
