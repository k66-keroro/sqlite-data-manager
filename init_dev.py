import os
import sqlite3
import logging # 追加
from config import DB_FILE

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s') # 追加

def init_db_dev() -> bool:
    try:
        # 既存DB削除
        if os.path.exists(DB_FILE):
            os.remove(DB_FILE)
            

        # 新規作成
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE column_master (
                file_name TEXT,
                column_name TEXT,
                data_type TEXT,
                initial_inferred_type TEXT,
                encoding TEXT,
                delimiter TEXT,
                PRIMARY KEY (file_name, column_name)
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"開発用DB初期化中にエラーが発生しました: {e}") # ログ出力追加
        return False
    
