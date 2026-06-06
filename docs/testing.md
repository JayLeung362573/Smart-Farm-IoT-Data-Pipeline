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

## 3. Benchmark Smoke Test

The benchmark smoke test runs a short ingestion benchmark and writes a JSON result under `results/`.

```bash
make benchmark-smoke
```

## Current CI Scope

GitHub Actions currently runs the unit test suite only.

The CI intentionally avoids starting PostgreSQL because the current unit tests do not require a database. Full Docker Compose integration is verified locally through the smoke test.

## Future Testing Improvements

Planned improvements:

- Add database-backed API integration tests
- Add schema initialization test
- Add materialized view refresh test
- Add a separate optional GitHub Actions integration workflow