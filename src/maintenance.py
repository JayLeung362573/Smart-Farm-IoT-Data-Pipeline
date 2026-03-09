import psycopg2
import logging
import os

def run_maintenance():
    db_host = os.getenv("DB_HOST", "127.0.0.1")
    db_password = os.getenv("DB_PASSWORD", "3221")

    try:
        conn = psycopg2.connect(
            dbname="smart_farm", 
            user="postgres", 
            password=db_password,
            host=db_host,
            port="5432"
        )

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