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

