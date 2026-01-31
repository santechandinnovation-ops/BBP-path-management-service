import psycopg2
from psycopg2 import pool, OperationalError
from .settings import settings
import logging

logger = logging.getLogger(__name__)

connection_pool = None

def _get_connection_kwargs():
    """get connection params with keepalive stuff"""
    return {
        'dsn': settings.DATABASE_URL,
        # TCP keepalive settings so we can detect dead conections
        'keepalives': 1,
        'keepalives_idle': 30,      # start keepalive after 30sec idle
        'keepalives_interval': 10,  # send keepalive evry 10sec
        'keepalives_count': 5,      # close after 5 failed keepalives
        'connect_timeout': 10,      # conection timeout
    }

def init_db_pool():
    global connection_pool
    try:
        kwargs = _get_connection_kwargs()
        connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20, **kwargs
        )
        if connection_pool:
            logger.info("Database connection pool created successfully")
    except Exception as e:
        logger.error(f"Error creating database connection pool: {e}")
        raise

def _test_connection(conn):
    """check if conection is still working"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except (OperationalError, psycopg2.InterfaceError):
        return False

def get_db_connection():
    """get a conection from pool with helth check"""
    global connection_pool
    if not connection_pool:
        raise Exception("Connection pool not initialized")
    
    conn = connection_pool.getconn()
    
    # test if the conection is still valid
    if not _test_connection(conn):
        logger.warning("Stale connection detected, reconnecting...")
        try:
            conn.close()
        except Exception:
            pass
        # put back the dead conection and get a new one
        connection_pool.putconn(conn, close=True)
        conn = connection_pool.getconn()
        
        # make sure the new conection actualy works
        if not _test_connection(conn):
            raise Exception("Failed to establish database connection")
    
    return conn

def return_db_connection(conn):
    """return conection to pool, close if its broken"""
    global connection_pool
    if connection_pool and conn:
        try:
            # check if conection is usable before puting back in pool
            if conn.closed:
                connection_pool.putconn(conn, close=True)
            else:
                connection_pool.putconn(conn)
        except Exception as e:
            logger.warning(f"Error returning connection to pool: {e}")
            try:
                connection_pool.putconn(conn, close=True)
            except Exception:
                pass

def close_db_pool():
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        logger.info("Database connection pool closed")
