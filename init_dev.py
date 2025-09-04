import os
import sqlite3
from config import DB_FILE

def init_db_dev():
    # 既存DB削除
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"古いDBを削除しました: {DB_FILE}")

    # 新規作成
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE column_master (
            file_name TEXT,
            column_name TEXT,
            data_type TEXT,
            encoding TEXT,
            delimiter TEXT,
            PRIMARY KEY (file_name, column_name)
        )
    """)
    conn.commit()
    conn.close()
    print(f"新しいDBを作成しました: {DB_FILE}")
