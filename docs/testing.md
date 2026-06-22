# Testing Strategy

This project uses four levels of verification: fast unit tests, a PostgreSQL-backed integration test, a local end-to-end smoke test, and configurable ingestion benchmarks.

## 1. Unit Tests

Unit tests are run with `pytest` and focus on fast checks that do not require PostgreSQL.

Current unit tests cover:

* API health checks
* Sensor payload validation
* Ingestion batch formatting
* Ingestion metric reset behavior
* Committed and skipped row accounting
* Transaction rollback and failed-row accounting
* Behavior when the database pool is unavailable

Run unit tests:

```bash
make test
```

## 2. Database-Backed Integration Test

The integration test verifies that PostgreSQL schema initialization, seeded metadata, raw telemetry insertion, materialized-view refresh, and field-level summary queries work together.

This test is skipped during the default unit-test command because it requires PostgreSQL.

Start the database service:

```bash
docker-compose up -d db
```

Run the integration test:

```bash
make test-integration
```

## 3. Local Smoke Test

The smoke test verifies that the complete Docker Compose system works end to end.

It checks:

* API health endpoint
* Sensor metadata seeding
* Live ingestion into `sensor_data`
* Materialized-view refresh
* Field-level summary response

Start the full system:

```bash
make up
```

In another terminal:

```bash
make smoke
```

## 4. Ingestion Benchmarks

The benchmark workflow runs the simulator with configurable sensor counts, ingestion workers, batch sizes, and durations.

It reports:

* Generated readings
* Committed PostgreSQL rows
* Failed and skipped writes
* Queue drops
* Producer throughput
* Database throughput
* Commit success rate

Run a short benchmark:

```bash
make benchmark-smoke
```

Run the default benchmark:

```bash
make benchmark
```

## Current CI Scope

GitHub Actions runs two independent jobs for pushes and pull requests targeting `main`:

1. **Unit Tests**

   * Installs the Python dependencies.
   * Runs tests marked as non-integration tests.
   * Does not require PostgreSQL.

2. **PostgreSQL Integration Test**

   * Starts a PostgreSQL service container.
   * Initializes the database using `sql/schema.sql`.
   * Runs the database-backed integration test with `RUN_DB_INTEGRATION=1`.

The full Docker Compose smoke test and configurable ingestion benchmarks remain local workflows because they run longer and are intended for end-to-end validation and performance evidence rather than every CI execution.

## Future Testing Improvements

Potential extensions include:

* Add API integration tests that query the running FastAPI service against PostgreSQL.
* Add automated smoke testing in a scheduled or manually triggered workflow.
* Add benchmark regression thresholds for committed throughput and dropped readings.
* Add concurrency and failure-injection tests for database connection interruptions.
