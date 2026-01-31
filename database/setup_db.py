import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        with open('database/init_path_tables.sql', 'r') as f:
            sql_script = f.read()

        cursor.execute(sql_script)
        conn.commit()

        print("Path Management tables created successfully")
        print("  - PathInfo table")
        print("  - Segments table")
        print("  - Obstacles table")
        print("  - Indexes created")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"ERROR creating tables: {e}")
        raise

if __name__ == "__main__":
    setup_database()
