import os

# 入力データフォルダ
DATA_DIR = r"C:\Users\sem3171\sqlite-gui-manager\テキスト"

# 出力フォルダ
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SQLite DBファイル
DB_FILE = os.path.join(OUTPUT_DIR, "master.db")

# 列候補CSV
CANDIDATE_CSV = os.path.join(OUTPUT_DIR, "column_mapping_candidates.csv")

# 除外拡張子
SKIP_EXTENSIONS = [".py", ".log", ".bak", ".db"]

# デリミタ・エンコーディング候補
DELIMITERS = [",", "\t", ";", "|", " "]
ENCODINGS = ["utf-8", "cp932", "shift_jis", "utf-16"]
