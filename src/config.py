
import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def get_database_config():
    required_variables = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]

    missing_variables = [
        name for name in required_variables
        if not os.getenv(name)
    ]

    if missing_variables:
        raise ValueError(
            f"Missing database settings: {', '.join(missing_variables)}"
        )

    return {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT")),
        "dbname": os.getenv("DB_NAME"),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
    }
