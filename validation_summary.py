#!/usr/bin/env python3
"""
検証結果の最終まとめ
"""

import sqlite3
import pandas as pd

def final_validation_summary():
    """検証結果の最終まとめ"""
    
    print("=== 検証結果の最終まとめ ===")
    
    conn = sqlite3.connect('output/master.db')
    
    # 1. 修正済み項目の確認
    print("\n✅ 修正済み項目:")
    print("-" * 40)
    
    # DATETIME型の確認
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type = 'DATETIME'")
    datetime_count = cursor.fetchone()[0]
    print(f"1. DATETIME型フィールド: {datetime_count}件 (修正済み)")
    
    # 2. 残存する問題の整理
    print("\n⚠️  残存する問題:")
    print("-" * 40)
    
    # zs65ファイル系の数値フィールド
    problem_files = ['zs65.txt', 'zs65_sss.txt']
    for file_name in problem_files:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM column_master 
            WHERE file_name = ? AND data_type = 'TEXT'
            AND (column_name LIKE '%数量%' OR column_name LIKE '%在庫%' OR 
                 column_name LIKE '%値%' OR column_name LIKE '%金額%')
            ORDER BY column_name
        """, (file_name,))
        
        numeric_fields = cursor.fetchall()
        if numeric_fields:
            print(f"\n{file_name} - 数値系フィールド (TEXT型): {len(numeric_fields)}件")
            for col, dtype in numeric_fields:
                print(f"  - {col}")
    
    # 払出明細ファイルの数量フィールド
    payout_files = ['払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt']
    for file_name in payout_files:
        cursor.execute("""
            SELECT column_name, data_type 
            FROM column_master 
            WHERE file_name = ? AND data_type = 'TEXT'
            AND column_name LIKE '%数量%'
            ORDER BY column_name
        """, (file_name,))
        
        quantity_fields = cursor.fetchall()
        if quantity_fields:
            print(f"\n{file_name} - 数量フィールド (TEXT型): {len(quantity_fields)}件")
            for col, dtype in quantity_fields:
                print(f"  - {col}")
    
    # 3. 対象外項目の確認
    print("\n🚫 対象外項目 (修正不要):")
    print("-" * 40)
    
    # コード系フィールド（0始まりコードのため対象外）
    cursor.execute("""
        SELECT COUNT(*) FROM column_master 
        WHERE data_type = 'TEXT' 
        AND (column_name LIKE '%コード%' OR column_name LIKE '%番号%' OR 
             column_name LIKE '%NO%' OR column_name LIKE '%CD%')
    """)
    code_count = cursor.fetchone()[0]
    print(f"1. コード系フィールド: {code_count}件 (0始まりコードのため対象外)")
    
    # 4. 修正推奨項目の特定
    print("\n🔧 修正推奨項目:")
    print("-" * 40)
    
    # 実際に修正すべき数値フィールドの集計
    cursor.execute("""
        SELECT file_name, COUNT(*) as count
        FROM column_master 
        WHERE data_type = 'TEXT'
        AND (column_name LIKE '%数量%' OR column_name LIKE '%在庫%' OR 
             column_name LIKE '%値%' OR column_name LIKE '%金額%')
        AND file_name IN ('zs65.txt', 'zs65_sss.txt', 
                         '払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt')
        GROUP BY file_name
        ORDER BY count DESC
    """)
    
    fix_candidates = cursor.fetchall()
    total_fix_needed = sum(count for _, count in fix_candidates)
    
    print(f"修正対象フィールド総数: {total_fix_needed}件")
    for file_name, count in fix_candidates:
        print(f"  - {file_name}: {count}件")
    
    # 5. 次のアクション
    print("\n📋 次のアクション:")
    print("-" * 40)
    print("1. zs65系ファイルの数値フィールドをREAL型に修正")
    print("2. 払出明細ファイルの数量フィールドをREAL型に修正")
    print("3. 修正後の検証テスト実行")
    
    conn.close()

if __name__ == "__main__":
    final_validation_summary()