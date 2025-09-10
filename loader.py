import os
import pandas as pd
import sqlite3
from typing import Optional, Tuple, Dict, List
from config import DATA_DIR, DB_FILE, OUTPUT_DIR, DELIMITERS, ENCODINGS, SKIP_EXTENSIONS

def detect_delimiter_simple(file_path: str, encoding: str) -> str:
    """シンプルな区切り文字検出"""
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            # 最初の数行を読む
            sample_text = ""
            for i in range(5):
                line = f.readline()
                if not line:
                    break
                sample_text += line
        
        # 各区切り文字の出現回数をカウント
        delimiter_counts = {}
        for delimiter in ['\t', ',', '|', ';']:  # よく使われる区切り文字
            count = sample_text.count(delimiter)
            if count > 0:
                delimiter_counts[delimiter] = count
        
        # 最も多い区切り文字を返す（なければタブ）
        if delimiter_counts:
            return max(delimiter_counts.keys(), key=delimiter_counts.get)
        else:
            return '\t'  # デフォルト
            
    except Exception:
        return '\t'

def safe_read_csv(file_path: str, encoding: str, delimiter: str) -> Optional[pd.DataFrame]:
    """安全なCSV読み込み（pandas バージョン問わず動作）"""
    try:
        # 基本的な引数のみ使用
        df = pd.read_csv(
            file_path,
            sep=delimiter,  # delimiterの代わりにsepを使用
            dtype=str,
            encoding=encoding,
            engine='python',
            nrows=1000,  # サンプルのみ
            na_filter=False  # NaN変換を無効化
        )
        return df
    except Exception:
        return None

class SimpleFileProcessor:
    """シンプルなファイル処理クラス"""
    
    def process_excel(self, file_path: str) -> Tuple[Optional[pd.DataFrame], str, Optional[str]]:
        """Excelファイル処理"""
        try:
            df = pd.read_excel(file_path, dtype=str, nrows=1000)
            if df.empty:
                return None, None, None
            return df, "excel", None
        except Exception as e:
            print(f"Excel読み込み失敗: {os.path.basename(file_path)} - {e}")
            return None, None, None
    
    def process_text(self, file_path: str) -> Tuple[Optional[pd.DataFrame], str, str]:
        """テキスト/CSVファイル処理"""
        file_name = os.path.basename(file_path)
        
        # エンコーディングを順番に試す
        for encoding in ['utf-8', 'cp932', 'shift_jis', 'utf-16']:
            try:
                # まず区切り文字を検出
                delimiter = detect_delimiter_simple(file_path, encoding)
                print(f"試行中: {file_name} (encoding: {encoding}, delimiter: '{delimiter}')")
                
                # CSVを読み込み
                df = safe_read_csv(file_path, encoding, delimiter)
                
                if df is not None and not df.empty and len(df.columns) > 0:
                    print(f"読み込み成功: {file_name} (encoding: {encoding}, shape: {df.shape})")
                    return df, encoding, delimiter
                
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"エラー: {file_name} (encoding: {encoding}) - {e}")
                continue
        
        print(f"読み込み失敗: {file_name} - すべてのエンコーディングで失敗")
        return None, None, None
    
    def process_file(self, file_path: str) -> Tuple[Optional[pd.DataFrame], str, Optional[str]]:
        """ファイル処理のメインメソッド"""
        file_name = os.path.basename(file_path)
        
        if file_name.lower().endswith(('.xls', '.xlsx')):
            return self.process_excel(file_path)
        else:
            return self.process_text(file_path)

def get_table_info(conn: sqlite3.Connection, table_name: str) -> Dict[str, str]:
    """テーブル情報を取得"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {row[1]: row[2] for row in cursor.fetchall()}
    except Exception:
        return {}

def get_inferred_info(conn: sqlite3.Connection, file_name: str) -> Dict[str, str]:
    """推定情報を取得"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT column_name, data_type FROM column_master WHERE file_name=?", (file_name,))
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception:
        return {}


def convert_dataframe_types(df: pd.DataFrame, inferred_schema: Dict[str, str]) -> pd.DataFrame:
    """DataFrameの列を推定型に応じて変換"""
    df_converted = df.copy()
    
    for col_name, inferred_type in inferred_schema.items():
        if col_name not in df_converted.columns:
            continue
            
        try:
            if inferred_type == "INTEGER":
                # 整数変換（エラー値はNoneに）
                df_converted[col_name] = pd.to_numeric(df_converted[col_name], errors='coerce').astype('Int64')
            elif inferred_type == "REAL":
                # 実数変換（エラー値はNoneに）
                df_converted[col_name] = pd.to_numeric(df_converted[col_name], errors='coerce').astype('float64')
            elif inferred_type == "DATETIME":
                # 日付変換 → 文字列形式で保存（SQLiteのTimestamp問題回避）
                try:
                    dt_series = pd.to_datetime(df_converted[col_name], errors='coerce')
                    # 有効な日付のみ文字列変換、無効な日付はNone
                    df_converted[col_name] = dt_series.dt.strftime('%Y-%m-%d %H:%M:%S').where(pd.notna(dt_series), None)
                except:
                    # 変換失敗時はTEXTのまま
                    pass
            # TEXTはそのまま（文字列）
        except Exception:
            # 変換に失敗した場合はTEXTのまま
            continue
    
    return df_converted


def save_with_types(df: pd.DataFrame, table_name: str, conn: sqlite3.Connection, inferred_schema: Dict[str, str]):
    """型指定付きでSQLiteテーブルを作成・保存（簡単版）"""
    
    # テーブル削除
    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
    conn.commit()
    
    # データ挿入前の安全化
    df_safe = df.copy()
    
    # すべてのNaN、NaT、pd.NAをNoneに置換
    for col in df_safe.columns:
        # pandas 特殊値をすべてNoneに統一
        try:
            mask = pd.isna(df_safe[col])
            df_safe[col] = df_safe[col].where(~mask, None)
        except:
            # 変換エラーの場合はそのまま
            pass
    
    # 単純にto_sqlを使用（型変換はDataFrame側で完了済み）
    df_safe.to_sql(table_name, conn, if_exists='replace', index=False)

def sanitize_table_name(file_name: str) -> str:
    """テーブル名をサニタイズ"""
    base_name = os.path.splitext(file_name)[0]
    # 英数字とアンダースコア以外を置換
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in base_name)
    # 先頭が数字の場合は接頭辞を追加
    if sanitized and sanitized[0].isdigit():
        sanitized = 'table_' + sanitized
    return sanitized or 'unnamed_table'

def load_and_compare():
    """メイン処理"""
    print("=== SQLite GUI Manager - Load & Compare ===")
    
    # 初期化
    processor = SimpleFileProcessor()
    results = []
    
    # ディレクトリ確認
    if not os.path.exists(DATA_DIR):
        print(f"エラー: データディレクトリが見つかりません: {DATA_DIR}")
        return
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # ファイル一覧取得
    all_files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    target_files = [f for f in all_files if not any(f.lower().endswith(ext) for ext in SKIP_EXTENSIONS)]
    
    print(f"全ファイル数: {len(all_files)}")
    print(f"処理対象: {len(target_files)}")
    print(f"スキップ: {len(all_files) - len(target_files)}")
    print("-" * 50)
    
    # データベース接続
    try:
        conn = sqlite3.connect(DB_FILE)
        print(f"データベース接続成功: {DB_FILE}")
    except Exception as e:
        print(f"データベース接続失敗: {e}")
        return
    
    processed_count = 0
    error_count = 0
    
    try:
        for i, file_name in enumerate(target_files, 1):
            print(f"\n[{i}/{len(target_files)}] 処理中: {file_name}")
            
            file_path = os.path.join(DATA_DIR, file_name)
            
            # ファイル読み込み
            df, encoding_used, delimiter_used = processor.process_file(file_path)
            
            if df is None:
                error_count += 1
                continue
            
            # テーブル名生成
            table_name = sanitize_table_name(file_name)
            
            # SQLiteに保存（型変換付き）
            try:
                # column_masterから推定型情報を取得
                inferred_schema = get_inferred_info(conn, file_name)
                
                # DataFrame列の型変換
                df_typed = convert_dataframe_types(df, inferred_schema)
                
                # SQLiteに保存（型指定付き）
                save_with_types(df_typed, table_name, conn, inferred_schema)
                print(f"SQLite保存完了: {table_name}")
                
            except Exception as e:
                print(f"SQLite保存失敗: {e}")
                error_count += 1
                continue
            except Exception as e:
                print(f"SQLite保存失敗: {e}")
                error_count += 1
                continue
            
            # スキーマ比較
            actual_schema = get_table_info(conn, table_name)
            inferred_schema = get_inferred_info(conn, file_name)
            
            # 結果作成
            for col_name, actual_type in actual_schema.items():
                inferred_type = inferred_schema.get(col_name, "（未登録）")
                match = (actual_type.upper() == inferred_type.upper()) if inferred_type != "（未登録）" else False
                
                results.append({
                    "File": file_name,
                    "Column": col_name,
                    "Inferred_Type": inferred_type,
                    "Actual_Type": actual_type,
                    "Match": "○" if match else "×",
                    "Encoding": encoding_used,
                    "Delimiter": delimiter_used
                })
            
            processed_count += 1
            print(f"完了: {file_name} (列数: {len(actual_schema)})")
    
    except KeyboardInterrupt:
        print("\n処理が中断されました")
    
    finally:
        conn.close()
    
    # 結果出力
    print("\n" + "=" * 50)
    print(f"処理結果:")
    print(f"  成功: {processed_count} ファイル")
    print(f"  失敗: {error_count} ファイル")
    print(f"  総行数: {len(results)} 行")
    
    if results:
        report_path = os.path.join(OUTPUT_DIR, "compare_report.csv")
        try:
            pd.DataFrame(results).to_csv(report_path, index=False, encoding="utf-8-sig")
            print(f"\n 比較結果を出力しました → {report_path}")
        except Exception as e:
            print(f" CSV出力失敗: {e}")
    else:
        print(" 処理可能なファイルがありませんでした")

if __name__ == "__main__":
    load_and_compare()