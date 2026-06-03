# Architecture

## Overview

This project is a containerized IoT telemetry pipeline for simulated smart-farm soil sensors. The system generates virtual sensor readings, batches them through Python ingestion workers, stores raw time-series readings in PostgreSQL, and exposes sensor and field-level APIs through FastAPI.

The project is organized around three services:

1. **Ingestion Engine**: Generates virtual sensor readings and writes them to PostgreSQL in batches.
2. **PostgreSQL Database**: Stores sensor metadata, raw telemetry, indexes, partitions, and analytical summaries.
3. **FastAPI REST API**: Exposes endpoints for sensor metadata, latest sensor readings, and field-level summaries.

## Data Flow

1. Virtual sensors generate soil telemetry payloads with:
   - sensor ID
   - moisture
   - temperature
   - event ID

2. Sensor payloads are pushed into a bounded in-memory queue.

3. Worker threads consume the queue and group readings into batches.

4. Batched readings are inserted into the `sensor_data` table in PostgreSQL.

5. API endpoints query:
   - raw readings for latest sensor data
   - materialized view summaries for field-level analytics

## Hot and Warm Storage

The project separates raw ingestion data from analytical summary data.

### Hot Storage

The `sensor_data` table stores raw sensor readings. It is treated as hot storage because new records are continuously inserted by the ingestion engine.

The table is partitioned by `created_at` so time-series data can be managed by time range.

### Warm Storage

The `hourly_sensor_stats` materialized view stores pre-calculated hourly summaries.

This is treated as warm storage because it is optimized for analytical reads rather than continuous writes. The API can query this view instead of scanning raw telemetry rows for every field summary request.

## Why Use PostgreSQL Partitioning?

Sensor telemetry is naturally time-series data. As the raw table grows, partitioning by time range helps keep data easier to manage.

Partitioning also creates a path for future retention policies, such as dropping old raw-data partitions while preserving aggregated summaries.

## Why Use a BRIN Index?

The project uses a BRIN index on `created_at`.

A BRIN index is appropriate for append-heavy time-series data because newly inserted rows tend to be physically correlated with time. Compared with a large B-tree index, a BRIN index can stay smaller while still helping PostgreSQL skip irrelevant blocks for time-range queries.

## Materialized View Refresh Strategy

The `hourly_sensor_stats` materialized view is used as a warm analytical layer.

The current version refreshes this view manually using:

```
docker-compose run --rm --no-deps \
  -e DB_HOST=db \
  -e DB_PORT=5432 \
  -e DB_NAME=smart_farm \
  -e DB_USER=postgres \
  -e DB_PASSWORD=3221 \
  api python scripts/refresh_views.py
```

This design avoids refreshing the view on every insert, which would slow down ingestion.

The tradeoff is that field-level summaries are not fully real-time. They reflect the latest data only after the view is refreshed.

A future improvement would be scheduled refreshes or `REFRESH MATERIALIZED VIEW CONCURRENTLY`.

## Ingestion Worker Model

The ingestion engine uses Python threads to simulate multiple virtual sensors and database workers.

Virtual sensor threads generate readings and push them into a bounded queue. Database worker threads consume readings from the queue and insert them in batches.

Batching reduces per-row transaction overhead compared with inserting one reading at a time.

## Reliability Choices

The project includes basic startup reliability mechanisms:

- Docker Compose health checks wait for PostgreSQL to become available.
- The ingestion worker includes Wait-for-DB retry logic.
- The ingestion queue has a maximum size to avoid unbounded memory growth.
- Sensor readings include event IDs to make duplicate-handling logic easier to extend.

## Tradeoffs and Limitations

This project is designed as a portfolio-scale backend/data system, not a production deployment.

Current limitations:

- Materialized views are refreshed manually.
- Benchmark numbers are being refactored into a reproducible script.
- The simulator runs inside one container and uses Python threads rather than distributed sensor clients.
- There is no production-grade authentication or authorization.
- Retention logic is planned but not yet implemented as a scheduled maintenance process.

## Future Improvements

Planned improvements:

- Add reproducible ingestion benchmark script.
- Add pytest coverage for API endpoints, ingestion batching, data validation, and DB retry logic.
- Add scheduled or concurrent materialized view refresh.
- Add raw-data retention script for old partitions.
- Add CI workflow to run tests automatically.