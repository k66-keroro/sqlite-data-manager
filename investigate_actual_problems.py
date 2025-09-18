#!/usr/bin/env python3
"""
実際の問題を詳細調査
"""

import sqlite3
import pandas as pd
import os
from config import DATA_DIR

def investigate_actual_problems():
    """実際の問題を詳細調査"""
    
    print("=== 実際の問題の詳細調査 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 1. 日付問題の調査
    print("\n1. 日付問題の調査")
    print("-" * 50)
    
    # 実際のテーブルから日付データを確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # 日付フィールドがあるテーブルを探す
    for table in tables[:3]:  # 最初の3テーブル
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            date_columns = [col[1] for col in columns if col[2] == 'DATETIME']
            
            if date_columns:
                print(f"\n--- {table} ---")
                for date_col in date_columns[:2]:
                    try:
                        # 実際のデータサンプルを取得
                        cursor.execute(f"SELECT {date_col} FROM {table} WHERE {date_col} IS NOT NULL AND {date_col} != '0' LIMIT 5")
                        samples = cursor.fetchall()
                        
                        print(f"  {date_col}:")
                        for sample in samples:
                            print(f"    {sample[0]}")
                        
                        # 0になっているデータの数を確認
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {date_col} = '0'")
                        zero_count = cursor.fetchone()[0]
                        
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {date_col} IS NOT NULL")
                        total_count = cursor.fetchone()[0]
                        
                        if zero_count > 0:
                            print(f"    ⚠️  0になっているデータ: {zero_count}/{total_count}件")
                            
                    except Exception as e:
                        print(f"    エラー: {e}")
        except Exception:
            continue
    
    # 2. 0パディング問題の調査
    print("\n2. 0パディング問題の調査")
    print("-" * 50)
    
    # 受注伝票番号のサンプルを確認
    test_files = ['zs58month.txt', 'zp02.txt']
    
    for file_name in test_files:
        file_path = os.path.join(DATA_DIR, file_name)
        if os.path.exists(file_path):
            print(f"\n--- {file_name} ---")
            try:
                # ファイルから直接サンプルを読む
                df = pd.read_csv(file_path, dtype=str, nrows=3, encoding='cp932', sep='\t', engine='python')
                
                # 受注伝票番号を探す
                order_cols = [col for col in df.columns if '受注' in col and '番号' in col]
                
                for col in order_cols:
                    samples = df[col].dropna().head(3).tolist()
                    print(f"  {col}: {samples}")
                    
                    # 0で始まるデータを確認
                    zero_padded = [s for s in samples if s.startswith('0') and len(s) > 1]
                    if zero_padded:
                        print(f"    0パディング検出: {zero_padded}")
                        
            except Exception as e:
                print(f"  読み込みエラー: {e}")
    
    # 3. zs65、払出明細問題の調査
    print("\n3. zs65、払出明細問題の調査")
    print("-" * 50)
    
    problem_files = ['zs65.txt', 'zs65_sss.txt', '払出明細（大阪）_ZPR01201.txt']
    
    for file_name in problem_files:
        print(f"\n--- {file_name} ---")
        
        # column_masterでの型確認
        cursor.execute("""
            SELECT column_name, data_type 
            FROM column_master 
            WHERE file_name = ? AND data_type = 'REAL'
            ORDER BY column_name
        """, (file_name,))
        
        real_fields = cursor.fetchall()
        print(f"  REAL型フィールド: {len(real_fields)}件")
        for col, dtype in real_fields[:3]:
            print(f"    {col} ({dtype})")
        
        # 実際のテーブルが存在するか確認
        table_name = file_name.replace('.txt', '').replace('（', '_').replace('）', '_')
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f"%{table_name[:10]}%",))
        matching_tables = cursor.fetchall()
        
        if matching_tables:
            print(f"  対応テーブル: {[t[0] for t in matching_tables]}")
        else:
            print(f"  ⚠️  対応テーブルが見つかりません")
    
    conn.close()

if __name__ == "__main__":
    investigate_actual_problems()