import time
import requests
import statistics

URL = "http://localhost:8000/fields/1/summary"
NUM_REQUESTS = 100

def main():
    latencies = []

    print(f"Benchmarking {URL}")
    print(f"Requests: {NUM_REQUESTS}")

    for _ in range(NUM_REQUESTS):
        start = time.time()
        response = requests.get(URL)
        end = time.time()

        if response.status_code == 200:
            latencies.append((end - start) * 1000)
        else:
            print(f"Request failed: {response.status_code}")

    print("\n===== API Benchmark Results =====")
    print(f"Average latency: {statistics.mean(latencies):.2f} ms")
    print(f"Median latency: {statistics.median(latencies):.2f} ms")
    print(f"Min latency: {min(latencies):.2f} ms")
    print(f"Max latency: {max(latencies):.2f} ms")


if __name__ == "__main__":
    main()