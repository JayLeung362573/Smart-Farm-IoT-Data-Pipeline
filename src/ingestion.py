import psycopg2
from psycopg2 import pool
import threading

DB_PARAMS = {
    "user": "postgres",
    "password": "3221", 
    "host": "127.0.0.1",
    "port": "5432",
    "database": "smart_farm"
}

try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, **DB_PARAMS)
except Exception as e:
    print("Connection Error: {e}")

def db_worker(data_queue):
    while(True):
        item = data_queue.get()
        conn = db_pool.getconn()

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO sensor_data(sensor_id, moisture, temperature)" \
                    "Values(%s, %s, %s)",
                    (item['sensor_id'], item['moisture'], item['temperature'])
                )
                conn.commit()
        except Exception as e:
            print("Database error: {e}")

        finally:
            db_pool.putconn(conn)
            data_queue.task_done()

def start_workers(data_queue, num_workers=5):
    for _ in range(num_workers):
        t = threading.Thread(target=db_worker, args=(data_queue,), daemon=True)
        t.start()

    