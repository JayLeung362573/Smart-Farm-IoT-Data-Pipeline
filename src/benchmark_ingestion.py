import time
import queue
import threading
import random
import uuid
import psycopg2
from config import Config
from ingestion import start_workers

NUM_SENSORS = 500
TEST_DURATION = 3
NUM_WORKERS = 5

data_queue = queue.Queue(maxsize=5000)
shutdown_event = threading.Event()

produced_count = 0
dropped_count = 0
count_lock = threading.Lock()

def virtual_sensor(sensor_id):
    global produced_count, dropped_count

    while not shutdown_event.is_set():
        payload = {
            "sensor_id": sensor_id,
            "moisture": round(random.uniform(30, 70), 2),
            "temperature": round(random.uniform(10, 30), 2),
            "event_id": str(uuid.uuid4())
        }

        try:
            data_queue.put(payload, block=False)
            with count_lock:
                produced_count += 1
        except queue.Full:
            with count_lock:
                dropped_count += 1
        time.sleep(random.uniform(0.5, 1.5))

def get_row_count():
    conn = psycopg2.connect(**Config.get_db_params())
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sensor_data;")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def main():
    global produced_count, dropped_count

    print("Starting ingestion benchmark")
    print(f"Sensors: {NUM_SENSORS}")
    print(f"Workers: {NUM_WORKERS}")
    print(f"Duration: {TEST_DURATION}s")

    before_count = get_row_count()

    workers_threads = start_workers(data_queue, NUM_WORKERS)

    sensor_thread = []
    start_time = time.time()

    for i in range(NUM_SENSORS):
        t = threading.Thread(target=virtual_sensor, args=(i, ), daemon=True)
        t.start()
        sensor_thread.append(t)

    time.sleep(TEST_DURATION)

    shutdown_event.set()

    for _ in range(NUM_WORKERS):
        data_queue.put(None)

    data_queue.join()

    end_time = time.time()
    after_count = get_row_count()

    elapsed = end_time - start_time
    inserted = after_count - before_count

    print("\n===== Benchmark Results =====")
    print(f"Produced readings: {produced_count}")
    print(f"Inserted readings: {inserted}")
    print(f"Dropped readings: {dropped_count}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print(f"Ingestion throughput: {inserted / elapsed:.2f} readings/sec")
    print(f"Queue size at end: {data_queue.qsize()}")


if __name__ == "__main__":
    main()
