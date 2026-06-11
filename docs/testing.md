# Testing Strategy

This project uses three levels of testing: fast unit tests, a local end-to-end smoke test, and a short benchmark smoke test.

## 1. Unit Tests

Unit tests are run with `pytest` and focus on fast checks that do not require PostgreSQL.

Current unit tests cover:

- API health check
- Sensor payload validation
- Ingestion batch formatting

Run unit tests:

```bash
make test
```

## 2. Local Smoke Test

The smoke test verifies that the full Docker Compose system works end to end.

It checks:

- API health endpoint
- Sensor metadata seeding
- Live ingestion into `sensor_data`
- Materialized view refresh
- Field-level summary response

Run the full system:

```bash
make up
```

In another terminal:

```bash
make smoke
```

## 3. Database-Backed Integration Test

The integration test verifies that the Docker Compose PostgreSQL service, schema initialization, seeded metadata, raw telemetry insertion, materialized view refresh, and field-level summary query work together.

This test is skipped by default during the normal unit test run because it requires a running PostgreSQL database.

Start the database service:

```bash
docker-compose up -d db
```

Run the integration test:

```bash
make test-integration
```

## 4. Benchmark Smoke Test

The benchmark smoke test runs a short ingestion benchmark and writes a JSON result under `results/`.

```bash
make benchmark-smoke
```

## Current CI Scope

GitHub Actions currently runs the unit test suite only.

The CI intentionally avoids starting PostgreSQL because the default test command skips database-backed integration tests unless `RUN_DB_INTEGRATION=1` is set. Full Docker Compose integration is verified locally through the smoke test and the optional integration test.

## Future Testing Improvements

Planned improvements:

- Add schema initialization test
- Add materialized view refresh test
- Add a separate optional GitHub Actions integration workflow
