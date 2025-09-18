#!/usr/bin/env python3
"""
zs65ファイルの正確な列名を確認
"""

import pandas as pd
import os
from config import DATA_DIR

def check_zs65_columns():
    """zs65ファイルの正確な列名を確認"""
    
    print("=== zs65ファイルの列名確認 ===")
    
    files = ['zs65.txt', 'zs65_sss.txt']
    
    for file_name in files:
        file_path = os.path.join(DATA_DIR, file_name)
        
        if os.path.exists(file_path):
            print(f"\n--- {file_name} ---")
            try:
                # cp932エンコーディングでタブ区切りで読み込み
                df = pd.read_csv(
                    file_path, 
                    sep='\t', 
                    dtype=str, 
                    nrows=0,  # ヘッダーのみ
                    encoding='cp932', 
                    engine='python'
                )
                
                print(f"列数: {len(df.columns)}")
                print("列名一覧:")
                for i, col in enumerate(df.columns, 1):
                    print(f"{i:2d}. {col}")
                    
                # 数値っぽい列を特定
                numeric_candidates = []
                for col in df.columns:
                    if any(keyword in col for keyword in ['在庫', '値', '金額', '数量', '評価']):
                        numeric_candidates.append(col)
                
                print(f"\n数値候補フィールド ({len(numeric_candidates)}件):")
                for col in numeric_candidates:
                    print(f"  - {col}")
                    
            except Exception as e:
                print(f"エラー: {e}")
        else:
            print(f"{file_name} が見つかりません")

if __name__ == "__main__":
    check_zs65_columns()