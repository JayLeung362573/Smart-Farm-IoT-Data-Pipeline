import psycopg2
from psycopg2 import pool
import threading
import logging

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

def db_worker(data_queue):
    while(True):
        
        item = data_queue.get()
        # Sentinel Check: If we receive None, exit the loop
        if item is None:
            logging.info("Shutdown signal received. Exiting worker...")
            data_queue.task_done()
            break


        conn = None
        try:
            conn = db_pool.getconn()
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sensor_data(sensor_id, moisture, temperature, created_at)" \
                    "Values(%s, %s, %s, NOW())",
                    (item['sensor_id'], item['moisture'], item['temperature'])
                )
                conn.commit()
        except Exception as e:
            logging.error(f"Database insertion error: {e}")

        finally:
            if conn: 
                db_pool.putconn(conn)
            data_queue.task_done()

def start_workers(data_queue, num_workers=5):
    threads = []
    for _ in range(num_workers):
        t = threading.Thread(target=db_worker, args=(data_queue,), daemon=True)
        t.start()
        threads.append(t)
    return threads

    