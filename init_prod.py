import sqlite3
from config import DB_FILE

def init_db_prod():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # テーブルが存在しない場合は作成
    cur.execute("""
        CREATE TABLE IF NOT EXISTS column_master (
            file_name TEXT,
            column_name TEXT,
            data_type TEXT,
            encoding TEXT,
            delimiter TEXT,
            PRIMARY KEY (file_name, column_name)
        )
    """)

    # encoding列がなければ追加
    cur.execute("PRAGMA table_info(column_master)")
    columns = [row[1] for row in cur.fetchall()]
    if "encoding" not in columns:
        cur.execute("ALTER TABLE column_master ADD COLUMN encoding TEXT")
        print("テーブルに encoding 列を追加しました")

    if "delimiter" not in columns:
        cur.execute("ALTER TABLE column_master ADD COLUMN delimiter TEXT")
        print("テーブルに delimiter 列を追加しました")

    conn.commit()
    conn.close()
    print(f"DBチェック完了（本番モード）: {DB_FILE}")
