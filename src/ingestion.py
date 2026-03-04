import psycopg2
from psycopg2 import pool, extras
import threading
import logging
import queue
import time

# Configure structured logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [Worker-%(thread)d] %(levelname)s: %(message)s')

DB_PARAMS = {
    "user": "postgres",
    "password": "3221", 
    "host": "127.0.0.1",
    "port": "5432",
    "database": "smart_farm"
}

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_PARAMS)
    logging.info("Database connection pool initialized.")
except Exception as e:
    logging.error(f"Failed to initialize pool: {e}")

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

            batch.append((
                item['sensor_id'],
                item['moisture'],
                item['temperature'],
                item.get('event_id')
            ))

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

    
def start_workers(data_queue, num_workers=5):
    threads = []
    for _ in range(num_workers):
        t = threading.Thread(target=db_worker, args=(data_queue,), daemon=True)
        t.start()
        threads.append(t)
    return threads

def flush_batch(batch):
    conn = None
    try:
        conn = db_pool.getconn()
        with conn.cursor() as cur:
            extras.execute_values(
                cur,
                "INSERT INTO sensor_data (sensor_id, moisture, temperature, event_id) VALUES %s",
                batch
            )
            conn.commit()
    except Exception as e:
        logging.error(f"Batch insertion error: {e}")
    finally:
        if conn:
            db_pool.putconn(conn)