import sqlite3
import pandas as pd
from pathlib import Path
from config import DB_FILE, OUTPUT_DIR # configからDB_FILEとOUTPUT_DIRをインポート
import os

DB_PATH = Path(DB_FILE) # config.pyからDB_FILEを取得するように変更

def init_master():
    """マスタDBを初期化（テーブルがなければ作成）"""
    # DB_FILEがOUTPUT_DIR内にあることを想定し、OUTPUT_DIRが存在することを確認
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS column_master (
            file_name TEXT,
            column_name TEXT,
            data_type TEXT,
            initial_inferred_type TEXT, -- 初期推定型を追加
            encoding TEXT,
            delimiter TEXT,
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
