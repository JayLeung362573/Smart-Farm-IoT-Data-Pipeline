import threading
import time
import queue
import random
from ingestion import start_workers

data_queue = queue.Queue(maxsize=2000)

def virtual_sensor(sensor_id):
    while(True):
        payload = {
            "sensor_id": sensor_id,
            "moisture": round(random.uniform(30,70),2),
            "temperature": round(random.uniform(10,30),2)
        }

        data_queue.put(payload)
        time.sleep(random.uniform(0,1))

if __name__ == "__main__":
    print("Starting BD workers...")
    start_workers(data_queue)

    print(f"Launching 500 sensors...")
    for i in range(500):
        sensor_thread = threading.Thread(target=virtual_sensor, args=(i,), daemon=True)
        sensor_thread.start()

    try:
        while True:
            print(f"Data Queue Size: {data_queue.qsize()} items waiting for ingestion...")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nSimulator stopped.")