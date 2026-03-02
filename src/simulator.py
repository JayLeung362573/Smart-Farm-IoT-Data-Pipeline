import threading
import time
import queue
import random
from ingestion import start_workers

data_queue = queue.Queue(maxsize=2000)
shutdown_event = threading.Event()

def virtual_sensor(sensor_id):
    while not shutdown_event.is_set():
        payload = {
            "sensor_id": sensor_id,
            "moisture": round(random.uniform(30,70),2),
            "temperature": round(random.uniform(10,30),2)
        }
        try:
            data_queue.put(payload, timeout=1)
        except queue.Full:
            continue
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
            print(f"Data Queue Size: {data_queue.qsize()} items waiting for ingestion...")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        shutdown_event.set()
        
        for _ in range(num_workers):
            data_queue.put(None)
            
        print("Cleaned up threads and connections.")