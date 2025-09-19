#!/usr/bin/env python3
"""
Column Master 拡張・移行ツール
現在のcolumn_masterを拡張して処理種別を追跡可能にする
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple

class ColumnMasterMigrator:
    """Column Master拡張・移行クラス"""
    
    def __init__(self, db_path: str = "output/master.db"):
        self.db_path = db_path
    
    def create_extended_table(self) -> bool:
        """拡張column_masterテーブルを作成"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 拡張テーブル作成
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS column_master_v2 (
                    file_name TEXT,
                    column_name TEXT,
                    
                    -- 推論結果
                    initial_inferred_type TEXT,
                    
                    -- ルール適用結果
                    rule_applied_type TEXT,
                    applied_rule_name TEXT,
                    
                    -- 個別マッピング結果
                    manual_override_type TEXT,
                    override_reason TEXT,
                    
                    -- 最終決定型
                    final_data_type TEXT,
                    decision_source TEXT,  -- 'inference', 'rule', 'manual'
                    
                    -- メタデータ
                    encoding TEXT,
                    delimiter TEXT,
                    last_updated DATETIME,
                    
                    PRIMARY KEY (file_name, column_name)
                )
            """)
            
            conn.commit()
            conn.close()
            print("拡張column_master_v2テーブル作成完了")
            return True
            
        except Exception as e:
            print(f"テーブル作成エラー: {e}")
            return False
    
    def analyze_current_data(self) -> Dict[str, List[Tuple]]:
        """現在のデータを分析して処理種別を推定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT file_name, column_name, data_type, initial_inferred_type, encoding, delimiter
                FROM column_master
            """)
            
            all_data = cursor.fetchall()
            
            analysis = {
                'inference_only': [],      # 推論のみ
                'rule_applied': [],        # ルール適用
                'manual_override': []      # 個別マッピング
            }
            
            for row in all_data:
                file_name, column_name, data_type, initial_type, encoding, delimiter = row
                
                if data_type == initial_type:
                    # 推論のみで決定
                    analysis['inference_only'].append(row)
                elif self._is_rule_based_change(column_name, data_type, initial_type):
                    # ルールベースの変更
                    analysis['rule_applied'].append(row)
                else:
                    # 個別マッピング
                    analysis['manual_override'].append(row)
            
            return analysis
            
        finally:
            conn.close()
    
    def _is_rule_based_change(self, column_name: str, data_type: str, initial_type: str) -> bool:
        """ルールベースの変更かどうかを判定"""
        # コード系フィールドのTEXT化
        if ('コード' in column_name or '保管場所' in column_name) and data_type == 'TEXT':
            return True
        
        # 日付系フィールドのDATETIME化
        if ('日付' in column_name or '日時' in column_name) and data_type == 'DATETIME':
            return True
        
        # 0パディング対応のTEXT化
        if data_type == 'TEXT' and initial_type in ['INTEGER', 'REAL']:
            return True
        
        return False
    
    def _get_rule_name(self, column_name: str, data_type: str, initial_type: str) -> str:
        """適用されたルール名を推定"""
        if 'コード' in column_name:
            return 'sap_code_fields'
        elif '保管場所' in column_name:
            return 'storage_location_text'
        elif '日付' in column_name or '日時' in column_name:
            return 'datetime_fields'
        elif data_type == 'TEXT' and initial_type in ['INTEGER', 'REAL']:
            return 'zero_padding_protection'
        else:
            return 'unknown_rule'
    
    def migrate_data(self) -> bool:
        """既存データを拡張テーブルに移行"""
        try:
            analysis = self.analyze_current_data()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            current_time = datetime.now().isoformat()
            
            # 推論のみのデータ
            for row in analysis['inference_only']:
                file_name, column_name, data_type, initial_type, encoding, delimiter = row
                cursor.execute("""
                    INSERT OR REPLACE INTO column_master_v2 
                    (file_name, column_name, initial_inferred_type, final_data_type, 
                     decision_source, encoding, delimiter, last_updated)
                    VALUES (?, ?, ?, ?, 'inference', ?, ?, ?)
                """, (file_name, column_name, initial_type, data_type, encoding, delimiter, current_time))
            
            # ルール適用データ
            for row in analysis['rule_applied']:
                file_name, column_name, data_type, initial_type, encoding, delimiter = row
                rule_name = self._get_rule_name(column_name, data_type, initial_type)
                cursor.execute("""
                    INSERT OR REPLACE INTO column_master_v2 
                    (file_name, column_name, initial_inferred_type, rule_applied_type, 
                     applied_rule_name, final_data_type, decision_source, encoding, delimiter, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, 'rule', ?, ?, ?)
                """, (file_name, column_name, initial_type, data_type, rule_name, data_type, encoding, delimiter, current_time))
            
            # 個別マッピングデータ
            for row in analysis['manual_override']:
                file_name, column_name, data_type, initial_type, encoding, delimiter = row
                cursor.execute("""
                    INSERT OR REPLACE INTO column_master_v2 
                    (file_name, column_name, initial_inferred_type, manual_override_type, 
                     override_reason, final_data_type, decision_source, encoding, delimiter, last_updated)
                    VALUES (?, ?, ?, ?, '個別マッピング', ?, 'manual', ?, ?, ?)
                """, (file_name, column_name, initial_type, data_type, data_type, encoding, delimiter, current_time))
            
            conn.commit()
            conn.close()
            
            print("データ移行完了")
            print(f"推論のみ: {len(analysis['inference_only'])}件")
            print(f"ルール適用: {len(analysis['rule_applied'])}件")
            print(f"個別マッピング: {len(analysis['manual_override'])}件")
            
            return True
            
        except Exception as e:
            print(f"データ移行エラー: {e}")
            return False
    
    def generate_report(self) -> None:
        """移行結果レポートを生成"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 処理種別サマリー
            cursor.execute("""
                SELECT decision_source, COUNT(*) as count
                FROM column_master_v2
                GROUP BY decision_source
            """)
            
            print("\n=== 処理種別サマリー ===")
            for row in cursor.fetchall():
                source, count = row
                print(f"{source}: {count}件")
            
            # ルール別サマリー
            cursor.execute("""
                SELECT applied_rule_name, COUNT(*) as count
                FROM column_master_v2
                WHERE decision_source = 'rule'
                GROUP BY applied_rule_name
            """)
            
            print("\n=== ルール別サマリー ===")
            for row in cursor.fetchall():
                rule_name, count = row
                print(f"{rule_name}: {count}件")
            
            # 個別マッピングが多いファイル
            cursor.execute("""
                SELECT file_name, COUNT(*) as manual_count
                FROM column_master_v2
                WHERE decision_source = 'manual'
                GROUP BY file_name
                ORDER BY manual_count DESC
                LIMIT 10
            """)
            
            print("\n=== 個別マッピングが多いファイル ===")
            for row in cursor.fetchall():
                file_name, count = row
                print(f"{file_name}: {count}件")
                
        finally:
            conn.close()

def main():
    """メイン実行"""
    migrator = ColumnMasterMigrator()
    
    print("Column Master 拡張・移行開始")
    
    # 1. 拡張テーブル作成
    if not migrator.create_extended_table():
        return
    
    # 2. データ移行
    if not migrator.migrate_data():
        return
    
    # 3. レポート生成
    migrator.generate_report()
    
    print("\nColumn Master 拡張・移行完了")

if __name__ == "__main__":
    main()