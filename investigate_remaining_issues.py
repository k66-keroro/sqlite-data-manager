#!/usr/bin/env python3
"""
残っている問題の詳細調査
"""

import sqlite3
import pandas as pd
import re

def investigate_issues():
    """残っている問題を詳細調査"""
    
    print("=== 残っている問題の詳細調査 ===")
    
    conn = sqlite3.connect('output/master.db')
    
    # 1. 0パディング問題の調査
    print("\n1. 0パディング問題の調査")
    print("-" * 40)
    
    # 0で始まる数値っぽいフィールドを探す
    cursor = conn.cursor()
    cursor.execute("""
        SELECT file_name, column_name, data_type, initial_inferred_type
        FROM column_master 
        WHERE data_type = 'TEXT' 
        AND (column_name LIKE '%コード%' OR column_name LIKE '%番号%' OR column_name LIKE '%NO%' OR column_name LIKE '%CD%')
        ORDER BY file_name, column_name
    """)
    
    code_fields = cursor.fetchall()
    print(f"コード系フィールド（TEXT型）: {len(code_fields)}件")
    
    for i, (file_name, column_name, data_type, initial_type) in enumerate(code_fields[:10], 1):
        print(f"{i:2d}. {file_name}:{column_name} ({data_type})")
    
    if len(code_fields) > 10:
        print(f"    ... 他{len(code_fields)-10}件")
    
    # 2. 未登録ファイルの詳細調査
    print("\n2. 未登録ファイルの詳細調査")
    print("-" * 40)
    
    problem_files = ['zs65.txt', 'zs65_sss.txt', '払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt']
    
    for file_name in problem_files:
        print(f"\n--- {file_name} ---")
        cursor.execute("""
            SELECT column_name, data_type, initial_inferred_type
            FROM column_master 
            WHERE file_name = ?
            ORDER BY column_name
        """, (file_name,))
        
        fields = cursor.fetchall()
        
        # 型別集計
        type_counts = {}
        for _, data_type, _ in fields:
            type_counts[data_type] = type_counts.get(data_type, 0) + 1
        
        print(f"  総フィールド数: {len(fields)}")
        for dtype, count in type_counts.items():
            print(f"  {dtype}: {count}件")
        
        # 数値っぽいフィールドでTEXT型になっているものを表示
        numeric_text_fields = [
            (col, dtype, initial) for col, dtype, initial in fields 
            if dtype == 'TEXT' and (
                '数量' in col or '金額' in col or '単価' in col or '原価' in col or
                '重量' in col or 'QTY' in col or 'AMOUNT' in col or 'PRICE' in col or
                re.search(r'\d', col)  # 数字を含む列名
            )
        ]
        
        if numeric_text_fields:
            print(f"  数値っぽいのにTEXT型: {len(numeric_text_fields)}件")
            for col, dtype, initial in numeric_text_fields[:5]:
                print(f"    {col} ({dtype})")
    
    # 3. 日付フォーマット問題の調査
    print("\n3. 日付フォーマット問題の調査")
    print("-" * 40)
    
    # 実際のテーブルから日付データのサンプルを取得
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
    tables = [row[0] for row in cursor.fetchall()]
    
    date_samples = []
    for table in tables[:5]:  # 最初の5テーブルをチェック
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            date_columns = [col[1] for col in columns if col[2] == 'DATETIME']
            
            if date_columns:
                for date_col in date_columns[:2]:  # 各テーブル最大2列
                    try:
                        cursor.execute(f"SELECT {date_col} FROM {table} WHERE {date_col} IS NOT NULL LIMIT 3")
                        samples = cursor.fetchall()
                        if samples:
                            date_samples.append((table, date_col, [row[0] for row in samples]))
                    except Exception as e:
                        print(f"    エラー: {table}.{date_col} - {e}")
        except Exception:
            continue
    
    print("日付データのサンプル:")
    for table, col, samples in date_samples:
        print(f"  {table}.{col}:")
        for sample in samples:
            print(f"    {sample}")
    
    conn.close()

if __name__ == "__main__":
    investigate_issues()