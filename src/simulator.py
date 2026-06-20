import threading
import time
import queue
import random
import uuid
import logging
import os
import json

data_queue = queue.Queue(maxsize=2000)
shutdown_event = threading.Event()

SENSOR_COUNT = int(os.getenv("SENSOR_COUNT", "500"))
INGESTION_WORKERS = int(os.getenv("INGESTION_WORKERS", "5"))
RUN_SECONDS = int(os.getenv("RUN_SECONDS", "0"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "100"))

dropped_counter = 0
produced_counter = 0
counter_lock = threading.Lock()

def generate_sensor_payload(sensor_id):
    return {
        "sensor_id": sensor_id,
        "moisture": round(random.uniform(30, 70), 2),
        "temperature": round(random.uniform(10, 30), 2),
        "event_id": str(uuid.uuid4())
    }

def virtual_sensor(sensor_id):
    global dropped_counter, produced_counter

    while not shutdown_event.is_set():
        payload = generate_sensor_payload(sensor_id)

        try:
            data_queue.put(payload, block=False)
            with counter_lock:
                produced_counter += 1
        except queue.Full:
            with counter_lock:
                dropped_counter += 1

        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    from ingestion import fetch_sensor_ids, start_workers
    
    num_workers = INGESTION_WORKERS
    sensor_ids = fetch_sensor_ids(SENSOR_COUNT)
    worker_threads = start_workers(data_queue, num_workers)

    print(f"Launching {len(sensor_ids)} sensors...")
    for sensor_id in sensor_ids:
        sensor_thread = threading.Thread(
            target=virtual_sensor,
            args=(sensor_id,),
            daemon=True,
        )
        sensor_thread.start()

    start_time = time.time()

    try:
        while True:
            elapsed = time.time() - start_time

            with counter_lock:
                logging.info(
                    f"STATUS - Queue Size: {data_queue.qsize()} | "
                    f"Total Dropped: {dropped_counter} | "
                    f"Elapsed: {elapsed:.2f}s"
                )
            
            if RUN_SECONDS > 0 and elapsed >= RUN_SECONDS:
                logging.info("Configured run duration reached. Stopping simulator...")
                break

            time.sleep(1.0)
    except KeyboardInterrupt:
        logging.info("Graceful shutdown initiated...")

    finally:
        shutdown_event.set()
        
        for _ in range(num_workers):
            data_queue.put(None)
            
        data_queue.join()

        elapsed = time.time() - start_time

        with counter_lock:
            summary = {
                "sensor_count": SENSOR_COUNT,
                "worker_count": INGESTION_WORKERS,
                "batch_size": BATCH_SIZE,
                "run_seconds": RUN_SECONDS,
                "elapsed_seconds": round(elapsed, 2),
                "produced_readings": produced_counter,
                "dropped_readings": dropped_counter,
                "throughput_readings_per_sec": round(produced_counter / elapsed, 2) if elapsed > 0 else 0
            }

        print("Cleaned up threads and connections.")
        print(f"BENCHMARK_SUMMARY: {json.dumps(summary)}")