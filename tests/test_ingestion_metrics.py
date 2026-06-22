from unittest.mock import MagicMock

import src.ingestion as ingestion


def setup_function():
    ingestion.reset_ingestion_metrics()


def make_mock_database():
    connection = MagicMock()
    cursor = MagicMock()

    connection.cursor.return_value.__enter__.return_value = cursor

    database_pool = MagicMock()
    database_pool.getconn.return_value = connection

    return database_pool, connection, cursor


def test_reset_ingestion_metrics_clears_all_counters():
    ingestion.committed_counter = 10
    ingestion.failed_counter = 3
    ingestion.skipped_counter = 2

    ingestion.reset_ingestion_metrics()

    assert ingestion.get_ingestion_metrics() == {
        "committed_readings": 0,
        "failed_readings": 0,
        "skipped_readings": 0,
    }


def test_flush_batch_tracks_committed_and_skipped_rows(monkeypatch):
    database_pool, connection, cursor = make_mock_database()

    monkeypatch.setattr(ingestion, "db_pool", database_pool)

    execute_values = MagicMock(
        return_value=[
            (101,),
            (102,),
        ]
    )
    monkeypatch.setattr(ingestion.extras, "execute_values", execute_values)

    batch = [
        (1, 42.5, 21.0, "00000000-0000-0000-0000-000000000001"),
        (2, 43.0, 21.5, "00000000-0000-0000-0000-000000000002"),
        (3, 44.0, 22.0, "00000000-0000-0000-0000-000000000003"),
    ]

    committed = ingestion.flush_batch(batch)

    assert committed == 2
    assert ingestion.get_ingestion_metrics() == {
        "committed_readings": 2,
        "failed_readings": 0,
        "skipped_readings": 1,
    }

    execute_values.assert_called_once()
    assert execute_values.call_args.kwargs["fetch"] is True

    connection.commit.assert_called_once_with()
    connection.rollback.assert_not_called()
    database_pool.putconn.assert_called_once_with(connection)


def test_flush_batch_rolls_back_and_tracks_failed_rows(monkeypatch):
    database_pool, connection, cursor = make_mock_database()

    monkeypatch.setattr(ingestion, "db_pool", database_pool)
    monkeypatch.setattr(
        ingestion.extras,
        "execute_values",
        MagicMock(side_effect=RuntimeError("database insert failed")),
    )

    batch = [
        (1, 42.5, 21.0, "00000000-0000-0000-0000-000000000001"),
        (2, 43.0, 21.5, "00000000-0000-0000-0000-000000000002"),
    ]

    committed = ingestion.flush_batch(batch)

    assert committed == 0
    assert ingestion.get_ingestion_metrics() == {
        "committed_readings": 0,
        "failed_readings": 2,
        "skipped_readings": 0,
    }

    connection.commit.assert_not_called()
    connection.rollback.assert_called_once_with()
    database_pool.putconn.assert_called_once_with(connection)


def test_flush_batch_tracks_failure_when_pool_is_unavailable(monkeypatch):
    monkeypatch.setattr(ingestion, "db_pool", None)

    batch = [
        (1, 42.5, 21.0, "00000000-0000-0000-0000-000000000001"),
        (2, 43.0, 21.5, "00000000-0000-0000-0000-000000000002"),
    ]

    committed = ingestion.flush_batch(batch)

    assert committed == 0
    assert ingestion.get_ingestion_metrics() == {
        "committed_readings": 0,
        "failed_readings": 2,
        "skipped_readings": 0,
    }