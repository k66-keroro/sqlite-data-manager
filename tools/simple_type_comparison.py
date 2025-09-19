#!/usr/bin/env python3
"""
シンプルな型比較チェック
"""

import sqlite3

def simple_type_comparison():
    """シンプルな型比較"""
    
    print("=== column_master vs 実テーブル 型比較 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    try:
        # サンプルテーブルで比較
        test_tables = ['zs45', 'zs65', 'KANSEI_JISSEKI']
        
        for table in test_tables:
            try:
                print(f"\n--- {table} ---")
                
                # 実テーブルの構造
                cursor.execute(f"PRAGMA table_info({table})")
                actual_columns = cursor.fetchall()
                
                if not actual_columns:
                    print(f"  テーブル {table} が見つかりません")
                    continue
                
                print(f"  実テーブル構造 ({len(actual_columns)}カラム):")
                for col_info in actual_columns[:5]:  # 最初の5カラム
                    col_name, col_type = col_info[1], col_info[2]
                    print(f"    {col_name}: {col_type}")
                
                # column_masterの情報
                file_name = f"{table}.txt"
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM column_master 
                    WHERE file_name = ?
                    LIMIT 5
                """, (file_name,))
                
                master_info = cursor.fetchall()
                
                if master_info:
                    print(f"  column_master情報 ({len(master_info)}カラム):")
                    for col_name, data_type in master_info:
                        print(f"    {col_name}: {data_type}")
                else:
                    print(f"  column_masterに {file_name} の情報がありません")
                
                # 不整合チェック
                actual_dict = {row[1]: row[2] for row in actual_columns}
                master_dict = {row[0]: row[1] for row in master_info}
                
                inconsistencies = 0
                for col_name in list(actual_dict.keys())[:5]:  # 最初の5カラムのみ
                    actual_type = actual_dict[col_name]
                    master_type = master_dict.get(col_name, "未登録")
                    
                    if master_type != "未登録" and actual_type != master_type:
                        print(f"    ❌ 不整合: {col_name} - 実={actual_type}, master={master_type}")
                        inconsistencies += 1
                
                if inconsistencies == 0:
                    print(f"  ✅ 型整合性: OK")
                else:
                    print(f"  ⚠️  型不整合: {inconsistencies}件")
                
            except Exception as e:
                print(f"  エラー: {e}")
                continue
    
    finally:
        conn.close()

if __name__ == "__main__":
    simple_type_comparison()