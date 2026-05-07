import time
import uuid
import random
import psycopg2
from psycopg2 import extras
from config import Config

NUM_RECORDS = 5000

def generate_data():
    return [
        (
            random.randint(0, 499),
            round(random.uniform(30, 70), 2),
            round(random.uniform(10, 30), 2),
            str(uuid.uuid4())
        )
        for _ in range(NUM_RECORDS)
    ]

def single_insert(data):
    conn = psycopg2.connect(**Config.get_db_params())
    cur = conn.cursor()

    start = time.time()

    for row in data:
        cur.execute("""
            INSERT INTO sensor_data (sensor_id, moisture, temperature, event_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (event_id, created_at) DO NOTHING;
        """, row)

    conn.commit()

    end = time.time()

    cur.close()
    conn.close()

    return end - start

def batch_insert(data):
    conn = psycopg2.connect(**Config.get_db_params())
    cur = conn.cursor()

    start = time.time()

    extras.execute_values(
        cur,
        """
        INSERT INTO sensor_data (sensor_id, moisture, temperature, event_id)
        VALUES %s
        ON CONFLICT (event_id, created_at) DO NOTHING;
        """,
        data
    )

    conn.commit()

    end = time.time()

    cur.close()
    conn.close()

    return end - start

def main():
    data1 = generate_data()
    data2 = generate_data()

    print(f"Testing {NUM_RECORDS} records...")

    single_time = single_insert(data1)
    batch_time = batch_insert(data2)

    speedup = single_time / batch_time

    print("\n===== Insert Benchmark Results =====")
    print(f"Single-row insert time: {single_time:.2f}s")
    print(f"Batch insert time: {batch_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x faster")


if __name__ == "__main__":
    main()