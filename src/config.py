import os


class Config:
    @staticmethod
    def get_db_params():
        """Read database settings from the current environment."""
        return {
            "host": os.getenv("DB_HOST", "127.0.0.1"),
            "port": os.getenv("DB_PORT", "5432"),
            "database": os.getenv("DB_NAME", "smart_farm"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "3221"),
        }