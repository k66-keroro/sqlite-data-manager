#!/usr/bin/env python3
"""
column_masterと実テーブルのデータ型比較チェック
"""

import sqlite3
from t007_verification_system import VerificationSystem
from t002_data_structures import ModificationBatch, FieldModification, FieldType, ModificationAction, ConfidenceLevel

def check_table_type_consistency():
    """column_masterと実テーブルの型整合性をチェック"""
    
    print("=== column_master vs 実テーブル 型整合性チェック ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    try:
        # 全テーブルの型比較
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
        tables = [row[0] for row in cursor.fetchall()]
        
        inconsistencies = []
        
        for table in tables[:10]:  # 最初の10テーブルをチェック
            try:
                print(f"\n--- {table} ---")
                
                # 実テーブルの構造を取得
                cursor.execute(f"PRAGMA table_info({table})")
                actual_columns = {row[1]: row[2] for row in cursor.fetchall()}
                
                # column_masterの情報を取得
                file_name = f"{table}.txt"
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM column_master 
                    WHERE file_name = ?
                """, (file_name,))
                
                master_columns = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 比較
                for col_name in actual_columns:
                    actual_type = actual_columns[col_name]
                    master_type = master_columns.get(col_name, "未登録")
                    
                    if master_type != "未登録":
                        # 型の互換性チェック
                        compatible = types_compatible(actual_type, master_type)
                        
                        if not compatible:
                            inconsistency = {
                                "table": table,
                                "column": col_name,
                                "actual_type": actual_type,
                                "master_type": master_type
                            }
                            inconsistencies.append(inconsistency)
                            print(f"  ❌ {col_name}: 実テーブル={actual_type}, column_master={master_type}")
                        else:
                            print(f"  ✅ {col_name}: {actual_type} ≈ {master_type}")
                    else:
                        print(f"  ⚠️  {col_name}: column_masterに未登録")
                
            except Exception as e:
                print(f"  エラー: {e}")
                continue
        
        # 結果サマリー
        print(f"\n=== 結果サマリー ===")
        print(f"チェック対象テーブル: {min(len(tables), 10)}件")
        print(f"型不整合: {len(inconsistencies)}件")
        
        if inconsistencies:
            print("\n型不整合の詳細:")
            for inc in inconsistencies:
                print(f"  - {inc['table']}.{inc['column']}: {inc['actual_type']} vs {inc['master_type']}")
        
        return inconsistencies
        
    finally:
        conn.close()

def types_compatible(actual_type: str, expected_type: str) -> bool:
    """SQLite型の互換性チェック"""
    # SQLiteの型アフィニティを考慮
    type_mapping = {
        "TEXT": ["TEXT", "VARCHAR", "CHAR"],
        "INTEGER": ["INTEGER", "INT", "BIGINT"],
        "REAL": ["REAL", "FLOAT", "DOUBLE", "NUMERIC"],
        "DATETIME": ["DATETIME", "TIMESTAMP", "DATE"]
    }
    
    for canonical_type, variants in type_mapping.items():
        if expected_type == canonical_type:
            return actual_type.upper() in [v.upper() for v in variants]
    
    return actual_type.upper() == expected_type.upper()

def generate_type_comparison_report():
    """型比較レポートを生成"""
    
    print("\n=== 型比較レポート生成 ===")
    
    # 検証システムを使用
    verification_system = VerificationSystem("output/master.db")
    
    # ダミーバッチを作成（全フィールドをチェック用）
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT file_name, column_name, data_type FROM column_master LIMIT 50")
    fields = cursor.fetchall()
    
    modifications = []
    for file_name, column_name, data_type in fields:
        modification = FieldModification(
            file_name=file_name,
            column_name=column_name,
            current_type=FieldType(data_type),
            target_type=FieldType(data_type),  # 同じ型（チェック用）
            action=ModificationAction.TYPE_CHANGE,
            confidence=ConfidenceLevel.HIGH,
            reason="型整合性チェック用"
        )
        modifications.append(modification)
    
    batch = ModificationBatch(
        batch_id="type_check_001",
        name="型整合性チェック",
        description="column_masterと実テーブルの型比較",
        modifications=modifications
    )
    
    # 検証実行
    report = verification_system.verify_modification_batch(batch)
    
    # 型整合性チェック結果を表示
    for check in report.integrity_checks:
        if check.check_name == "column_type_consistency":
            print(f"型整合性チェック: {'✅ 正常' if check.passed else '❌ 問題あり'}")
            print(f"メッセージ: {check.message}")
            
            if not check.passed and 'inconsistencies' in check.details:
                print("不整合の詳細:")
                for inc in check.details['inconsistencies'][:5]:
                    print(f"  - {inc}")
    
    conn.close()
    return report

if __name__ == "__main__":
    # 直接比較
    inconsistencies = check_table_type_consistency()
    
    # 検証システムを使った比較
    report = generate_type_comparison_report()
    
    print(f"\n=== 最終結果 ===")
    print(f"型不整合件数: {len(inconsistencies)}件")
    print(f"検証システム結果: {report.overall_status}")