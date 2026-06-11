.PHONY: up down test test-integration smoke refresh benchmark-smoke benchmark clean

up:
	docker-compose up --build

down:
	docker-compose down

test:
	docker-compose run --rm --no-deps api python -m pytest

test-integration:
	docker-compose run --rm \
		-e RUN_DB_INTEGRATION=1 \
		-e DB_HOST=db \
		-e DB_PORT=5432 \
		-e DB_NAME=smart_farm \
		-e DB_USER=postgres \
		-e DB_PASSWORD=3221 \
		api python -m pytest tests/test_db_integration.py -v

smoke:
	./scripts/smoke_test.sh

refresh:
	docker-compose run --rm --no-deps \
		-e DB_HOST=db \
		-e DB_PORT=5432 \
		-e DB_NAME=smart_farm \
		-e DB_USER=postgres \
		-e DB_PASSWORD=3221 \
		api python scripts/refresh_views.py

benchmark-smoke:
	python3 scripts/benchmark_ingestion.py \
		--sensors 10 \
		--workers 2 \
		--batch-size 25 \
		--duration 5 \
		--output results/benchmark.json

benchmark:
	python3 scripts/benchmark_ingestion.py \
		--sensors 500 \
		--workers 5 \
		--batch-size 100 \
		--duration 60 \
		--output results/benchmark.json

clean:
	docker-compose down -v
	rm -rf results/