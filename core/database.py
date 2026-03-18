"""
Conexão com PostgreSQL usando psycopg2 com RealDictCursor.
Compatível com o banco já existente do projeto Streamlit.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from core.config import settings


def get_connection():
    conn = psycopg2.connect(
        host=settings.DB_HOST,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        port=settings.DB_PORT,
        sslmode="require"
    )
    return conn


def get_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)
