# app/db.py
import os
import mysql.connector
from mysql.connector import pooling
from .config import Config

_connection_pool = pooling.MySQLConnectionPool(
    pool_name="pool_sf",
    pool_size=5,
    host=Config.DB_HOST,
    user=Config.DB_USER,
    password=Config.DB_PASS,
    database=Config.DB_NAME,
    port=int(os.getenv("DB_PORT", 3306))
)

def get_conn():
    return _connection_pool.get_connection()
