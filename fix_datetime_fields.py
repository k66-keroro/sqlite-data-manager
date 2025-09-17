#!/usr/bin/env python3
"""
TEXT型のままの日付フィールドを修正するスクリプト
"""

import sqlite3
import pandas as pd
from pattern_rules import TypeCorrectionRules

def fix_datetime_fields():
    """TEXT型のままの日付フィールドを手動でDATETIME型に修正"""
    
    print("=== 日付フィールド修正スクリプト ===")
    
    # データベース接続
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # TEXT型のままの日付フィールドを取得
    cursor.execute("""
        SELECT file_name, column_name, data_type, initial_inferred_type 
        FROM column_master 
        WHERE (column_name LIKE '%日付%' OR column_name LIKE '%DATE%' OR column_name LIKE '%date%')
        AND data_type = 'TEXT'
    """)
    
    text_date_fields = cursor.fetchall()
    print(f"TEXT型のままの日付フィールド: {len(text_date_fields)}件")
    
    # 修正対象フィールドを表示
    for i, (file_name, column_name, data_type, initial_type) in enumerate(text_date_fields, 1):
        print(f"{i:2d}. {file_name}:{column_name} ({data_type})")
    
    if not text_date_fields:
        print("修正対象なし")
        conn.close()
        return
    
    # 一括でDATETIME型に修正
    print(f"\n{len(text_date_fields)}件をDATETIME型に修正します...")
    
    update_count = 0
    for file_name, column_name, _, _ in text_date_fields:
        try:
            cursor.execute("""
                UPDATE column_master 
                SET data_type = 'DATETIME' 
                WHERE file_name = ? AND column_name = ?
            """, (file_name, column_name))
            update_count += 1
            print(f"  ✓ {file_name}:{column_name} -> DATETIME")
        except Exception as e:
            print(f"  ✗ {file_name}:{column_name} -> エラー: {e}")
    
    # 変更をコミット
    conn.commit()
    conn.close()
    
    print(f"\n修正完了: {update_count}/{len(text_date_fields)}件")
    
    # 結果確認
    print("\n=== 修正後の確認 ===")
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COUNT(*) as total, data_type 
        FROM column_master 
        WHERE (column_name LIKE '%日付%' OR column_name LIKE '%DATE%' OR column_name LIKE '%date%')
        GROUP BY data_type
    """)
    
    print("日付フィールドの型分布:")
    for count, data_type in cursor.fetchall():
        print(f"  {data_type}: {count}件")
    
    conn.close()

if __name__ == "__main__":
    fix_datetime_fields()