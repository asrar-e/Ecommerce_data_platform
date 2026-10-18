
from src.config import get_database_config

config = get_database_config()

print({
    "host": config["host"],
    "port": config["port"],
    "dbname": config["dbname"],
    "user": config["user"],
    "password": "***",
})
