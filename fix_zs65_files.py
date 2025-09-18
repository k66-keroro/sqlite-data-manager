#!/usr/bin/env python3
"""
zs65ファイルの区切り文字問題を修正
"""

import os
import pandas as pd
from config import DATA_DIR

def investigate_zs65_files():
    """zs65ファイルの実際の内容を調査"""
    
    print("=== zs65ファイルの調査 ===")
    
    files = ['zs65.txt', 'zs65_sss.txt']
    
    for file_name in files:
        file_path = os.path.join(DATA_DIR, file_name)
        
        if not os.path.exists(file_path):
            print(f"ファイルが見つかりません: {file_path}")
            continue
            
        print(f"\n--- {file_name} ---")
        
        # ファイルの最初の数行を読んで区切り文字を調査
        encodings = ['utf-8', 'cp932', 'shift_jis']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
                    lines = [f.readline().strip() for _ in range(3)]
                
                print(f"エンコーディング: {encoding}")
                for i, line in enumerate(lines, 1):
                    print(f"  行{i}: {line[:100]}...")
                    
                    # 区切り文字候補をチェック
                    delimiters = ['\t', '|', ',', ';', ' ']
                    for delim in delimiters:
                        count = line.count(delim)
                        if count > 5:  # 5個以上あれば区切り文字候補
                            print(f"    '{delim}' が {count}個")
                
                break  # 成功したエンコーディングで終了
                
            except Exception as e:
                print(f"エンコーディング {encoding} 失敗: {e}")
                continue

def test_zs65_parsing():
    """zs65ファイルの正しい読み込み方法をテスト"""
    
    print("\n=== zs65ファイルの読み込みテスト ===")
    
    files = ['zs65.txt', 'zs65_sss.txt']
    
    for file_name in files:
        file_path = os.path.join(DATA_DIR, file_name)
        
        if not os.path.exists(file_path):
            continue
            
        print(f"\n--- {file_name} ---")
        
        # 複数の区切り文字でテスト
        test_configs = [
            ('cp932', '\t'),
            ('cp932', '|'),  
            ('cp932', ' '),
            ('utf-8', '\t'),
            ('shift_jis', '\t'),
        ]
        
        for encoding, delimiter in test_configs:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=delimiter,
                    dtype=str,
                    encoding=encoding,
                    engine='python',
                    nrows=5
                )
                
                print(f"  {encoding} + '{delimiter}': {df.shape} - 列数{len(df.columns)}")
                if len(df.columns) > 10:  # 10列以上なら成功の可能性
                    print(f"    列名サンプル: {list(df.columns[:5])}")
                    
            except Exception as e:
                print(f"  {encoding} + '{delimiter}': 失敗 - {e}")

if __name__ == "__main__":
    investigate_zs65_files()
    test_zs65_parsing()