import psycopg2
import logging
from src.config import Config

def run_maintenance():

    try:
        conn = psycopg2.connect(**Config.get_db_params())

        conn.autocommit = True
        cur = conn.cursor()

        logging.info("Refreshing Materialized Views")
        cur.execute("REFRESH MATERIALIZED VIEW hourly_sensor_stats;")

        logging.info("Pruning raw data older than 7 days")
        cur.execute("DELETE FROM sensor_data WHERE created_at < NOW() - INTERVAL '7 days';")

        logging.info("Maintenance Complete.")
    except Exception as e:
        logging.error(f"Maintenance Failed: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run_maintenance()