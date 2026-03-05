from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
import psycopg2
from psycopg2 import pool, extras
import logging

# 1. Initialize FastAPI
app = FastAPI(title="Smart Farm IoT API",
              description="Real-time access to partitioned sensor data",
              version="1.0.0")

# 2. Database Configuration
DB_PARAMS = {
    "user": "postgres",
    "password": "3221", 
    "host": "127.0.0.1",
    "port": "5432",
    "database": "smart_farm"
}

# 3. Setup API Connection Pool
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, **DB_PARAMS)
    print("API Connection Pool Initialized")
except Exception as e:
    print(f"Failed to initialize API pool: {e}")

# 4. Helper to handle Pool lifecycle
def get_db():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)

@app.get("/")
def health_check():
    return {"status": "online", 
            "message": "Smart Farm API is responding"}


@app.get("/sensors")
def list_sensors():
    """
    Returns a list of all registered sensors and their associated field names.
    Uses a JOIN to combine metadata from 'sensors' and 'fields'.
    """
    conn = db_pool.getconn()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT s.sensor_id, f.name as field_name, s.sensor_type, s.status
                FROM sensors s
                JOIN fields f ON s.field_id = f.field_id
                ORDER BY s.sensor_id ASC;
            """)
            
            sensors = cur.fetchall()
            
            return {"total": len(sensors), "data": sensors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)

@app.get("/sensors/{sensor_id}/latest")
def get_latest_reading(sensor_id: int):
    """
    Get the absolute latest reading for a specific sensor.
    Optimized by the (sensor_id, created_at DESC) index.
    """
    conn = db_pool.getconn()

    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT sensor_id, moisture, temperature, created_at
                FROM sensor_data
                WHERE sensor_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
            """, (sensor_id,))

            result = cur.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"No data found for sensor {sensor_id}")
            return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)

@app.get("/fields/{field_id}/summary")
def get_field_summary(field_id: int, window: str = "1h"):
    """
    Get aggregate stats for a field (avg/min/max) over a time window.
    Leverages Table Partitioning via the created_at filter.
    """

    conn = db_pool.getconn()
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    f.name as field_name,
                    COUNT(sd.id) as reading_count,
                    ROUND(AVG(sd.moisture)::numeric, 2) as avg_moisture,
                    ROUND(AVG(sd.temperature)::numeric, 2) as avg_temp
                FROM fields f
                JOIN sensors s on f.field_id = s.field_id
                JOIN sensor_data sd on s.sensor_id = sd.sensor_id
                WHERE f.field_id = %s
                    AND sd.created_at > NOW() - (%s::interval)
                GROUP BY f.name;
            """, (field_id, window))
            result = cur.fetchone()
        return result or {"message": "No data found for this field in the selected window"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_pool.putconn(conn)