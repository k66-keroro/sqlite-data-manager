import os
import pandas as pd

DATA_DIR = r"C:\Users\sem3171\sqlite-gui-manager\テキスト"
OUTPUT_FILE = r"C:\Users\sem3171\sqlite-gui-manager\column_mapping_candidates.csv"

DELIMITERS = [",", "\t", ";", "|", " "]
ENCODINGS = ["utf-8", "cp932", "shift_jis", "utf-16"]

def infer_sqlite_type(series, column_name):
    s = series.dropna().astype(str)

    if len(s) == 0:
        return "TEXT"

    if any(key in column_name.upper() for key in ["CD", "コード", "ID", "NO", "番号", "指図", "ネットワーク"]):
        return "TEXT"

    if all(x.isdigit() for x in s) and any(x.startswith("0") for x in s):
        return "TEXT"

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

def detect_delimiter(file_path, encoding):
    with open(file_path, "r", encoding=encoding, errors="ignore") as f:
        first_line = f.readline()
        counts = {d: first_line.count(d) for d in DELIMITERS}
        return max(counts, key=counts.get)

results = []
SKIP_EXTENSIONS = [".py", ".log", ".bak"]

for file_name in os.listdir(DATA_DIR):
    file_path = os.path.join(DATA_DIR, file_name)

    if not os.path.isfile(file_path):
        continue

    # 除外拡張子はスキップ
    if any(file_name.lower().endswith(ext) for ext in SKIP_EXTENSIONS):
        continue

    # Excelファイルはread_excelで処理
    if file_name.lower().endswith((".xls", ".xlsx")):
        try:
            df = pd.read_excel(file_path, nrows=200, dtype=str)
            for col in df.columns:
                sqlite_type = infer_sqlite_type(df[col], col)
                results.append({"File": file_name, "Column": col, "Inferred_Type": sqlite_type})
            continue
        except Exception as e:
            print(f"読み込み失敗(Excel): {file_name}, {e}")
            continue

    # テキスト/CSV系
    success = False
    for enc in ENCODINGS:
        try:
            delimiter = detect_delimiter(file_path, enc)
            df = pd.read_csv(file_path, delimiter=delimiter, dtype=str, nrows=200, encoding=enc, engine="python")
            for col in df.columns:
                sqlite_type = infer_sqlite_type(df[col], col)
                results.append({"File": file_name, "Column": col, "Inferred_Type": sqlite_type})
            success = True
            break
        except Exception as e:
            continue

    if not success:
        print(f"読み込み失敗: {file_name}")

# CSV保存
pd.DataFrame(results).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
print(f"列候補を出力しました → {OUTPUT_FILE}")
