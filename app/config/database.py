import psycopg2
from psycopg2 import pool
from .settings import settings

connection_pool = None

def init_db_pool():
    global connection_pool
    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,
            dsn=settings.DATABASE_URL
        )
        if connection_pool:
            print("Database connection pool created successfully")
    except Exception as e:
        print(f"Error creating database connection pool: {e}")
        raise

def get_db_connection():
    if connection_pool:
        return connection_pool.getconn()
    else:
        raise Exception("Connection pool not initialized")

def return_db_connection(conn):
    if connection_pool:
        connection_pool.putconn(conn)

def close_db_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("Database connection pool closed")
