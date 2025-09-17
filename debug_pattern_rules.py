#!/usr/bin/env python3
"""
パターンルールのデバッグ用スクリプト
日付フィールドがなぜTEXT型になっているかを調査
"""

import sqlite3
import pandas as pd
from pattern_rules import TypeCorrectionRules

def debug_datetime_detection():
    """日付検出の問題を調査"""
    
    print("=== パターンルール デバッグ ===")
    
    # TypeCorrectionRulesのインスタンス作成
    corrector = TypeCorrectionRules()
    
    # column_masterから日付関連でTEXT型になっているフィールドを取得
    conn = sqlite3.connect('output/master.db')
    
    query = """
    SELECT file_name, column_name, data_type, initial_inferred_type 
    FROM column_master 
    WHERE (column_name LIKE '%日付%' OR column_name LIKE '%DATE%' OR column_name LIKE '%date%')
    AND data_type = 'TEXT'
    LIMIT 5
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"TEXT型になっている日付フィールド: {len(df)}件")
    print(df.to_string())
    
    # 各フィールドについて、パターンルールを手動テスト
    for _, row in df.iterrows():
        file_name = row['file_name']
        column_name = row['column_name']
        
        print(f"\n--- {file_name}:{column_name} のテスト ---")
        
        # サンプルデータを作成（実際のデータがないので仮想データで）
        sample_dates = [
            "20240101", "20240202", "20240303",  # YYYYMMDD形式
            "2024/01/01", "2024/02/02", "2024/03/03",  # YYYY/MM/DD形式
            "2024-01-01", "2024-02-02", "2024-03-03",  # YYYY-MM-DD形式
        ]
        
        # パターンルールを適用
        result = corrector.correct_type(file_name, column_name, sample_dates, "TEXT")
        print(f"パターンルール結果: {result}")
        
        # 個別メソッドもテスト
        datetime_result = corrector.enhance_datetime_detection(sample_dates, column_name)
        print(f"DATETIME検出結果: {datetime_result}")
        
        # 日付パターンマッチングをテスト
        patterns = corrector._rules_data['datetime_patterns']
        print(f"設定されている日付パターン: {patterns}")
        
        for sample in sample_dates[:3]:
            for pattern in patterns:
                import re
                if re.match(pattern, sample):
                    print(f"  {sample} -> パターン {pattern} にマッチ")
                    break
            else:
                print(f"  {sample} -> どのパターンにもマッチしない")

if __name__ == "__main__":
    debug_datetime_detection()