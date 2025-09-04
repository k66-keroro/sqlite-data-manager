import os
import pandas as pd
import sqlite3
from config import DELIMITERS, ENCODINGS, SKIP_EXTENSIONS

def infer_sqlite_type(series, column_name):
    s = series.dropna().astype(str)
    if len(s) == 0:
        return "TEXT"

    # コード系は無条件でTEXT
    if any(key in column_name.upper() for key in ["CD", "コード", "ID", "NO", "番号", "指図", "ネットワーク"]):
        return "TEXT"

    # 0パディング混在はTEXT
    if all(x.isdigit() for x in s) and any(x.startswith("0") for x in s):
        return "TEXT"

    # 日付判定
    date_formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m-%d %H:%M:%S", "%H:%M:%S"]
    for fmt in date_formats:
        try:
            pd.to_datetime(s, format=fmt, errors="raise")
            return "DATETIME"
        except Exception:
            continue

    try:
        s.astype(int)
        return "INTEGER"
    except Exception:
        pass
    try:
        s.astype(float)
        return "REAL"
    except Exception:
        pass

    return "TEXT"

def detect_delimiter(file_path, encoding, sample_lines=5):
    """複数行を使って区切り文字を推定する"""
    with open(file_path, "r", encoding=encoding, errors="ignore") as f:
        lines = [f.readline() for _ in range(sample_lines)]
    text = "".join(lines)
    counts = {d: text.count(d) for d in DELIMITERS}
    return max(counts, key=counts.get)


def analyze_files(data_dir, output_file, db_file="master.db"):
    results = []

    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)

        if not os.path.isfile(file_path):
            continue
        if any(file_name.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
            continue

        # Excel
        if file_name.lower().endswith((".xls", ".xlsx")):
            try:
                df = pd.read_excel(file_path, nrows=200, dtype=str)
                for col in df.columns:
                    sqlite_type = infer_sqlite_type(df[col], col)
                    results.append({
                        "File": file_name,
                        "Column": col,
                        "Inferred_Type": sqlite_type,
                        "Encoding": "excel",
                        "Delimiter": None
                    })
                continue
            except Exception as e:
                print(f"読み込み失敗(Excel): {file_name}, {e}")
                continue

        # テキスト/CSV
        success = False
        for enc in ENCODINGS:
            try:
                delimiter = detect_delimiter(file_path, enc)
                df = pd.read_csv(file_path, delimiter=delimiter, dtype=str, nrows=200, encoding=enc, engine="python")
                for col in df.columns:
                    sqlite_type = infer_sqlite_type(df[col], col)
                    results.append({
                        "File": file_name,
                        "Column": col,
                        "Inferred_Type": sqlite_type,
                        "Encoding": enc,
                        "Delimiter": delimiter
                    })
                success = True
                break
            except Exception:
                continue

        if not success:
            print(f"読み込み失敗: {file_name}")

    # CSV保存
    pd.DataFrame(results).to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"列候補を出力しました → {output_file}")

    # SQLiteに保存
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

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

    for row in results:
        cur.execute("""
            INSERT INTO column_master (file_name, column_name, data_type, encoding, delimiter)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(file_name, column_name)
            DO UPDATE SET 
                data_type=excluded.data_type,
                encoding=excluded.encoding,
                delimiter=excluded.delimiter
        """, (row["File"], row["Column"], row["Inferred_Type"], row.get("Encoding"), row.get("Delimiter")))

    conn.commit()
    conn.close()
    print(f"SQLiteに保存しました → {db_file}")
