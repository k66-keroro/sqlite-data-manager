#!/usr/bin/env python3
"""
日付が0になる問題を調査
"""

import sqlite3
import pandas as pd
import os
from config import DATA_DIR

def investigate_date_zero_problem():
    """日付が0になる問題を詳細調査"""
    
    print("=== 日付が0になる問題の調査 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 1. 実際のテーブルで0になっているデータを確認
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
    tables = [row[0] for row in cursor.fetchall()]
    
    zero_date_found = False
    
    for table in tables[:5]:  # 最初の5テーブル
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            date_columns = [col[1] for col in columns if col[2] == 'DATETIME']
            
            if date_columns:
                for date_col in date_columns[:2]:
                    try:
                        # 0になっているデータの確認
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {date_col} = '0'")
                        zero_count = cursor.fetchone()[0]
                        
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {date_col} IS NOT NULL")
                        total_count = cursor.fetchone()[0]
                        
                        if zero_count > 0:
                            print(f"\n⚠️  {table}.{date_col}:")
                            print(f"  0になっているデータ: {zero_count}/{total_count}件")
                            zero_date_found = True
                            
                            # 実際の0データのサンプルを確認
                            cursor.execute(f"SELECT * FROM {table} WHERE {date_col} = '0' LIMIT 3")
                            zero_samples = cursor.fetchall()
                            
                            if zero_samples:
                                print(f"  0データのサンプル:")
                                for i, sample in enumerate(zero_samples, 1):
                                    print(f"    {i}. {sample[:5]}...")  # 最初の5列のみ表示
                            
                            # 元ファイルから同じデータを確認
                            original_file = table + '.txt'
                            file_path = os.path.join(DATA_DIR, original_file)
                            
                            if os.path.exists(file_path):
                                print(f"  元ファイル確認: {original_file}")
                                try:
                                    df = pd.read_csv(file_path, dtype=str, nrows=5, encoding='cp932', sep='\t', engine='python')
                                    
                                    # 日付っぽい列を探す
                                    date_like_cols = [col for col in df.columns if '日' in col or 'DATE' in col or '時' in col]
                                    
                                    if date_like_cols:
                                        for col in date_like_cols[:2]:
                                            samples = df[col].dropna().head(3).tolist()
                                            print(f"    {col}: {samples}")
                                            
                                except Exception as e:
                                    print(f"    元ファイル読み込みエラー: {e}")
                            
                    except Exception as e:
                        print(f"    エラー: {table}.{date_col} - {e}")
        except Exception:
            continue
    
    if not zero_date_found:
        print("✅ 0になっている日付データは見つかりませんでした")
    
    # 2. loader.pyの日付変換ロジックを確認
    print("\n=== loader.pyの日付変換ロジック確認 ===")
    
    try:
        with open('loader.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 日付変換部分を探す
        if 'convert_date' in content:
            print("✅ convert_date関数が見つかりました")
            
            # 関数の内容を抽出（簡易版）
            lines = content.split('\n')
            in_convert_date = False
            convert_date_lines = []
            
            for line in lines:
                if 'def convert_date' in line:
                    in_convert_date = True
                    convert_date_lines.append(line)
                elif in_convert_date:
                    if line.startswith('def ') and 'convert_date' not in line:
                        break
                    convert_date_lines.append(line)
            
            print("convert_date関数の内容:")
            for line in convert_date_lines[:20]:  # 最初の20行
                print(f"  {line}")
                
        else:
            print("⚠️  convert_date関数が見つかりません")
            
    except Exception as e:
        print(f"loader.py読み込みエラー: {e}")
    
    conn.close()

if __name__ == "__main__":
    investigate_date_zero_problem()