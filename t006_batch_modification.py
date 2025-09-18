#!/usr/bin/env python3
"""
T006: バッチ修正機能の実装
"""

import csv
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import asdict
from t002_data_structures import (
    FieldModification, ModificationBatch, ModificationAction, 
    FieldType, ConfidenceLevel
)
from t004_modification_engine import ModificationEngine

class BatchModificationManager:
    """バッチ修正管理クラス"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.modification_engine = ModificationEngine(db_path)
        self.progress_callbacks: List[Callable] = []
        self.error_handlers: List[Callable] = []
    
    def add_progress_callback(self, callback: Callable[[str, int, int], None]) -> None:
        """進捗コールバックを追加"""
        self.progress_callbacks.append(callback)
    
    def add_error_handler(self, handler: Callable[[str, Exception], None]) -> None:
        """エラーハンドラーを追加"""
        self.error_handlers.append(handler)
    
    def _notify_progress(self, message: str, current: int, total: int) -> None:
        """進捗を通知"""
        for callback in self.progress_callbacks:
            try:
                callback(message, current, total)
            except Exception as e:
                print(f"進捗コールバックエラー: {e}")
    
    def _handle_error(self, context: str, error: Exception) -> None:
        """エラーを処理"""
        for handler in self.error_handlers:
            try:
                handler(context, error)
            except Exception as e:
                print(f"エラーハンドラーエラー: {e}")
        
        # デフォルトエラー処理
        print(f"エラー ({context}): {error}")
    
    def load_modifications_from_csv(self, csv_file_path: str) -> List[FieldModification]:
        """CSV形式の修正指示を読み込み"""
        print(f"=== CSV修正指示読み込み: {csv_file_path} ===")
        
        modifications = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                required_columns = [
                    'file_name', 'column_name', 'current_type', 'target_type', 
                    'action', 'confidence', 'reason'
                ]
                
                # 必須カラムの存在確認
                missing_columns = [col for col in required_columns if col not in reader.fieldnames]
                if missing_columns:
                    raise ValueError(f"必須カラムが不足: {missing_columns}")
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # 空行をスキップ
                        if not any(row.values()):
                            continue
                        
                        # 修正情報を作成
                        modification = FieldModification(
                            file_name=row['file_name'].strip(),
                            column_name=row['column_name'].strip(),
                            current_type=FieldType(row['current_type'].strip()),
                            target_type=FieldType(row['target_type'].strip()),
                            action=ModificationAction(row['action'].strip()),
                            confidence=ConfidenceLevel(row['confidence'].strip()),
                            reason=row['reason'].strip(),
                            sample_data=row.get('sample_data', '').split(',') if row.get('sample_data') else [],
                            estimated_affected_rows=int(row.get('estimated_affected_rows', 0)),
                            validation_rules=json.loads(row.get('validation_rules', '{}'))
                        )
                        
                        modifications.append(modification)
                        
                    except Exception as e:
                        error_msg = f"行{row_num}の処理エラー: {e}"
                        self._handle_error(f"CSV読み込み", Exception(error_msg))
                        continue
                
                print(f"CSV読み込み完了: {len(modifications)}件の修正指示")
                return modifications
                
        except Exception as e:
            self._handle_error("CSV読み込み", e)
            return []
    
    def export_modifications_to_csv(self, modifications: List[FieldModification], 
                                  csv_file_path: str) -> bool:
        """修正指示をCSV形式でエクスポート"""
        print(f"=== CSV修正指示エクスポート: {csv_file_path} ===")
        
        try:
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = [
                    'file_name', 'column_name', 'current_type', 'target_type',
                    'action', 'confidence', 'reason', 'sample_data',
                    'estimated_affected_rows', 'validation_rules', 'created_at'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for modification in modifications:
                    writer.writerow({
                        'file_name': modification.file_name,
                        'column_name': modification.column_name,
                        'current_type': modification.current_type.value,
                        'target_type': modification.target_type.value,
                        'action': modification.action.value,
                        'confidence': modification.confidence.value,
                        'reason': modification.reason,
                        'sample_data': ','.join(modification.sample_data),
                        'estimated_affected_rows': modification.estimated_affected_rows,
                        'validation_rules': json.dumps(modification.validation_rules),
                        'created_at': modification.created_at.isoformat()
                    })
                
                print(f"CSVエクスポート完了: {len(modifications)}件")
                return True
                
        except Exception as e:
            self._handle_error("CSVエクスポート", e)
            return False
    
    def execute_batch_with_progress(self, batch: ModificationBatch) -> Dict[str, Any]:
        """進捗表示付きバッチ実行"""
        print(f"=== 進捗表示付きバッチ実行: {batch.name} ===")
        
        total_modifications = len(batch.modifications)
        self._notify_progress("バッチ実行開始", 0, total_modifications)
        
        # バックアップ作成
        self._notify_progress("バックアップ作成中", 0, total_modifications)
        backup_info = self.modification_engine.backup_manager.create_backup(
            self.db_path, batch, f"Batch execution backup: {batch.name}"
        )
        
        if not backup_info:
            error_msg = "バックアップ作成に失敗"
            self._handle_error("バッチ実行", Exception(error_msg))
            return {
                "success": False,
                "error": error_msg,
                "executed_modifications": 0
            }
        
        batch.backup_path = backup_info.backup_path
        batch.status = "in_progress"
        
        # 修正実行
        executed_count = 0
        failed_count = 0
        execution_log = []
        
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        
        try:
            for i, modification in enumerate(batch.modifications, 1):
                self._notify_progress(
                    f"修正実行中: {modification.file_name}.{modification.column_name}",
                    i, total_modifications
                )
                
                try:
                    result = self.modification_engine._execute_single_modification(conn, modification)
                    
                    if result["success"]:
                        executed_count += 1
                        log_msg = f"✅ {modification.file_name}.{modification.column_name}: {result['message']}"
                        execution_log.append(log_msg)
                        print(log_msg)
                    else:
                        failed_count += 1
                        log_msg = f"❌ {modification.file_name}.{modification.column_name}: {result['error']}"
                        execution_log.append(log_msg)
                        self._handle_error(f"修正実行", Exception(result['error']))
                    
                    # 進捗更新
                    time.sleep(0.1)  # UI更新のための短い待機
                    
                except Exception as e:
                    failed_count += 1
                    error_msg = f"修正実行エラー: {str(e)}"
                    log_msg = f"❌ {modification.file_name}.{modification.column_name}: {error_msg}"
                    execution_log.append(log_msg)
                    self._handle_error(f"修正実行", e)
            
            conn.commit()
            batch.status = "completed" if failed_count == 0 else "partial_success"
            batch.execution_log = execution_log
            
            self._notify_progress("バッチ実行完了", total_modifications, total_modifications)
            
            result = {
                "success": True,
                "executed_modifications": executed_count,
                "failed_modifications": failed_count,
                "backup_path": backup_info.backup_path,
                "execution_log": execution_log
            }
            
            print(f"バッチ実行完了: 成功{executed_count}件, 失敗{failed_count}件")
            return result
            
        except Exception as e:
            conn.rollback()
            batch.status = "failed"
            error_msg = f"バッチ実行エラー: {str(e)}"
            batch.execution_log = [error_msg]
            
            self._handle_error("バッチ実行", e)
            self._notify_progress(f"バッチ実行失敗: {error_msg}", 0, total_modifications)
            
            return {
                "success": False,
                "error": error_msg,
                "executed_modifications": executed_count,
                "backup_path": backup_info.backup_path
            }
            
        finally:
            conn.close()
    
    def create_batch_from_template(self, template_name: str, 
                                 target_files: List[str] = None) -> Optional[ModificationBatch]:
        """テンプレートからバッチを作成"""
        print(f"=== テンプレートからバッチ作成: {template_name} ===")
        
        try:
            from t002_rule_templates import RuleTemplateManager
            
            template_manager = RuleTemplateManager()
            rules = template_manager.create_rules_from_template(template_name)
            
            if not rules:
                print(f"テンプレート '{template_name}' からルールを作成できませんでした")
                return None
            
            # ルールを修正情報に変換（実際のデータベースをスキャンして適用可能な箇所を特定）
            modifications = self._scan_and_apply_rules(rules, target_files)
            
            if not modifications:
                print("適用可能な修正が見つかりませんでした")
                return None
            
            batch = ModificationBatch(
                batch_id=f"template_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=f"テンプレート適用: {template_name}",
                description=f"テンプレート '{template_name}' から生成されたバッチ",
                modifications=modifications
            )
            
            print(f"テンプレートバッチ作成完了: {len(modifications)}件の修正")
            return batch
            
        except Exception as e:
            self._handle_error("テンプレートバッチ作成", e)
            return None
    
    def _scan_and_apply_rules(self, rules: List, target_files: List[str] = None) -> List[FieldModification]:
        """ルールをスキャンして適用可能な修正を特定"""
        modifications = []
        
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
            tables = [row[0] for row in cursor.fetchall()]
            
            if target_files:
                # 指定されたファイルのみを対象
                target_tables = [f.replace('.txt', '').replace('.csv', '') for f in target_files]
                tables = [t for t in tables if t in target_tables]
            
            for rule in rules:
                for table in tables:
                    try:
                        # テーブル構造を取得
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = cursor.fetchall()
                        
                        for col_info in columns:
                            col_name = col_info[1]
                            
                            # ルールパターンに基づいてデータをサンプリング
                            cursor.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} IS NOT NULL LIMIT 20")
                            samples = [str(row[0]) for row in cursor.fetchall()]
                            
                            if samples:
                                # パターンマッチング
                                import re
                                matching_samples = [s for s in samples if re.match(rule.pattern, s)]
                                match_rate = len(matching_samples) / len(samples)
                                
                                if match_rate >= rule.confidence_threshold:
                                    # 修正情報を作成
                                    modification = FieldModification(
                                        file_name=f"{table}.txt",
                                        column_name=col_name,
                                        current_type=FieldType.TEXT,  # 仮の値
                                        target_type=rule.target_type,
                                        action=rule.action,
                                        confidence=ConfidenceLevel.HIGH if match_rate > 0.8 else ConfidenceLevel.MEDIUM,
                                        reason=f"ルール '{rule.name}' 適用 (マッチ率: {match_rate:.1%})",
                                        sample_data=matching_samples[:5],
                                        estimated_affected_rows=len(matching_samples)
                                    )
                                    
                                    modifications.append(modification)
                    
                    except Exception as e:
                        self._handle_error(f"ルール適用 ({table})", e)
                        continue
        
        finally:
            conn.close()
        
        return modifications
    
    def validate_batch_before_execution(self, batch: ModificationBatch) -> Dict[str, Any]:
        """バッチ実行前の検証"""
        print(f"=== バッチ実行前検証: {batch.name} ===")
        
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "statistics": {
                "total_modifications": len(batch.modifications),
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0,
                "estimated_total_rows": 0
            }
        }
        
        # 統計情報の計算
        for mod in batch.modifications:
            validation_result["statistics"]["estimated_total_rows"] += mod.estimated_affected_rows
            
            if mod.confidence == ConfidenceLevel.HIGH:
                validation_result["statistics"]["high_confidence"] += 1
            elif mod.confidence == ConfidenceLevel.MEDIUM:
                validation_result["statistics"]["medium_confidence"] += 1
            else:
                validation_result["statistics"]["low_confidence"] += 1
        
        # 警告とエラーのチェック
        low_confidence_count = validation_result["statistics"]["low_confidence"]
        if low_confidence_count > 0:
            validation_result["warnings"].append(
                f"信頼度の低い修正が{low_confidence_count}件含まれています"
            )
        
        large_batch_threshold = 1000
        if validation_result["statistics"]["estimated_total_rows"] > large_batch_threshold:
            validation_result["warnings"].append(
                f"大量のデータ修正が予想されます ({validation_result['statistics']['estimated_total_rows']}行)"
            )
        
        # データベース接続確認
        try:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.close()
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"データベース接続エラー: {e}")
        
        print(f"バッチ検証完了: {'有効' if validation_result['valid'] else '無効'}")
        return validation_result

def main():
    """テスト実行"""
    print("=== バッチ修正機能テスト ===")
    
    if not Path("output/master.db").exists():
        print("テスト用データベースが見つかりません")
        return
    
    manager = BatchModificationManager("output/master.db")
    
    # 進捗コールバックの設定
    def progress_callback(message: str, current: int, total: int):
        percentage = (current / total * 100) if total > 0 else 0
        print(f"進捗: {percentage:5.1f}% ({current}/{total}) - {message}")
    
    def error_handler(context: str, error: Exception):
        print(f"エラーハンドラー: {context} - {error}")
    
    manager.add_progress_callback(progress_callback)
    manager.add_error_handler(error_handler)
    
    # テスト用修正情報をCSVエクスポート
    test_modifications = [
        FieldModification(
            file_name="test.txt",
            column_name="test_field",
            current_type=FieldType.TEXT,
            target_type=FieldType.INTEGER,
            action=ModificationAction.TYPE_CHANGE,
            confidence=ConfidenceLevel.HIGH,
            reason="テスト用修正"
        )
    ]
    
    csv_path = "test_modifications.csv"
    if manager.export_modifications_to_csv(test_modifications, csv_path):
        print(f"テスト用CSVエクスポート完了: {csv_path}")
        
        # CSVから読み込みテスト
        loaded_modifications = manager.load_modifications_from_csv(csv_path)
        print(f"CSV読み込みテスト: {len(loaded_modifications)}件")
    
    # テンプレートからバッチ作成テスト
    batch = manager.create_batch_from_template("sap_data_cleaning")
    if batch:
        print(f"テンプレートバッチ作成成功: {len(batch.modifications)}件")
        
        # バッチ検証
        validation = manager.validate_batch_before_execution(batch)
        print(f"バッチ検証結果: {'有効' if validation['valid'] else '無効'}")

if __name__ == "__main__":
    main()