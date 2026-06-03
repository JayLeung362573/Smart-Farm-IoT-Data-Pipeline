# Smart-Farm-IoT-Data-Pipeline
A containerized IoT telemetry pipeline that simulates soil sensor readings, batches them through Python ingestion workers, stores time-series data in PostgreSQL, and exposes field-level summaries through FastAPI.

# Key Features
- High Concurrency: Simulates 500 virtual IoT sensors producing soil telemetry readings.

- Tiered Storage Strategy:

  - Hot Storage: Time-series partitioning for raw sensor readings.

  - Warm Storage: Materialized views for pre-calculated hourly analytics.

- Containerized Startup: Uses Docker Compose with database health checks and retry logic in the ingestion worker.

- Optimized API: FastAPI backend uses indexed sensor lookups and a materialized view for field-level summary queries.

# System Architecture
The system is split into three decoupled services:

For a deeper explanation of the data flow, storage strategy, indexing choices, and materialized view tradeoffs, see [`docs/architecture.md`](docs/architecture.md).

The system is split into three decoupled services:

1. Ingestion Engine: A multi-threaded Python worker that batches telemetry to minimize database IOPS.

2. Database: PostgreSQL uses range partitioning, BRIN indexes, and materialized views to manage time-series telemetry.

3. REST API: Provides latest sensor readings and field-level summaries from the refreshed analytical view.

# Tech Stack
- Backend: Python 3.12, FastAPI

- Database: PostgreSQL with partitioning, BRIN indexes, and materialized views.

- DevOps: Docker, Docker Compose

- Libraries: Psycopg2 (Connection Pooling), Pydantic

# Getting Started
Prerequisites
- Docker Desktop (ensure it is running)
- Port Availability: Ensure ports 8000 (API) and 5433 (PostgreSQL) are not currently in use by local services.

One-Command Deployment
Clone the repository and run:

`docker-compose up --build`

The system will automatically initialize the schema, seed 500 sensors, and begin the ingestion simulation.

Accessing the API
Interactive Docs: `http://localhost:8000/docs`

Field Summary: `http://localhost:8000/fields/1/summary`

# Refreshing Analytical Summaries

Raw sensor readings are ingested continuously into the `sensor_data` table. Field-level summary endpoints read from the `hourly_sensor_stats` materialized view, so the view must be refreshed after new readings are inserted.

With the system already running, refresh the materialized view:

```
docker-compose run --rm --no-deps \
  -e DB_HOST=db \
  -e DB_PORT=5432 \
  -e DB_NAME=smart_farm \
  -e DB_USER=postgres \
  -e DB_PASSWORD=3221 \
  api python scripts/refresh_views.py
```
Then query the field summary endpoint:

```
curl http://localhost:8000/fields/1/summary
```

Example response:
```
{
  "field_name": "North Field",
  "total_readings": 22559,
  "avg_moisture": 50.05,
  "avg_temp": 20.02
}
```

This project currently treats materialized views as a warm analytical layer. Refreshing summaries manually avoids refreshing the view on every insert, which would slow down ingestion. A future improvement is adding scheduled or concurrent refreshes.

# Performance & Scaling
- Concurrency: Simulates 500 virtual sensor streams using Python threads.

- Write Optimization: Batches sensor readings before inserting them into PostgreSQL.

- Read Optimization: Uses a materialized view to avoid scanning raw telemetry rows for field-level summary endpoints.

- Reliability: Uses Docker Compose health checks and a Wait-for-DB retry loop in the ingestion worker to handle startup ordering.

# Benchmark Results

Current benchmark numbers were removed until they can be reproduced through the benchmark script.

Planned benchmark command:

```
python scripts/benchmark_ingestion.py --sensors 500 --workers 5 --batch-size 100 --duration 60
```