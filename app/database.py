import psycopg2
from psycopg2 import pool
import psycopg2.extras
from contextlib import contextmanager
from app.config import settings

# Register the UUID adapter so that Python uuid.UUID objects are
# properly converted for PostgreSQL UUID columns.
psycopg2.extras.register_uuid()

# Connection pool (initialized on startup)
connection_pool = None


def init_pool():
    """Initialize the PostgreSQL connection pool."""
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=settings.db_connection_string,
        )
        print("[OK] PostgreSQL connection pool created successfully.")
    except Exception as e:
        print(f"[ERROR] Error creating PostgreSQL connection pool: {e}")
        raise


def close_pool():
    """Close all connections in the pool."""
    global connection_pool
    if connection_pool:
        connection_pool.closeall()
        print("[INFO] PostgreSQL connection pool closed.")


@contextmanager
def get_db_cursor():
    """
    Context manager that provides a database cursor.
    Automatically commits on success, rolls back on error,
    and returns the connection to the pool.
    """
    conn = connection_pool.getconn()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        connection_pool.putconn(conn)


def init_db():
    """Create required tables if they don't exist."""
    with get_db_cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                references_data TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_session_id
            ON chat_history(session_id);
        """)
    print("[OK] Database tables initialized.")
