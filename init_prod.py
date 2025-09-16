import sqlite3
import logging # 追加
from config import DB_FILE

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s') # 追加

def init_db_prod() -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        # テーブルが存在しない場合は作成
        cur.execute("""
            CREATE TABLE IF NOT EXISTS column_master (
                file_name TEXT,
                column_name TEXT,
                data_type TEXT,
                initial_inferred_type TEXT,
                encoding TEXT,
                delimiter TEXT,
                PRIMARY KEY (file_name, column_name)
            )
        """)

        # initial_inferred_type列がなければ追加
        cur.execute("PRAGMA table_info(column_master)")
        columns = [row[1] for row in cur.fetchall()]
        if "initial_inferred_type" not in columns:
            cur.execute("ALTER TABLE column_master ADD COLUMN initial_inferred_type TEXT")

        if "encoding" not in columns:
            cur.execute("ALTER TABLE column_master ADD COLUMN encoding TEXT")
            

        if "delimiter" not in columns:
            cur.execute("ALTER TABLE column_master ADD COLUMN delimiter TEXT")
            

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"本番用DB初期化中にエラーが発生しました: {e}") # ログ出力追加
        return False
    
