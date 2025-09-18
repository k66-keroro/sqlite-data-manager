import os
import pandas as pd
import sqlite3
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy import types as sql_types
from config import DATA_DIR, DB_FILE, OUTPUT_DIR, SKIP_EXTENSIONS

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
            
    except Exception: # E722: Do not use bare `except`
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
    except Exception: # E722: Do not use bare `except`
        return None

class SimpleFileProcessor:
    """シンプルなファイル処理クラス"""
    
    def process_excel(self, file_path: str) -> Tuple[Optional[pd.DataFrame], str, Optional[str]]:
        """Excelファイル処理"""
        try:
            df = pd.read_excel(file_path, dtype=str, nrows=1000)
            if df.empty:
                print(f"デバッグ: Excelファイルが空です: {os.path.basename(file_path)}")
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
                elif df is not None and df.empty:
                    print(f"デバッグ: テキスト/CSVファイルが空です: {file_name} (encoding: {encoding})")
                    return None, None, None
                
            except UnicodeDecodeError as ude:
                print(f"デバッグ: UnicodeDecodeError: {file_name} (encoding: {encoding}) - {ude}")
                continue
            except Exception as e:
                print(f"デバッグ: その他のエラー: {file_name} (encoding: {encoding}) - {e}")
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

def get_table_info(engine: Engine, table_name: str) -> Dict[str, str]:
    """テーブル情報を取得"""
    try:
        with engine.connect() as connection:
            # PRAGMA文はtext()でラップする必要がある
            result = connection.execute(text(f"PRAGMA table_info({table_name})"))
            return {row[1]: row[2] for row in result}
    except Exception: # E722: Do not use bare `except`
        return {}

def get_inferred_info(engine: Engine, file_name: str) -> Dict[str, str]:
    """推定情報を取得"""
    try:
        with engine.connect() as connection:
            query = text("SELECT column_name, data_type FROM column_master WHERE file_name=:file_name")
            result = connection.execute(query, {"file_name": file_name})
            return {row[0]: row[1] for row in result}
    except Exception: # E722: Do not use bare `except`
        return {}

def convert_dataframe_types(df: pd.DataFrame, inferred_schema: Dict[str, str], file_name: str) -> pd.DataFrame:
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
                # 日付変換。複数フォーマットを試行して安全に変換
                try:
                    # まず元の値をそのまま保持
                    original_values = df_converted[col_name].copy()
                    
                    # 複数の日付フォーマットを試行
                    date_formats = [
                        None,  # pandasの自動推論を最初に試す
                        '%Y%m%d',
                        '%Y/%m/%d',
                        '%Y-%m-%d',
                        '%d.%m.%Y',
                        '%m/%d/%Y',
                        '%Y.%m.%d'
                    ]
                    
                    converted = None
                    for fmt in date_formats:
                        try:
                            if fmt is None:
                                # 自動推論を試す
                                converted = pd.to_datetime(original_values, errors='coerce')
                            else:
                                # 特定フォーマットを試す
                                converted = pd.to_datetime(original_values, format=fmt, errors='coerce')
                            
                            # 変換成功率をチェック（50%以上成功なら採用）
                            success_rate = (converted.notna().sum() / len(converted))
                            if success_rate >= 0.5:
                                df_converted[col_name] = converted
                                print(f"日付変換成功: {col_name} (フォーマット: {fmt or 'auto'}, 成功率: {success_rate:.1%})")
                                break
                        except Exception:
                            continue
                    else:
                        # すべての変換が失敗した場合は元の値を保持（TEXT扱い）
                        print(f"日付変換失敗: {col_name} - 元の値を保持")
                        df_converted[col_name] = original_values
                        
                except Exception as e:
                    print(f"日付変換エラー: {col_name} - {e}")
                    # 変換に失敗した場合は、列をそのままにしておく
                    pass
            # TEXTはそのまま（文字列）
        except Exception: # E722: Do not use bare `except`
            # 変換に失敗した場合はTEXTのまま
            continue
    
    return df_converted


def save_with_types(df: pd.DataFrame, table_name: str, engine: Engine, inferred_schema: Dict[str, str]):
    """
    スキーマを手動で作成し、データを追加する方式に修正。
    pandas.to_sqlのスキーマ推論に関する問題を完全に回避する。
    """
    # 1. スキーマ定義からCREATE TABLE文を動的に生成
    column_defs = []
    for col_name in df.columns:
        # column_masterに定義されている型を取得、なければTEXTをフォールバック
        sql_type = inferred_schema.get(col_name, "TEXT").upper()
        # SQLiteが理解できる型名に正規化
        if sql_type not in ["TEXT", "INTEGER", "REAL", "DATETIME"]:
            sql_type = "TEXT"
        column_defs.append(f'"{col_name}" {sql_type}')
    
    create_table_sql = f'CREATE TABLE "{table_name}" ({", ".join(column_defs)});'

    # 2. テーブルを再作成
    with engine.connect() as connection:
        # トランザクションを開始
        with connection.begin() as transaction:
            try:
                connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                connection.execute(text(create_table_sql))
            except Exception as e:
                transaction.rollback()
                raise e

    # 3. データをテーブルに追加（スキーマは作成済みなので'append'）
    # データ挿入前の安全化
    df_safe = df.copy()
    for col in df_safe.columns:
        try:
            # pandasの特殊なNA/NaT値をPythonネイティブのNoneに変換
            # これにより、データベースドライバが正しくNULLとして解釈できる
            mask = pd.isna(df_safe[col])
            df_safe[col] = df_safe[col].where(~mask, None)
        except Exception:
            pass

    df_safe.to_sql(table_name, engine, if_exists='append', index=False)

def sanitize_table_name(file_name: str) -> str:
    """テーブル名をサニタイズ"""
    base_name = os.path.splitext(file_name)[0]
    # 英数字とアンダースコア以外を置換
    sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in base_name)
    # 先頭が数字の場合は接頭辞を追加
    if sanitized and sanitized[0].isdigit():
        sanitized = 'table_' + sanitized
    return sanitized or 'unnamed_table'

def load_data():
    """メイン処理：定義されたスキーマに基づき、データをロードする"""
    print("=== SQLite GUI Manager - Data Loading ===")
    
    # 初期化
    processor = SimpleFileProcessor()
    
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
    
    # SQLAlchemy Engineの作成
    try:
        engine = create_engine(f"sqlite:///{DB_FILE}")
        print(f"データベースエンジン接続成功: {DB_FILE}")
    except Exception as e:
        print(f"データベースエンジン接続失敗: {e}")
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
                # ファイルが空の場合も成功としてカウントし、次のファイルへ
                processed_count += 1
                print(f"完了 (空ファイル): {file_name}")
                continue
            
            # テーブル名生成
            table_name = sanitize_table_name(file_name)
            
            # SQLiteに保存（型変換付き）
            try:
                # column_masterから推定型情報を取得
                inferred_schema = get_inferred_info(engine, file_name)
                
                # DataFrame列の型変換
                df_typed = convert_dataframe_types(df, inferred_schema, file_name)
                
                # SQLiteに保存（型指定付き）
                save_with_types(df_typed, table_name, engine, inferred_schema)
                print(f"SQLite保存完了: {table_name}")
                
            except Exception as e:
                print(f"SQLite保存失敗: {e}")
                error_count += 1
                continue
            
            processed_count += 1
            print(f"完了: {file_name}")
    
    except KeyboardInterrupt:
        print("\n処理が中断されました")
    
    # 結果出力
    print("\n" + "=" * 50)
    print("処理結果:")
    print(f"  成功: {processed_count} ファイル")
    print(f"  失敗: {error_count} ファイル")
    print("=" * 50)


if __name__ == "__main__":
    load_data()