from psycopg2 import pool

from src.config import Config


def create_db_pool():
    """Create a new database connection pool when called."""
    return pool.SimpleConnectionPool(
        1, 20, **Config.get_db_params()
    )