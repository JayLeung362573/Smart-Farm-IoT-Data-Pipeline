import psycopg2
from psycopg2 import pool, extras
import threading
import logging
import queue
import time
import os

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [Worker-%(thread)d] %(levelname)s: %(message)s')

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PASSWORD = os.getenv("DB_PASSWORD", "3221")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

DB_PARAMS = {
    "user": "postgres",
    "password": DB_PASSWORD, 
    "host": DB_HOST,
    "port": "5432",
    "database": "smart_farm"
}

db_pool = None

committed_counter = 0
failed_counter = 0
skipped_counter = 0
metrics_lock = threading.Lock()


def reset_ingestion_metrics():
    """Reset ingestion counters before a benchmark run."""
    global committed_counter, failed_counter, skipped_counter

    with metrics_lock:
        committed_counter = 0
        failed_counter = 0
        skipped_counter = 0


def get_ingestion_metrics():
    """Return a thread-safe snapshot of ingestion counters."""
    with metrics_lock:
        return {
            "committed_readings": committed_counter,
            "failed_readings": failed_counter,
            "skipped_readings": skipped_counter,
        }


def to_insert_tuple(item):
    return (
        item["sensor_id"],
        item["moisture"],
        item["temperature"],
        item.get("event_id")
    )

def init_pool():
    global db_pool
    while db_pool is None:
        try:
            db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_PARAMS)
            logging.info("Successfully connected to the database pool.")
        except Exception as e:
            logging.error(f"Database not ready yet. Retrying in 2s: {e}")
            time.sleep(2)


def fetch_sensor_ids(limit):
    """Return valid sensor IDs from PostgreSQL for simulator workers."""
    if limit <= 0:
        raise ValueError("Sensor count must be greater than zero.")

    init_pool()

    conn = None
    try:
        conn = db_pool.getconn()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sensor_id
                FROM sensors
                ORDER BY sensor_id
                LIMIT %s;
                """,
                (limit,),
            )
            sensor_ids = [row[0] for row in cur.fetchall()]
    finally:
        if conn:
            db_pool.putconn(conn)

    if len(sensor_ids) < limit:
        raise ValueError(
            f"Requested {limit} sensors, but only "
            f"{len(sensor_ids)} sensor records exist in PostgreSQL."
        )

    return sensor_ids


def db_worker(data_queue, batch_size=100):
    batch = []
    while(True):
        try:
            item = data_queue.get(timeout=0.5)
            # Sentinel Check: If we receive None, exit the loop
            if item is None:
                if batch:
                    flush_batch(batch)
                logging.info("Shutdown signal received. Exiting worker...")
                data_queue.task_done()
                break

            batch.append(to_insert_tuple(item))

            if len(batch) >= batch_size:
                flush_batch(batch)
                batch = []
            data_queue.task_done()

        except queue.Empty:
            # Flush batch if no new data arrived for 0.5s
            if batch:
                flush_batch(batch)
                batch = []
            continue

    
def start_workers(data_queue, num_workers, batch_size=BATCH_SIZE):
    init_pool()

    threads = []
    for _ in range(num_workers):
        thread = threading.Thread(
            target=db_worker,
            args=(data_queue, batch_size),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    return threads

def flush_batch(batch):
    """Insert one batch and update thread-safe ingestion metrics."""
    global committed_counter, failed_counter, skipped_counter

    if not batch:
        return 0

    if not db_pool:
        with metrics_lock:
            failed_counter += len(batch)
        return 0

    conn = None

    try:
        conn = db_pool.getconn()

        with conn.cursor() as cur:
            query = """
                INSERT INTO sensor_data (
                    sensor_id,
                    moisture,
                    temperature,
                    event_id
                )
                VALUES %s
                ON CONFLICT (event_id, created_at) DO NOTHING
                RETURNING id;
            """

            inserted_rows = extras.execute_values(
                cur,
                query,
                batch,
                fetch=True,
            )

        conn.commit()

        committed = len(inserted_rows)
        skipped = len(batch) - committed

        with metrics_lock:
            committed_counter += committed
            skipped_counter += skipped

        return committed

    except Exception as error:
        if conn:
            conn.rollback()

        with metrics_lock:
            failed_counter += len(batch)

        logging.error(f"Batch insertion error: {error}")
        return 0

    finally:
        if conn:
            db_pool.putconn(conn)