from src.config import Config
import psycopg2


def refresh_views():
    conn = psycopg2.connect(**Config.get_db_params())

    try:
        with conn.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW hourly_sensor_stats;")
        conn.commit()
        print("Refreshed materialized view: hourly_sensor_stats")
    finally:
        conn.close()


if __name__ == "__main__":
    refresh_views()