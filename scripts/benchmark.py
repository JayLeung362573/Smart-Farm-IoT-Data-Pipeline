import psycopg2
import time

def run_benchmark():
    conn = psycopg2.connect(dbname="smart_farm", user="postgres", password="3221", host="127.0.0.1")
    cur = conn.cursor()

    print("Starting 10-second throughput benchmark.")
    
    cur.execute("SELECT count(*) FROM sensor_data;")
    start_count = cur.fetchone()[0]
    start_time = time.time()

    time.sleep(10)

    cur.execute("SELECT count(*) FROM sensor_data;")
    end_count = cur.fetchone()[0]
    end_time = time.time()

    total_rows = end_count - start_count
    total_time = end_time - start_time
    rps = total_rows / total_time

    print("-" * 30)
    print(f"Total Rows Ingested: {total_rows}")
    print(f"Elapsed Time: {total_time:.2f}s")
    print(f"Throughput: {rps:.2f} Rows/Sec")
    print("-" * 30)

    cur.close()
    conn.close()

if __name__ == "__main__":
    run_benchmark()