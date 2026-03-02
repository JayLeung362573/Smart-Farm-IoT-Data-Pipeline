CREATE_TABLE sensor_data(
    id SERIAL PRIMARY KEY,
    sensor_id INT NOT NULL,
    moisture FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sensor_id ON sensor_data(sensor_id);