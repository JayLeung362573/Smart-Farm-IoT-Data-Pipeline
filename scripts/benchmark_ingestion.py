import argparse
import subprocess
import sys
import json


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run the Smart Farm ingestion benchmark through Docker Compose."
    )

    parser.add_argument("--sensors", type=int, default=500)
    parser.add_argument("--workers", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save the parsed benchmark summary as JSON."
    )

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

    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Benchmark failed.", file=sys.stderr)
        sys.exit(result.returncode)
    
    summary_line = None
    for line in result.stdout.splitlines():
        if line.startswith("BENCHMARK_SUMMARY:"):
            summary_line = line
            break

    if summary_line is None:
        print("Benchmark completed, but no BENCHMARK_SUMMARY line was found.", file=sys.stderr)
        sys.exit(1)

    summary_json = summary_line.replace("BENCHMARK_SUMMARY:", "", 1).strip()
    summary = json.loads(summary_json)

    print("\nParsed benchmark summary:")
    print(json.dumps(summary, indent=2))

    if args.output:
        from pathlib import Path

        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
            f.write("\n")

        print(f"\nSaved benchmark summary to: {output_path}")
    

if __name__ == "__main__":
    main()