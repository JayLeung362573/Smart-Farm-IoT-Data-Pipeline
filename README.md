# Smart-Farm-IoT-Data-Pipeline

![Tests](https://github.com/JayLeung362573/Smart-Farm-IoT-Data-Pipeline/actions/workflows/tests.yml/badge.svg)

A containerized IoT telemetry pipeline that simulates soil sensor readings, batches them through Python ingestion workers, stores time-series data in PostgreSQL, and exposes field-level summaries through FastAPI.

## Key Features
- High Concurrency: Simulates 500 virtual IoT sensors producing soil telemetry readings.

- Tiered Storage Strategy:

  - Hot Storage: Time-series partitioning for raw sensor readings.

  - Warm Storage: Materialized views for pre-calculated hourly analytics.

- Containerized Startup: Uses Docker Compose with database health checks and retry logic in the ingestion worker.

- Optimized API: FastAPI backend uses indexed sensor lookups and a materialized view for field-level summary queries.

## System Architecture

For a deeper explanation of the data flow, storage strategy, indexing choices, and materialized view tradeoffs, see [`docs/architecture.md`](docs/architecture.md).

The system is split into three decoupled services:

1. **Ingestion Engine**: A multi-threaded Python worker that batches telemetry to reduce per-row database write overhead.
2. **Database**: PostgreSQL uses range partitioning, BRIN indexes, and materialized views to manage time-series telemetry.
3. **REST API**: Provides latest sensor readings and field-level summaries from the refreshed analytical view.

## Tech Stack
- Backend: Python 3.12, FastAPI

- Database: PostgreSQL with partitioning, BRIN indexes, and materialized views.

- DevOps: Docker, Docker Compose

- Libraries: psycopg2, Pydantic, pytest

## Getting Started

### Prerequisites

- Docker Desktop
- Ports 8000 and 5433 available

### One-Command Deployment

Clone the repository and run:

```bash
docker-compose up --build
```

The system will automatically initialize the schema, seed 500 sensors, and begin the ingestion simulation.

### Accessing the API

- Interactive Docs: `http://localhost:8000/docs`
- Sensors: `http://localhost:8000/sensors`
- Latest Sensor Reading: `http://localhost:8000/sensors/1/latest`
- Field Summary: `http://localhost:8000/fields/1/summary`

## Refreshing Analytical Summaries

Raw sensor readings are ingested continuously into the `sensor_data` table. Field-level summary endpoints read from the `hourly_sensor_stats` materialized view, so the view must be refreshed after new readings are inserted.

With the system already running, refresh the materialized view:

```bash
docker-compose run --rm --no-deps \
  -e DB_HOST=db \
  -e DB_PORT=5432 \
  -e DB_NAME=smart_farm \
  -e DB_USER=postgres \
  -e DB_PASSWORD=3221 \
  api python scripts/refresh_views.py
```
Then query the field summary endpoint:

```bash
curl http://localhost:8000/fields/1/summary
```

Example response:
```json
{
  "field_name": "North Field",
  "total_readings": 22559,
  "avg_moisture": 50.05,
  "avg_temp": 20.02
}
```

This project currently treats materialized views as a warm analytical layer. Refreshing summaries manually avoids refreshing the view on every insert, which would slow down ingestion. A future improvement is adding scheduled or concurrent refreshes.

## Performance & Scaling
- Concurrency: Simulates 500 virtual sensor streams using Python threads.

- Write Optimization: Batches sensor readings before inserting them into PostgreSQL.

- Read Optimization: Uses a materialized view to avoid scanning raw telemetry rows for field-level summary endpoints.

- Reliability: Uses Docker Compose health checks and a Wait-for-DB retry loop in the ingestion worker to handle startup ordering.

### Example Local Benchmark Results

The benchmark runs the sensor simulator and PostgreSQL ingestion workers through Docker Compose. It tracks generated readings, successfully committed rows, failed or skipped writes, queue drops, and database ingestion throughput.

The following local runs used five ingestion workers, a batch size of 100, and a 30-second configured duration. Results vary by machine and runtime environment, so they are presented as reproducible local measurements rather than production guarantees.

| Sensors | Workers | Batch Size | Committed Rows | Failed | Skipped | Dropped | Database Throughput | Commit Success |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 5 | 100 | 3,056 | 0 | 0 | 0 | 101.33 rows/sec | 100% |
| 250 | 5 | 100 | 7,678 | 0 | 0 | 0 | 254.60 rows/sec | 100% |
| 500 | 5 | 100 | 15,324 | 0 | 0 | 0 | 508.94 rows/sec | 100% |

Across these local runs, committed PostgreSQL throughput scaled approximately with the number of simulated sensor streams while maintaining zero failed writes, skipped writes, or queue drops. The benchmark waits for queued batches to finish before producing its final summary.

## Common Commands

This project includes a `Makefile` for common local workflows.

```bash
make up               # Start the full Docker Compose system
make test             # Run pytest inside the API container
make test-integration # Run database-backed PostgreSQL integration test
make smoke            # Run local end-to-end smoke test
make refresh          # Refresh the materialized analytical view
make benchmark-smoke  # Run a short benchmark
make benchmark        # Run the default 500-sensor benchmark
make clean            # Remove containers, volumes, and local benchmark results
```

## Running Tests

For more details about the unit, integration, smoke, and benchmark testing strategy, see [`docs/testing.md`](docs/testing.md).

Run the default test suite inside the Docker environment:

```bash
make test
```

The default test suite includes:

- API health check
- Sensor payload validation
- Ingestion batch formatting

Database-backed integration testing is available through a separate command because it requires a running PostgreSQL service.

Start the database service:

```bash
docker-compose up -d db
```

Run the integration test:

```bash
make test-integration
```

The integration test verifies PostgreSQL connectivity, schema initialization, seeded sensor metadata, raw telemetry insertion, materialized view refresh, and field-level summary querying.

## Running a Local Smoke Test

After starting the system with Docker Compose:

```bash
docker-compose up --build
```

Run the smoke test in another terminal:

```bash
./scripts/smoke_test.sh
```

The smoke test checks API health, seeded sensor metadata, latest sensor ingestion, materialized view refresh, and field-level summary output.

## Benchmarking

The ingestion benchmark runs the simulator through Docker Compose and requires the database service to already be running.

Start the system:

```bash
docker-compose up --build
```

In another terminal, run a benchmark:

```bash
python3 scripts/benchmark_ingestion.py \
  --sensors 500 \
  --workers 5 \
  --batch-size 100 \
  --duration 60 \
  --output results/benchmark.json
```

For a shorter local smoke test:

```bash
python3 scripts/benchmark_ingestion.py \
  --sensors 10 \
  --workers 2 \
  --batch-size 25 \
  --duration 5 \
  --output results/benchmark.json
```

For the summarized benchmark table, see the Performance & Scaling section above.

Example output:

```json
{
  "sensor_count": 100,
  "worker_count": 5,
  "batch_size": 100,
  "run_seconds": 30,
  "elapsed_seconds": 30.16,
  "produced_readings": 3056,
  "committed_readings": 3056,
  "failed_readings": 0,
  "skipped_readings": 0,
  "dropped_readings": 0,
  "producer_throughput_readings_per_sec": 101.33,
  "database_throughput_readings_per_sec": 101.33,
  "commit_success_rate_percent": 100.0
}
```

Benchmark result files are written under `results/`, which is ignored by Git because results vary by machine and runtime environment.