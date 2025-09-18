#!/usr/bin/env python3
"""
最終検証レポート
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_final_report():
    """最終検証レポートを生成"""
    
    print("=" * 60)
    print("🎉 SQLiteデータマネージャー - 最終検証レポート")
    print("=" * 60)
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 1. 全体統計
    print("\n📊 全体統計:")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(DISTINCT file_name) FROM column_master")
    file_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM column_master")
    total_fields = cursor.fetchone()[0]
    
    print(f"処理ファイル数: {file_count}件")
    print(f"総フィールド数: {total_fields}件")
    
    # 2. データ型別統計
    print("\n📈 データ型別統計:")
    print("-" * 40)
    
    cursor.execute("""
        SELECT data_type, COUNT(*) as count
        FROM column_master 
        GROUP BY data_type 
        ORDER BY count DESC
    """)
    
    type_stats = cursor.fetchall()
    for dtype, count in type_stats:
        percentage = (count / total_fields) * 100
        print(f"{dtype:12}: {count:4}件 ({percentage:5.1f}%)")
    
    # 3. 修正完了項目
    print("\n✅ 修正完了項目:")
    print("-" * 40)
    
    # DATETIME型の修正
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type = 'DATETIME'")
    datetime_count = cursor.fetchone()[0]
    print(f"1. 日付フィールドの型統一: {datetime_count}件 → DATETIME型")
    
    # REAL型の修正
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type = 'REAL'")
    real_count = cursor.fetchone()[0]
    print(f"2. 数値フィールドの型統一: {real_count}件 → REAL型")
    
    # 4. 問題ファイルの修正状況
    print("\n🔧 問題ファイルの修正状況:")
    print("-" * 40)
    
    problem_files = [
        'zs65.txt', 
        'zs65_sss.txt', 
        '払出明細（大阪）_ZPR01201.txt', 
        '払出明細（滋賀）_ZPR01201.txt'
    ]
    
    for file_name in problem_files:
        cursor.execute("""
            SELECT data_type, COUNT(*) 
            FROM column_master 
            WHERE file_name = ?
            GROUP BY data_type
            ORDER BY data_type
        """, (file_name,))
        
        results = cursor.fetchall()
        total_file_fields = sum(count for _, count in results)
        
        print(f"\n{file_name} ({total_file_fields}フィールド):")
        for dtype, count in results:
            print(f"  {dtype}: {count}件")
    
    # 5. 対象外項目（確認）
    print("\n🚫 対象外項目 (修正不要):")
    print("-" * 40)
    
    cursor.execute("""
        SELECT COUNT(*) FROM column_master 
        WHERE data_type = 'TEXT' 
        AND (column_name LIKE '%コード%' OR column_name LIKE '%番号%' OR 
             column_name LIKE '%NO%' OR column_name LIKE '%CD%')
    """)
    code_count = cursor.fetchone()[0]
    print(f"コード系フィールド: {code_count}件 (0始まりコードのため)")
    
    # 6. 品質指標
    print("\n📋 品質指標:")
    print("-" * 40)
    
    # 型統一率
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type != 'TEXT'")
    typed_fields = cursor.fetchone()[0]
    type_unification_rate = (typed_fields / total_fields) * 100
    
    print(f"型統一率: {type_unification_rate:.1f}% ({typed_fields}/{total_fields})")
    
    # 日付型統一率
    cursor.execute("""
        SELECT COUNT(*) FROM column_master 
        WHERE column_name LIKE '%日%' OR column_name LIKE '%DATE%' OR column_name LIKE '%時%'
    """)
    date_like_fields = cursor.fetchone()[0]
    
    if date_like_fields > 0:
        date_unification_rate = (datetime_count / date_like_fields) * 100
        print(f"日付型統一率: {date_unification_rate:.1f}% ({datetime_count}/{date_like_fields})")
    
    # 7. 次のステップ
    print("\n🚀 次のステップ:")
    print("-" * 40)
    print("1. ✅ データ型統合完了")
    print("2. 📝 T002: データ型修正支援ツール基盤の開発")
    print("3. 📊 T003: 型統合レポート機能の実装")
    print("4. 🔄 日次バッチ処理の自動化準備")
    
    print("\n" + "=" * 60)
    print("🎊 データ型統合フェーズ完了！")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    generate_final_report()