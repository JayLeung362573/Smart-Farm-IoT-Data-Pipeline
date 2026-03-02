CREATE TABLE IF NOT EXISTS sensor_data(
    id SERIAL PRIMARY KEY,
    sensor_id INT NOT NULL,
    moisture FLOAT NOT NULL CHECK (moisture >= 0 AND moisture <= 100),
    temperature FLOAT NOT NULL CHECK (temperature >= -50 AND temperature <= 100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sensor_id ON sensor_data(sensor_id, created_at DESC);