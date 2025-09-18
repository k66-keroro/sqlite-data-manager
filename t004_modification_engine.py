#!/usr/bin/env python3
"""
T004: 型修正エンジンの開発
"""

import sqlite3
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from t002_data_structures import (
    FieldModification, ModificationBatch, ModificationAction, 
    FieldType, ConfidenceLevel
)
from t002_backup_system import BackupManager

class ModificationEngine:
    """型修正エンジン"""
    
    def __init__(self, db_path: str, backup_manager: BackupManager = None):
        self.db_path = db_path
        self.backup_manager = backup_manager or BackupManager()
        self.modification_history: List[Dict] = []
        self.rollback_points: List[Dict] = []
    
    def execute_batch(self, batch: ModificationBatch) -> Dict[str, Any]:
        """修正バッチを実行"""
        print(f"=== バッチ実行開始: {batch.name} ===")
        
        # バックアップ作成
        backup_info = self.backup_manager.create_backup(
            self.db_path, batch, f"Batch execution backup: {batch.name}"
        )
        
        if not backup_info:
            return {
                "success": False,
                "error": "バックアップ作成に失敗",
                "executed_modifications": 0
            }
        
        batch.backup_path = backup_info.backup_path
        batch.status = "in_progress"
        
        conn = sqlite3.connect(self.db_path)
        executed_count = 0
        failed_count = 0
        execution_log = []
        
        try:
            # ロールバックポイント作成
            rollback_point = self._create_rollback_point(batch.batch_id)
            
            for modification in batch.modifications:
                try:
                    result = self._execute_single_modification(conn, modification)
                    if result["success"]:
                        executed_count += 1
                        execution_log.append(f"✅ {modification.file_name}.{modification.column_name}: {result['message']}")
                    else:
                        failed_count += 1
                        execution_log.append(f"❌ {modification.file_name}.{modification.column_name}: {result['error']}")
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f"実行エラー: {str(e)}"
                    execution_log.append(f"❌ {modification.file_name}.{modification.column_name}: {error_msg}")
            
            conn.commit()
            batch.status = "completed" if failed_count == 0 else "partial_success"
            batch.execution_log = execution_log
            
            # 修正履歴に記録
            self._record_modification_history(batch, executed_count, failed_count)
            
            print(f"バッチ実行完了: 成功{executed_count}件, 失敗{failed_count}件")
            
            return {
                "success": True,
                "executed_modifications": executed_count,
                "failed_modifications": failed_count,
                "backup_path": backup_info.backup_path,
                "execution_log": execution_log
            }
            
        except Exception as e:
            conn.rollback()
            batch.status = "failed"
            error_msg = f"バッチ実行エラー: {str(e)}"
            batch.execution_log = [error_msg]
            
            print(f"バッチ実行失敗: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "executed_modifications": executed_count,
                "backup_path": backup_info.backup_path
            }
            
        finally:
            conn.close()
    
    def _execute_single_modification(self, conn: sqlite3.Connection, 
                                   modification: FieldModification) -> Dict[str, Any]:
        """単一の修正を実行"""
        cursor = conn.cursor()
        
        try:
            if modification.action == ModificationAction.TYPE_CHANGE:
                return self._execute_type_change(cursor, modification)
            elif modification.action == ModificationAction.ZERO_PADDING_REMOVE:
                return self._execute_zero_padding_removal(cursor, modification)
            elif modification.action == ModificationAction.TRAILING_MINUS_FIX:
                return self._execute_trailing_minus_fix(cursor, modification)
            elif modification.action == ModificationAction.DATE_FORMAT_FIX:
                return self._execute_date_format_fix(cursor, modification)
            elif modification.action == ModificationAction.DECIMAL_COMMA_FIX:
                return self._execute_decimal_comma_fix(cursor, modification)
            else:
                return {
                    "success": False,
                    "error": f"未対応のアクション: {modification.action}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"修正実行エラー: {str(e)}"
            }
    
    def _execute_type_change(self, cursor: sqlite3.Cursor, 
                           modification: FieldModification) -> Dict[str, Any]:
        """型変更を実行"""
        try:
            # column_masterの型を更新
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (modification.target_type.value, modification.file_name, modification.column_name))
            
            affected_rows = cursor.rowcount
            
            if affected_rows > 0:
                return {
                    "success": True,
                    "message": f"型変更完了 {modification.current_type.value} → {modification.target_type.value}",
                    "affected_rows": affected_rows
                }
            else:
                return {
                    "success": False,
                    "error": "対象フィールドが見つかりません"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"型変更エラー: {str(e)}"
            }
    
    def _execute_zero_padding_removal(self, cursor: sqlite3.Cursor, 
                                    modification: FieldModification) -> Dict[str, Any]:
        """0パディング除去を実行"""
        try:
            # 実際のテーブル名を取得
            table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
            
            # テーブルが存在するか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"テーブルが見つかりません: {table_name}"
                }
            
            # 0パディングデータを更新
            zero_padding_pattern = r'^0+(\d+)$'
            cursor.execute(f"SELECT rowid, {modification.column_name} FROM {table_name} WHERE {modification.column_name} LIKE '0%'")
            rows = cursor.fetchall()
            
            updated_count = 0
            for rowid, value in rows:
                match = re.match(zero_padding_pattern, str(value))
                if match:
                    cleaned_value = match.group(1)
                    cursor.execute(f"UPDATE {table_name} SET {modification.column_name} = ? WHERE rowid = ?", 
                                 (cleaned_value, rowid))
                    updated_count += 1
            
            # column_masterの型も更新
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (modification.target_type.value, modification.file_name, modification.column_name))
            
            return {
                "success": True,
                "message": f"0パディング除去完了: {updated_count}件更新",
                "affected_rows": updated_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"0パディング除去エラー: {str(e)}"
            }
    
    def _execute_trailing_minus_fix(self, cursor: sqlite3.Cursor, 
                                  modification: FieldModification) -> Dict[str, Any]:
        """後ろマイナス修正を実行"""
        try:
            table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"テーブルが見つかりません: {table_name}"
                }
            
            # 後ろマイナスパターンを修正
            trailing_minus_pattern = r'^(\d+\.?\d*)-$'
            cursor.execute(f"SELECT rowid, {modification.column_name} FROM {table_name} WHERE {modification.column_name} LIKE '%-'")
            rows = cursor.fetchall()
            
            updated_count = 0
            for rowid, value in rows:
                match = re.match(trailing_minus_pattern, str(value))
                if match:
                    fixed_value = f"-{match.group(1)}"
                    cursor.execute(f"UPDATE {table_name} SET {modification.column_name} = ? WHERE rowid = ?", 
                                 (fixed_value, rowid))
                    updated_count += 1
            
            # column_masterの型も更新
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (modification.target_type.value, modification.file_name, modification.column_name))
            
            return {
                "success": True,
                "message": f"後ろマイナス修正完了: {updated_count}件更新",
                "affected_rows": updated_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"後ろマイナス修正エラー: {str(e)}"
            }
    
    def _execute_date_format_fix(self, cursor: sqlite3.Cursor, 
                               modification: FieldModification) -> Dict[str, Any]:
        """日付フォーマット修正を実行"""
        try:
            table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"テーブルが見つかりません: {table_name}"
                }
            
            # 日付フォーマット変換（YYYYMMDD → YYYY-MM-DD）
            cursor.execute(f"SELECT rowid, {modification.column_name} FROM {table_name} WHERE LENGTH({modification.column_name}) = 8")
            rows = cursor.fetchall()
            
            updated_count = 0
            for rowid, value in rows:
                if re.match(r'^\d{8}$', str(value)):
                    date_str = str(value)
                    formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} 00:00:00.000000"
                    cursor.execute(f"UPDATE {table_name} SET {modification.column_name} = ? WHERE rowid = ?", 
                                 (formatted_date, rowid))
                    updated_count += 1
            
            # column_masterの型も更新
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (modification.target_type.value, modification.file_name, modification.column_name))
            
            return {
                "success": True,
                "message": f"日付フォーマット修正完了: {updated_count}件更新",
                "affected_rows": updated_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"日付フォーマット修正エラー: {str(e)}"
            }
    
    def _execute_decimal_comma_fix(self, cursor: sqlite3.Cursor, 
                                 modification: FieldModification) -> Dict[str, Any]:
        """小数点カンマ修正を実行"""
        try:
            table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"テーブルが見つかりません: {table_name}"
                }
            
            # 小数点カンマを修正
            decimal_comma_pattern = r'^(\d+),(\d+)$'
            cursor.execute(f"SELECT rowid, {modification.column_name} FROM {table_name} WHERE {modification.column_name} LIKE '%,%'")
            rows = cursor.fetchall()
            
            updated_count = 0
            for rowid, value in rows:
                match = re.match(decimal_comma_pattern, str(value))
                if match:
                    fixed_value = f"{match.group(1)}.{match.group(2)}"
                    cursor.execute(f"UPDATE {table_name} SET {modification.column_name} = ? WHERE rowid = ?", 
                                 (fixed_value, rowid))
                    updated_count += 1
            
            # column_masterの型も更新
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (modification.target_type.value, modification.file_name, modification.column_name))
            
            return {
                "success": True,
                "message": f"小数点カンマ修正完了: {updated_count}件更新",
                "affected_rows": updated_count
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"小数点カンマ修正エラー: {str(e)}"
            }
    
    def _create_rollback_point(self, batch_id: str) -> Dict[str, Any]:
        """ロールバックポイントを作成"""
        rollback_point = {
            "rollback_id": f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "batch_id": batch_id,
            "created_at": datetime.now().isoformat(),
            "db_state": self._capture_db_state()
        }
        
        self.rollback_points.append(rollback_point)
        return rollback_point
    
    def _capture_db_state(self) -> Dict[str, Any]:
        """データベース状態をキャプチャ"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # column_masterの状態を記録
            cursor.execute("SELECT file_name, column_name, data_type FROM column_master")
            column_states = cursor.fetchall()
            
            return {
                "column_master_state": column_states,
                "timestamp": datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def rollback_to_backup(self, backup_id: str) -> bool:
        """バックアップからロールバック"""
        return self.backup_manager.restore_backup(backup_id, self.db_path)
    
    def _record_modification_history(self, batch: ModificationBatch, 
                                   executed_count: int, failed_count: int) -> None:
        """修正履歴を記録"""
        history_entry = {
            "batch_id": batch.batch_id,
            "batch_name": batch.name,
            "executed_at": datetime.now().isoformat(),
            "executed_modifications": executed_count,
            "failed_modifications": failed_count,
            "status": batch.status,
            "backup_path": batch.backup_path
        }
        
        self.modification_history.append(history_entry)
        
        # 履歴をファイルに保存
        history_file = Path("modification_history.json")
        try:
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    existing_history = json.load(f)
            else:
                existing_history = []
            
            existing_history.append(history_entry)
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(existing_history, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"履歴保存エラー: {e}")
    
    def get_modification_history(self) -> List[Dict[str, Any]]:
        """修正履歴を取得"""
        history_file = Path("modification_history.json")
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"履歴読み込みエラー: {e}")
        
        return self.modification_history

def main():
    """テスト実行"""
    from t002_data_structures import FieldModification, ModificationBatch
    
    print("=== 型修正エンジンテスト ===")
    
    # テスト用の修正エンジン
    engine = ModificationEngine("output/master.db")
    
    # テスト用修正情報
    test_modification = FieldModification(
        file_name="test.txt",
        column_name="test_field",
        current_type=FieldType.TEXT,
        target_type=FieldType.INTEGER,
        action=ModificationAction.TYPE_CHANGE,
        confidence=ConfidenceLevel.HIGH,
        reason="テスト用型変更"
    )
    
    # テスト用バッチ
    test_batch = ModificationBatch(
        batch_id="test_engine_001",
        name="エンジンテストバッチ",
        description="型修正エンジンのテスト",
        modifications=[test_modification]
    )
    
    # バッチ実行（実際のDBがある場合のみ）
    if Path("output/master.db").exists():
        result = engine.execute_batch(test_batch)
        print(f"バッチ実行結果: {result}")
    
    # 履歴表示
    history = engine.get_modification_history()
    print(f"修正履歴: {len(history)}件")

if __name__ == "__main__":
    main()