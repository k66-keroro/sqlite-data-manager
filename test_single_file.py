#!/usr/bin/env python3
"""
単一ファイルでの日付変換テスト
"""

import os
import pandas as pd
import sqlite3
from loader import SimpleFileProcessor, convert_dataframe_types, get_inferred_info, save_with_types
from sqlalchemy import create_engine

def test_single_file():
    """zm21.txtファイルで日付変換をテスト"""
    
    print("=== 単一ファイル日付変換テスト ===")
    
    # ファイル処理
    processor = SimpleFileProcessor()
    file_path = r"C:\Users\sem3171\sqlite-gui-manager\テキスト\zm21.txt"
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    # ファイル読み込み
    df, encoding_used, delimiter_used = processor.process_file(file_path)
    
    if df is None:
        print("ファイル読み込み失敗")
        return
    
    print(f"読み込み成功: shape={df.shape}, encoding={encoding_used}")
    
    # 日付列の元データを確認
    if '発注日付' in df.columns:
        print(f"\n発注日付の元データ (先頭5件):")
        print(df['発注日付'].head().tolist())
    
    # データベース接続
    engine = create_engine("sqlite:///output/master.db")
    
    # column_masterから推定型情報を取得
    inferred_schema = get_inferred_info(engine, "zm21.txt")
    print(f"\n推定スキーマ:")
    date_fields = {k: v for k, v in inferred_schema.items() if 'DATETIME' in v}
    for field, dtype in date_fields.items():
        print(f"  {field}: {dtype}")
    
    # DataFrame列の型変換（修正版）
    print(f"\n=== 型変換実行 ===")
    df_typed = convert_dataframe_types(df, inferred_schema, "zm21.txt")
    
    # 変換後の日付列を確認
    if '発注日付' in df_typed.columns:
        print(f"\n発注日付の変換後データ (先頭5件):")
        print(df_typed['発注日付'].head().tolist())
        print(f"データ型: {df_typed['発注日付'].dtype}")

if __name__ == "__main__":
    test_single_file()