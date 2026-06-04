from src.ingestion import to_insert_tuple


def test_to_insert_tuple_formats_sensor_reading_for_database_insert():
    item = {
        "sensor_id": 1,
        "moisture": 42.5,
        "temperature": 21.3,
        "event_id": "00000000-0000-0000-0000-000000000001"
    }

    result = to_insert_tuple(item)

    assert result == (
        1,
        42.5,
        21.3,
        "00000000-0000-0000-0000-000000000001"
    )


def test_to_insert_tuple_allows_missing_event_id():
    item = {
        "sensor_id": 2,
        "moisture": 50.0,
        "temperature": 19.8
    }

    result = to_insert_tuple(item)

    assert result == (
        2,
        50.0,
        19.8,
        None
    )