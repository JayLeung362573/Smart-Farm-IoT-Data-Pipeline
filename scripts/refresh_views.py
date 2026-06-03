import os
import psycopg2


def refresh_views():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "smart_farm"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "3221"),
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=os.getenv("DB_PORT", "5432"),
    )

    try:
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW hourly_sensor_stats;")
        conn.commit()
        print("Refreshed materialized view: hourly_sensor_stats")
    finally:
        conn.close()


if __name__ == "__main__":
    refresh_views()