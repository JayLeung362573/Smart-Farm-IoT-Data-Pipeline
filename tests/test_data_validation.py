from src.simulator import generate_sensor_payload


def test_generated_sensor_payload_has_required_fields():
    payload = generate_sensor_payload(sensor_id=1)

    assert "sensor_id" in payload
    assert "moisture" in payload
    assert "temperature" in payload
    assert "event_id" in payload


def test_generated_sensor_payload_values_are_in_expected_ranges():
    payload = generate_sensor_payload(sensor_id=1)

    assert payload["sensor_id"] == 1
    assert 30 <= payload["moisture"] <= 70
    assert 10 <= payload["temperature"] <= 30
    assert isinstance(payload["event_id"], str)
    assert len(payload["event_id"]) > 0