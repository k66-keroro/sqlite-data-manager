#!/usr/bin/env python3
"""
T002: 修正されたloader.pyの動作テスト
1ファイルのみで型変換が正常に動作するかをテスト
"""

import os
import sys
import sqlite3
import pandas as pd
from config import OUTPUT_DIR, DATA_DIR
from loader import SimpleFileProcessor, convert_dataframe_types, save_with_types, get_inferred_info, sanitize_table_name

def test_single_file():
    """1ファイルでの型変換テスト"""
    
    print("=== T002: 型変換テスト開始 ===")
    
    # ファイル設定
    test_file = "zp58.txt"
    file_path = os.path.join(DATA_DIR, test_file)
    db_path = os.path.join(OUTPUT_DIR, "master.db")
    
    if not os.path.exists(file_path):
        print(f"テストファイルが見つかりません: {file_path}")
        return
    
    # ファイル読み込み
    processor = SimpleFileProcessor()
    df, encoding_used, delimiter_used = processor.process_file(file_path)
    
    if df is None:
        print("ファイル読み込み失敗")
        return
    
    print(f"ファイル読み込み成功:")
    print(f"  形状: {df.shape}")
    print(f"  エンコーディング: {encoding_used}")
    print(f"  区切り文字: {repr(delimiter_used)}")
    print()
    
    # 推定型情報取得
    conn = sqlite3.connect(db_path)
    inferred_schema = get_inferred_info(conn, test_file)
    
    print(f"推定型情報:")
    for col, dtype in list(inferred_schema.items())[:5]:  # 最初の5列のみ表示
        print(f"  {col:20}: {dtype}")
    print(f"  ... (計{len(inferred_schema)}列)")
    print()
    
    # 型変換実行
    print("型変換実行中...")
    df_typed = convert_dataframe_types(df, inferred_schema)
    
    # 型変更の確認
    print("型変換結果:")
    for col in df.columns[:5]:  # 最初の5列のみ
        original_type = str(df[col].dtype)
        converted_type = str(df_typed[col].dtype)
        inferred_type = inferred_schema.get(col, "不明")
        print(f"  {col:20}: {original_type:10} -> {converted_type:10} (推定: {inferred_type})")
    print()
    
    # SQLiteに保存
    table_name = sanitize_table_name(test_file)
    print(f"SQLiteに保存中... (テーブル名: {table_name})")
    
    try:
        save_with_types(df_typed, table_name, conn, inferred_schema)
        print("SQLite保存成功！")
    except Exception as e:
        print(f"SQLite保存失敗: {e}")
        return
    
    # 結果確認
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_info = cursor.fetchall()
    
    print("作成されたテーブル構造:")
    for info in table_info[:5]:  # 最初の5列のみ表示
        col_name, col_type = info[1], info[2]
        expected_type = inferred_schema.get(col_name, "TEXT")
        match = "○" if col_type == expected_type else "×"
        print(f"  {col_name:20}: {col_type:10} (期待: {expected_type:10}) {match}")
    
    if len(table_info) > 5:
        print(f"  ... (計{len(table_info)}列)")
    
    conn.close()
    print("\n=== T002: 型変換テスト完了 ===")

if __name__ == "__main__":
    test_single_file()
