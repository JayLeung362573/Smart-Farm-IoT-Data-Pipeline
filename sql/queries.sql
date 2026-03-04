-- 1. Performance Check: See which partition the data is coming from
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM sensor_data 
WHERE created_at BETWEEN '2026-03-01' AND '2026-03-31';

-- 2. Latest 5 readings for a specific field (North Field)
SELECT s.sensor_id, sd.moisture, sd.temperature, sd.created_at
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id
JOIN fields f ON s.field_id = f.field_id
WHERE f.name = 'North Field'
ORDER BY sd.created_at DESC
LIMIT 5;

-- 3. Find "Problem Sensors" (Temperature > 25 in the last hour)
SELECT sensor_id, MAX(temperature) as max_temp
FROM sensor_data
WHERE temperature > 25 
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY sensor_id;

-- 4. Farm-wide summary
SELECT 
    COUNT(DISTINCT s.sensor_id) as active_sensors,
    COUNT(sd.id) as total_records,
    ROUND(AVG(sd.temperature)::numeric, 2) as farm_avg_temp
FROM sensor_data sd
JOIN sensors s ON sd.sensor_id = s.sensor_id;