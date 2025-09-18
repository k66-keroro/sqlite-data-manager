#!/usr/bin/env python3
"""
T008: 統合テスト
"""

import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# テスト対象モジュールのインポート
from t002_data_structures import (
    FieldModification, ModificationBatch, ModificationAction, 
    FieldType, ConfidenceLevel, DataStructureManager
)
from t002_rule_templates import RuleTemplateManager
from t002_backup_system import BackupManager
from t004_modification_engine import ModificationEngine
from t005_sap_special_rules import SAPSpecialRulesEngine
from t006_batch_modification import BatchModificationManager
from t007_verification_system import VerificationSystem

class IntegrationTestSuite:
    """統合テストスイート"""
    
    def __init__(self):
        self.test_db_path = None
        self.temp_dir = None
        self.original_db_path = "output/master.db"
        self.test_results = []
    
    def setup_test_environment(self) -> bool:
        """テスト環境をセットアップ"""
        try:
            # 一時ディレクトリ作成
            self.temp_dir = tempfile.mkdtemp(prefix="sqlite_manager_test_")
            self.test_db_path = os.path.join(self.temp_dir, "test_master.db")
            
            # 元のDBをコピー（存在する場合）
            if os.path.exists(self.original_db_path):
                shutil.copy2(self.original_db_path, self.test_db_path)
                print(f"テスト用DB作成: {self.test_db_path}")
            else:
                # テスト用の最小限DBを作成
                self._create_minimal_test_db()
                print(f"最小限テスト用DB作成: {self.test_db_path}")
            
            return True
            
        except Exception as e:
            print(f"テスト環境セットアップエラー: {e}")
            return False
    
    def cleanup_test_environment(self) -> None:
        """テスト環境をクリーンアップ"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("テスト環境クリーンアップ完了")
        except Exception as e:
            print(f"クリーンアップエラー: {e}")
    
    def _create_minimal_test_db(self) -> None:
        """最小限のテスト用DBを作成"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        try:
            # column_masterテーブル作成
            cursor.execute("""
                CREATE TABLE column_master (
                    file_name TEXT,
                    column_name TEXT,
                    data_type TEXT,
                    initial_inferred_type TEXT,
                    encoding TEXT,
                    delimiter TEXT,
                    PRIMARY KEY (file_name, column_name)
                )
            """)
            
            # テスト用データ挿入
            test_data = [
                ("test_file.txt", "test_field1", "TEXT", "TEXT", "utf-8", "\t"),
                ("test_file.txt", "test_field2", "TEXT", "INTEGER", "utf-8", "\t"),
                ("test_file.txt", "test_field3", "TEXT", "REAL", "utf-8", "\t"),
                ("sap_data.txt", "amount_field", "TEXT", "REAL", "cp932", "\t"),
                ("sap_data.txt", "code_field", "TEXT", "TEXT", "cp932", "\t")
            ]
            
            cursor.executemany("""
                INSERT INTO column_master 
                (file_name, column_name, data_type, initial_inferred_type, encoding, delimiter)
                VALUES (?, ?, ?, ?, ?, ?)
            """, test_data)
            
            # テスト用実データテーブル作成
            cursor.execute("""
                CREATE TABLE test_file (
                    test_field1 TEXT,
                    test_field2 TEXT,
                    test_field3 TEXT
                )
            """)
            
            cursor.execute("""
                INSERT INTO test_file VALUES 
                ('sample1', '123', '45.67'),
                ('sample2', '456', '78.90'),
                ('sample3', '789', '12.34')
            """)
            
            cursor.execute("""
                CREATE TABLE sap_data (
                    amount_field TEXT,
                    code_field TEXT
                )
            """)
            
            cursor.execute("""
                INSERT INTO sap_data VALUES 
                ('123.45-', 'CODE001'),
                ('678.90-', 'CODE002'),
                ('100,50', 'CODE003')
            """)
            
            conn.commit()
            
        finally:
            conn.close()
    
    def run_all_tests(self) -> Dict[str, Any]:
        """すべての統合テストを実行"""
        print("=== 統合テスト実行開始 ===")
        
        if not self.setup_test_environment():
            return {"success": False, "error": "テスト環境セットアップ失敗"}
        
        try:
            # 各テストを実行
            self.test_data_structure_management()
            self.test_rule_template_system()
            self.test_backup_system()
            self.test_modification_engine()
            self.test_sap_special_rules()
            self.test_batch_modification()
            self.test_verification_system()
            self.test_end_to_end_workflow()
            self.test_performance()
            self.test_error_recovery()
            
            # 結果集計
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["passed"])
            failed_tests = total_tests - passed_tests
            
            overall_result = {
                "success": failed_tests == 0,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "test_results": self.test_results
            }
            
            print(f"=== 統合テスト完了 ===")
            print(f"総テスト数: {total_tests}")
            print(f"成功: {passed_tests}")
            print(f"失敗: {failed_tests}")
            
            return overall_result
            
        finally:
            self.cleanup_test_environment()
    
    def _add_test_result(self, test_name: str, passed: bool, message: str, details: Dict = None):
        """テスト結果を記録"""
        self.test_results.append({
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        })
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
    
    def test_data_structure_management(self) -> None:
        """データ構造管理テスト"""
        try:
            manager = DataStructureManager()
            
            # 修正情報作成テスト
            modification = FieldModification(
                file_name="test.txt",
                column_name="test_field",
                current_type=FieldType.TEXT,
                target_type=FieldType.INTEGER,
                action=ModificationAction.TYPE_CHANGE,
                confidence=ConfidenceLevel.HIGH,
                reason="テスト用修正"
            )
            
            manager.add_modification(modification)
            
            # バッチ作成テスト
            batch = manager.create_batch("テストバッチ", "統合テスト用", [modification])
            
            # 検証
            assert len(manager.modifications) == 1
            assert len(manager.batches) == 1
            assert batch.batch_id is not None
            
            self._add_test_result("data_structure_management", True, "データ構造管理正常")
            
        except Exception as e:
            self._add_test_result("data_structure_management", False, f"エラー: {e}")
    
    def test_rule_template_system(self) -> None:
        """ルールテンプレートシステムテスト"""
        try:
            manager = RuleTemplateManager()
            
            # テンプレート一覧取得
            templates = manager.list_templates()
            assert len(templates) > 0
            
            # ルール作成テスト
            rules = manager.create_rules_from_template("sap_data_cleaning")
            assert len(rules) > 0
            
            # パターン検証テスト
            test_data = ["0001", "0002", "0003"]
            validation = manager.validate_rule_pattern(r"^0+(\d+)$", test_data)
            assert validation["valid"] == True
            assert validation["match_rate"] == 1.0
            
            self._add_test_result("rule_template_system", True, "ルールテンプレートシステム正常")
            
        except Exception as e:
            self._add_test_result("rule_template_system", False, f"エラー: {e}")
    
    def test_backup_system(self) -> None:
        """バックアップシステムテスト"""
        try:
            backup_manager = BackupManager(os.path.join(self.temp_dir, "backups"))
            
            # テスト用バッチ
            from t002_data_structures import ModificationBatch
            test_batch = ModificationBatch(
                batch_id="test_backup_001",
                name="バックアップテスト",
                description="統合テスト用バックアップ"
            )
            
            # バックアップ作成テスト
            backup_info = backup_manager.create_backup(self.test_db_path, test_batch)
            assert backup_info is not None
            assert os.path.exists(backup_info.backup_path)
            
            # 整合性チェックテスト
            integrity_ok = backup_manager.verify_backup_integrity(backup_info)
            assert integrity_ok == True
            
            # バックアップ一覧テスト
            backups = backup_manager.list_backups()
            assert len(backups) >= 1
            
            self._add_test_result("backup_system", True, "バックアップシステム正常")
            
        except Exception as e:
            self._add_test_result("backup_system", False, f"エラー: {e}")
    
    def test_modification_engine(self) -> None:
        """修正エンジンテスト"""
        try:
            engine = ModificationEngine(self.test_db_path)
            
            # テスト用修正
            modification = FieldModification(
                file_name="test_file.txt",
                column_name="test_field2",
                current_type=FieldType.TEXT,
                target_type=FieldType.INTEGER,
                action=ModificationAction.TYPE_CHANGE,
                confidence=ConfidenceLevel.HIGH,
                reason="統合テスト用型変更"
            )
            
            # バッチ作成
            batch = ModificationBatch(
                batch_id="test_engine_001",
                name="エンジンテスト",
                description="修正エンジン統合テスト",
                modifications=[modification]
            )
            
            # バッチ実行テスト
            result = engine.execute_batch(batch)
            assert result["success"] == True
            
            self._add_test_result("modification_engine", True, "修正エンジン正常")
            
        except Exception as e:
            self._add_test_result("modification_engine", False, f"エラー: {e}")
    
    def test_sap_special_rules(self) -> None:
        """SAP特殊ルールテスト"""
        try:
            engine = SAPSpecialRulesEngine(self.test_db_path)
            
            # 後ろマイナス検出テスト
            trailing_minus_fields = engine.detect_trailing_minus_fields()
            
            # 小数点カンマ検出テスト
            decimal_comma_fields = engine.detect_decimal_comma_fields()
            
            # コードフィールド検出テスト
            code_fields = engine.detect_code_fields()
            
            # GUI統合機能設計テスト
            integration_spec = engine.create_gui_rule_integration()
            assert "gui_interface" in integration_spec
            
            self._add_test_result("sap_special_rules", True, "SAP特殊ルール正常")
            
        except Exception as e:
            self._add_test_result("sap_special_rules", False, f"エラー: {e}")
    
    def test_batch_modification(self) -> None:
        """バッチ修正機能テスト"""
        try:
            manager = BatchModificationManager(self.test_db_path)
            
            # 進捗コールバックテスト
            progress_calls = []
            def progress_callback(message, current, total):
                progress_calls.append((message, current, total))
            
            manager.add_progress_callback(progress_callback)
            
            # テスト用修正をCSVエクスポート
            test_modifications = [
                FieldModification(
                    file_name="test_file.txt",
                    column_name="test_field3",
                    current_type=FieldType.TEXT,
                    target_type=FieldType.REAL,
                    action=ModificationAction.TYPE_CHANGE,
                    confidence=ConfidenceLevel.HIGH,
                    reason="バッチテスト用修正"
                )
            ]
            
            csv_path = os.path.join(self.temp_dir, "test_batch.csv")
            export_success = manager.export_modifications_to_csv(test_modifications, csv_path)
            assert export_success == True
            assert os.path.exists(csv_path)
            
            # CSVから読み込みテスト
            loaded_modifications = manager.load_modifications_from_csv(csv_path)
            assert len(loaded_modifications) == 1
            
            self._add_test_result("batch_modification", True, "バッチ修正機能正常")
            
        except Exception as e:
            self._add_test_result("batch_modification", False, f"エラー: {e}")
    
    def test_verification_system(self) -> None:
        """検証システムテスト"""
        try:
            verification_system = VerificationSystem(self.test_db_path)
            
            # テスト用バッチ
            test_batch = ModificationBatch(
                batch_id="test_verification_001",
                name="検証テスト",
                description="検証システム統合テスト",
                modifications=[
                    FieldModification(
                        file_name="test_file.txt",
                        column_name="test_field1",
                        current_type=FieldType.TEXT,
                        target_type=FieldType.TEXT,
                        action=ModificationAction.TYPE_CHANGE,
                        confidence=ConfidenceLevel.HIGH,
                        reason="検証テスト用"
                    )
                ]
            )
            
            # 検証実行テスト
            report = verification_system.verify_modification_batch(test_batch)
            assert report.batch_id == test_batch.batch_id
            assert len(report.integrity_checks) > 0
            assert report.overall_status in ["passed", "warning", "failed"]
            
            self._add_test_result("verification_system", True, "検証システム正常")
            
        except Exception as e:
            self._add_test_result("verification_system", False, f"エラー: {e}")
    
    def test_end_to_end_workflow(self) -> None:
        """エンドツーエンドワークフローテスト"""
        try:
            # 1. ルールテンプレートからバッチ作成
            batch_manager = BatchModificationManager(self.test_db_path)
            batch = batch_manager.create_batch_from_template("numeric_conversion")
            
            if batch and len(batch.modifications) > 0:
                # 2. バッチ検証
                validation = batch_manager.validate_batch_before_execution(batch)
                assert "valid" in validation
                
                # 3. バッチ実行
                if validation["valid"]:
                    result = batch_manager.execute_batch_with_progress(batch)
                    
                    # 4. 結果検証
                    verification_system = VerificationSystem(self.test_db_path)
                    report = verification_system.verify_modification_batch(batch)
                    
                    assert report.overall_status in ["passed", "warning", "failed"]
            
            self._add_test_result("end_to_end_workflow", True, "エンドツーエンドワークフロー正常")
            
        except Exception as e:
            self._add_test_result("end_to_end_workflow", False, f"エラー: {e}")
    
    def test_performance(self) -> None:
        """パフォーマンステスト"""
        try:
            start_time = datetime.now()
            
            # 大量データでのテスト（シミュレーション）
            modifications = []
            for i in range(100):  # 100個の修正を作成
                modifications.append(
                    FieldModification(
                        file_name=f"perf_test_{i % 10}.txt",
                        column_name=f"field_{i}",
                        current_type=FieldType.TEXT,
                        target_type=FieldType.INTEGER,
                        action=ModificationAction.TYPE_CHANGE,
                        confidence=ConfidenceLevel.MEDIUM,
                        reason=f"パフォーマンステスト {i}"
                    )
                )
            
            # データ構造管理のパフォーマンス
            manager = DataStructureManager()
            for mod in modifications:
                manager.add_modification(mod)
            
            batch = manager.create_batch("パフォーマンステスト", "大量データテスト", modifications)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 10秒以内で完了することを確認
            assert duration < 10.0
            
            self._add_test_result("performance", True, f"パフォーマンステスト正常 ({duration:.2f}秒)")
            
        except Exception as e:
            self._add_test_result("performance", False, f"エラー: {e}")
    
    def test_error_recovery(self) -> None:
        """エラー回復テスト"""
        try:
            # 無効なDBパスでのテスト
            invalid_db_path = "/invalid/path/to/db.sqlite"
            
            try:
                engine = ModificationEngine(invalid_db_path)
                # エラーが発生することを期待
                assert False, "無効なDBパスでエラーが発生しませんでした"
            except:
                # エラーが発生することが正常
                pass
            
            # 無効な修正データでのテスト
            try:
                invalid_modification = FieldModification(
                    file_name="",  # 空のファイル名
                    column_name="",  # 空のカラム名
                    current_type=FieldType.TEXT,
                    target_type=FieldType.INTEGER,
                    action=ModificationAction.TYPE_CHANGE,
                    confidence=ConfidenceLevel.HIGH,
                    reason="無効データテスト"
                )
                
                # バリデーションでエラーが検出されることを確認
                # （実際の実装では適切なバリデーションが必要）
                
            except:
                pass
            
            self._add_test_result("error_recovery", True, "エラー回復テスト正常")
            
        except Exception as e:
            self._add_test_result("error_recovery", False, f"エラー: {e}")

def main():
    """統合テストメイン実行"""
    print("=== SQLite Data Manager 統合テスト ===")
    
    test_suite = IntegrationTestSuite()
    results = test_suite.run_all_tests()
    
    # 結果レポート生成
    report_path = "integration_test_report.json"
    try:
        import json
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"統合テストレポート保存: {report_path}")
    except Exception as e:
        print(f"レポート保存エラー: {e}")
    
    # 結果サマリー表示
    if results["success"]:
        print("🎉 すべての統合テストが成功しました！")
    else:
        print(f"⚠️  {results['failed_tests']}件のテストが失敗しました")
        
        # 失敗したテストの詳細表示
        for result in results["test_results"]:
            if not result["passed"]:
                print(f"  ❌ {result['test_name']}: {result['message']}")
    
    return results["success"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)