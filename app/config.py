import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "Argueta+2003")
    DB_NAME = os.getenv("DB_NAME", "Sistema_Facturacion")
    PORT = int(os.getenv("PORT", "5000"))
