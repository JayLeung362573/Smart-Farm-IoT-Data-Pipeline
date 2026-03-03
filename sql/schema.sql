-- 1. Metadata Tables
CREATE TABLE IF NOT EXISTS farms (
    farm_id SERIAL PRIMARY KEY,
    owner_name VARCHAR(100),
    region VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS fields (
    field_id SERIAL PRIMARY KEY,
    farm_id INT REFERENCES farms(farm_id),
    name VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS sensors (
    sensor_id SERIAL PRIMARY KEY,
    field_id INT REFERENCES fields(field_id),
    sensor_type VARCHAR(50) DEFAULT 'soil_moisture',
    status VARCHAR(20) DEFAULT 'active'
);

-- 2. Partitioned Table
DROP TABLE IF EXISTS sensor_data;
CREATE TABLE sensor_data (
    id SERIAL,
    sensor_id INT NOT NULL REFERENCES sensors(sensor_id),
    moisture FLOAT NOT NULL CHECK (moisture >= 0 AND moisture <= 100),
    temperature FLOAT NOT NULL CHECK (temperature >= -50 AND temperature <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- 3. Partitions
CREATE TABLE sensor_data_y2026m03 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- 4. Time-Series Indexes
CREATE INDEX idx_sensor_time ON sensor_data (sensor_id, created_at DESC);