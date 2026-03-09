# Smart-Farm-IoT-Data-Pipeline
A high-performance, containerized IoT data ingestion pipeline designed to handle high-frequency sensor telemetry. This project demonstrates a tiered data architecture using PostgreSQL partitioning for "hot" data and materialized views for "warm" analytical summaries.

# 🚀 Key Features
- High Concurrency: Simulates 500 independent IoT sensors broadcasting telemetry simultaneously.

- Tiered Storage Strategy:

  - Hot Storage: Time-series partitioning (by month) for rapid data ingestion.

  - Warm Storage: Materialized views for pre-calculated hourly analytics.

  - Data Retention: Automated maintenance script to prune raw data older than 7 days while preserving summaries.

- Production Readiness: Fully containerized with Docker Compose, including self-healing database connection retry logic.

- Optimized API: FastAPI backend leveraging database indexes and summary tables for sub-50ms response times.

# 🏗️ System Architecture
The system is split into three decoupled services:

1. Ingestion Engine: A multi-threaded Python worker that batches telemetry to minimize database IOPS.

2. Database (PostgreSQL 18): Utilizes BRIN indexes and Table Partitioning to manage time-series data at scale.

3. REST API: Provides real-time field summaries and latest sensor readings.

# 🛠️ Tech Stack
- Backend: Python 3.12, FastAPI

- Database: PostgreSQL 18 (Partitioning, Materialized Views)

- DevOps: Docker, Docker Compose

- Libraries: Psycopg2 (Connection Pooling), Pydantic

# 🚦 Getting Started
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

# 📈 Performance & Scaling
- Throughput: Successfully tested with 500 concurrent sensor streams.

- Optimization: Moved from O(N) raw table scans to O(1) materialized view lookups for field analytics.

- Reliability: Implemented a "Wait-for-DB" retry loop in the ingestion worker to handle distributed system startup lag.
