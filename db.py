import sqlite3
from config import DB_FILE

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS column_master (
            file_name TEXT,
            column_name TEXT,
            data_type TEXT,
            PRIMARY KEY (file_name, column_name)
        )
    """)
    conn.commit()
    conn.close()
