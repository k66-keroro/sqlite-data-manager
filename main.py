import sys
from config import DATA_DIR, CANDIDATE_CSV, DB_FILE
from analyzer import analyze_files
from init_dev import init_db_dev
from init_prod import init_db_prod
from loader import load_and_compare  # ← 追加

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python main.py [init_dev | init_prod | analyze | load]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init_dev":
        init_db_dev()

    elif cmd == "init_prod":
        init_db_prod()

    elif cmd == "analyze":
        print(f"使用中のDBファイル: {DB_FILE}")
        analyze_files(DATA_DIR, CANDIDATE_CSV, DB_FILE)

    elif cmd == "load":
        load_and_compare()

    else:
        print(f"不明なコマンド: {cmd}")
        print("使い方: python main.py [init_dev | init_prod | analyze | load]")
