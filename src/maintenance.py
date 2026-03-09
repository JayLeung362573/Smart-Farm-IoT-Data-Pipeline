import psycopg2
import logging

def run_maintenance():
    conn = psycopg2.connect(dbname="smart_farm", user="postgres", password="3221")
    conn.autocommit = True
    cur = conn.cursor()

    try:
        logging.info("Refreshing Materialized Views")
        cur.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_sensor_stats;")

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