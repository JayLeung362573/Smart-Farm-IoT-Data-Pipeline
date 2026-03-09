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
DROP TABLE IF EXISTS sensor_data CASCADE;
CREATE TABLE sensor_data (
    id SERIAL,
    sensor_id INT NOT NULL REFERENCES sensors(sensor_id),
    moisture FLOAT NOT NULL CHECK (moisture >= 0 AND moisture <= 100),
    temperature FLOAT NOT NULL CHECK (temperature >= -50 AND temperature <= 100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_id UUID NOT NULL,
    PRIMARY KEY (id, created_at),
    UNIQUE (event_id, created_at)
) PARTITION BY RANGE (created_at);

-- 3. Partitions
CREATE TABLE sensor_data_y2026m03 PARTITION OF sensor_data
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');

-- 4. Time-Series Indexes
CREATE INDEX idx_sensor_time ON sensor_data (sensor_id, created_at DESC);

CREATE INDEX idx_sensor_brin ON sensor_data USING BRIN (created_at);

-- 5. pre-calculate averages so the API doesn't have to scan millions of rows
CREATE MATERIALIZED VIEW hourly_sensor_stats AS
SELECT
    sensor_id,
    date_trunc('hour', created_at) as hour_bucket,
    ROUND(AVG(moisture)::numeric, 2) as avg_moisture,
    ROUND(AVG(temperature)::numeric, 2) as avg_temperature,
    COUNT(*) as sample_count

FROM sensor_data
GROUP BY sensor_id, hour_bucket
WITH DATA;

-- Create an index on the materialized view to make API lookups instant
CREATE INDEX idx_hourly_stats_time ON hourly_sensor_stats(hour_bucket DESC);

-- Seed 1 Farm
INSERT INTO farms (owner_name, region) VALUES ('SmartFarm Global', 'North America') ON CONFLICT DO NOTHING;

-- Seed 2 Farm
INSERT INTO fields (farm_id, name) VALUES (1, 'North Field'), (1, 'South Field') ON CONFLICT DO NOTHING;

-- Seed 500 Sensors (250 per field)
INSERT INTO sensors (field_id, sensor_type)
SELECT 
    CASE WHEN i <= 250 THEN 1 ELSE 2 END,
    'soil_moisture'
FROM generate_series(1, 500) s(i)
ON CONFLICT DO NOTHING;