#!/usr/bin/env python3
"""
0パディング問題を調査
"""

import pandas as pd
import os
import sqlite3
from config import DATA_DIR

def investigate_zero_padding():
    """0パディング問題を詳細調査"""
    
    print("=== 0パディング問題の調査 ===")
    
    # 1. zs58monthファイルの確認
    print("\n1. zs58monthファイルの確認")
    print("-" * 50)
    
    file_path = os.path.join(DATA_DIR, 'zs58month.txt')
    
    if os.path.exists(file_path):
        try:
            # ファイルを読み込み
            df = pd.read_csv(file_path, dtype=str, nrows=10, encoding='cp932', sep='\t', engine='python')
            
            print(f"列数: {len(df.columns)}")
            print("列名一覧:")
            for i, col in enumerate(df.columns, 1):
                print(f"{i:2d}. {col}")
            
            # 受注伝票番号を探す
            order_cols = [col for col in df.columns if '受注' in col and '番号' in col]
            
            if order_cols:
                print(f"\n受注伝票番号フィールド: {order_cols}")
                
                for col in order_cols:
                    print(f"\n--- {col} ---")
                    samples = df[col].dropna().head(10).tolist()
                    print(f"サンプルデータ: {samples}")
                    
                    # 0で始まるデータを確認
                    zero_padded = [s for s in samples if str(s).startswith('0') and len(str(s)) > 1]
                    if zero_padded:
                        print(f"0パディング検出: {zero_padded}")
                        
                        # 0を除去した結果を表示
                        cleaned = [str(s).lstrip('0') or '0' for s in zero_padded]
                        print(f"0除去後: {cleaned}")
                    else:
                        print("0パディングは検出されませんでした")
            else:
                print("受注伝票番号フィールドが見つかりません")
                
                # 番号系フィールドを探す
                number_cols = [col for col in df.columns if '番号' in col or 'NO' in col or 'コード' in col]
                if number_cols:
                    print(f"番号系フィールド: {number_cols[:5]}")
                    
                    for col in number_cols[:3]:
                        samples = df[col].dropna().head(5).tolist()
                        zero_padded = [s for s in samples if str(s).startswith('0') and len(str(s)) > 1]
                        if zero_padded:
                            print(f"{col}: 0パディング検出 {zero_padded}")
                
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
    else:
        print("zs58month.txt が見つかりません")
    
    # 2. zp02ファイルとの比較
    print("\n2. zp02ファイルとの比較")
    print("-" * 50)
    
    zp02_path = os.path.join(DATA_DIR, 'zp02.txt')
    
    if os.path.exists(zp02_path):
        try:
            df_zp02 = pd.read_csv(zp02_path, dtype=str, nrows=10, encoding='cp932', sep='\t', engine='python')
            
            order_cols_zp02 = [col for col in df_zp02.columns if '受注' in col and '番号' in col]
            
            if order_cols_zp02:
                for col in order_cols_zp02:
                    samples = df_zp02[col].dropna().head(10).tolist()
                    print(f"zp02.{col}: {samples}")
                    
                    zero_padded = [s for s in samples if str(s).startswith('0') and len(str(s)) > 1]
                    if zero_padded:
                        print(f"  0パディング検出: {zero_padded}")
                    else:
                        print(f"  0パディングなし")
            
        except Exception as e:
            print(f"zp02.txt読み込みエラー: {e}")
    
    # 3. pattern_rules.pyの0パディングルールを確認
    print("\n3. pattern_rules.pyの0パディングルール確認")
    print("-" * 50)
    
    try:
        with open('pattern_rules_data.json', 'r', encoding='utf-8') as f:
            rules_data = pd.read_json(f)
            
        # 0パディングルールを探す
        if 'data_cleaning_rules' in rules_data:
            cleaning_rules = rules_data['data_cleaning_rules']
            if 'zero_padding' in cleaning_rules:
                zero_padding_rule = cleaning_rules['zero_padding']
                print(f"0パディングルール: {zero_padding_rule}")
            else:
                print("0パディングルールが見つかりません")
        else:
            print("data_cleaning_rulesが見つかりません")
            
    except Exception as e:
        print(f"pattern_rules_data.json読み込みエラー: {e}")
    
    # 4. 実際のデータベースでの状況確認
    print("\n4. データベースでの状況確認")
    print("-" * 50)
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # zs58monthテーブルが存在するか確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%zs58%'")
    zs58_tables = cursor.fetchall()
    
    if zs58_tables:
        table_name = zs58_tables[0][0]
        print(f"テーブル発見: {table_name}")
        
        # 受注伝票番号フィールドを探す
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        order_columns = [col[1] for col in columns if '受注' in col[1] and '番号' in col[1]]
        
        if order_columns:
            for col in order_columns:
                cursor.execute(f"SELECT {col} FROM {table_name} WHERE {col} IS NOT NULL LIMIT 10")
                samples = [row[0] for row in cursor.fetchall()]
                print(f"DB.{col}: {samples}")
                
                # 0で始まるデータを確認
                zero_padded = [s for s in samples if str(s).startswith('0') and len(str(s)) > 1]
                if zero_padded:
                    print(f"  DB内0パディング: {zero_padded}")
        else:
            print("受注伝票番号フィールドが見つかりません")
    else:
        print("zs58monthテーブルが見つかりません")
    
    conn.close()

if __name__ == "__main__":
    investigate_zero_padding()