import os
import mysql.connector

DB_CFG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", ""),
    "port": int(os.getenv("DB_PORT", "3306")),
}

def get_conn():
    print("🔌 Conectando a:", DB_CFG)  # <-- Línea temporal para debug
    return mysql.connector.connect(**DB_CFG)
