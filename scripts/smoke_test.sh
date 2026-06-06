#!/usr/bin/env bash

set -e

echo "Checking API health..."
curl -s http://localhost:8000/ | grep "online" > /dev/null
echo "API health check passed."

echo "Checking seeded sensors..."
SENSORS_RESPONSE=$(curl -s http://localhost:8000/sensors)
echo "$SENSORS_RESPONSE" | grep '"total":500' > /dev/null
echo "Sensor seed check passed."

echo "Waiting for ingestion data..."
sleep 5

echo "Checking latest sensor reading..."
LATEST_RESPONSE=$(curl -s http://localhost:8000/sensors/1/latest)
echo "$LATEST_RESPONSE" | grep '"sensor_id":1' > /dev/null
echo "Latest sensor reading check passed."

echo "Refreshing materialized view..."
docker-compose run --rm --no-deps \
  -e DB_HOST=db \
  -e DB_PORT=5432 \
  -e DB_NAME=smart_farm \
  -e DB_USER=postgres \
  -e DB_PASSWORD=3221 \
  api python scripts/refresh_views.py

echo "Checking field summary..."
SUMMARY_RESPONSE=$(curl -s http://localhost:8000/fields/1/summary)
echo "$SUMMARY_RESPONSE" | grep '"field_name":"North Field"' > /dev/null
echo "Field summary check passed."

echo "Smoke test passed."