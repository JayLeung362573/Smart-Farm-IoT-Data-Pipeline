import threading
import time
import queue
import random
import uuid
import logging
from ingestion import start_workers

data_queue = queue.Queue(maxsize=2000)
shutdown_event = threading.Event()

dropped_counter = 0
counter_lock = threading.Lock()

def virtual_sensor(sensor_id):
    while not shutdown_event.is_set():
        payload = {
            "sensor_id": sensor_id,
            "moisture": round(random.uniform(30,70),2),
            "temperature": round(random.uniform(10,30),2),
            "event_id": str(uuid.uuid4())
        }
        try:
            data_queue.put(payload, block=False)
        except queue.Full:
            with counter_lock:
                dropped_counter += 1
        time.sleep(random.uniform(0.5, 1.5))

if __name__ == "__main__":
    num_workers = 5
    worker_threads = start_workers(data_queue, num_workers)

    print(f"Launching {500} sensors...")
    for i in range(500):
        sensor_thread = threading.Thread(target=virtual_sensor, args=(i,), daemon=True)
        sensor_thread.start()

    try:
        while True:
            with counter_lock:
                logging.info(f"STATUS - Queue Size: {data_queue.qsize()} | Total Dropped: {dropped_counter}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        logging.info("Graceful shutdown initiated...")
        shutdown_event.set()
        
        for _ in range(num_workers):
            data_queue.put(None)
            
        print("Cleaned up threads and connections.")