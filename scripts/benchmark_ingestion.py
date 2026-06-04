import argparse
import subprocess
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Smart Farm ingestion benchmark through Docker Compose."
    )

    parser.add_argument("--sensors", type=int, default=500)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--duration", type=int, default=60)

    return parser.parse_args()


def main():
    args = parse_args()

    command = [
        "docker-compose",
        "run",
        "--rm",
        "--no-deps",
        "-e", "DB_HOST=db",
        "-e", "DB_PORT=5432",
        "-e", "DB_NAME=smart_farm",
        "-e", "DB_USER=postgres",
        "-e", "DB_PASSWORD=3221",
        "-e", f"SENSOR_COUNT={args.sensors}",
        "-e", f"INGESTION_WORKERS={args.workers}",
        "-e", f"BATCH_SIZE={args.batch_size}",
        "-e", f"RUN_SECONDS={args.duration}",
        "engine",
        "python",
        "src/simulator.py",
    ]

    print("Running ingestion benchmark with:")
    print(f"  sensors:    {args.sensors}")
    print(f"  workers:    {args.workers}")
    print(f"  batch size: {args.batch_size}")
    print(f"  duration:   {args.duration}s")
    print()

    result = subprocess.run(command)

    if result.returncode != 0:
        print("Benchmark failed.", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()