import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(r"C:\Projects_workspace\03_python\master.db")

def init_master():
    """マスタDBを初期化（テーブルがなければ作成）"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS column_master (
            file_name TEXT,
            column_name TEXT,
            data_type TEXT,
            PRIMARY KEY(file_name, column_name)
        )
        """)
    print(f"✅ マスタ初期化済み: {DB_PATH}")

def load_master():
    """マスタを読み込んでDataFrameで返す"""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql("SELECT * FROM column_master", conn)

def update_master(candidates: pd.DataFrame):
    """差分候補をマスタに追加"""
    with sqlite3.connect(DB_PATH) as conn:
        candidates.to_sql("column_master", conn, if_exists="append", index=False)
    print("✅ マスタ更新完了")
