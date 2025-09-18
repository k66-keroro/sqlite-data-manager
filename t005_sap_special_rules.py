#!/usr/bin/env python3
"""
T005: SAP データ特殊ルールの実装
"""

import sqlite3
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from t002_data_structures import (
    FieldModification, ModificationBatch, ModificationAction, 
    FieldType, ConfidenceLevel
)
from t004_modification_engine import ModificationEngine

class SAPSpecialRulesEngine:
    """SAP特殊ルール処理エンジン"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.modification_engine = ModificationEngine(db_path)
        self.sap_patterns = self._load_sap_patterns()
    
    def _load_sap_patterns(self) -> Dict[str, Any]:
        """SAPパターンルールを読み込み"""
        try:
            with open('pattern_rules_data.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('sap_patterns', {})
        except Exception as e:
            print(f"SAPパターン読み込みエラー: {e}")
            return {
                "trailing_minus": r"^(\d+\.?\d*)-$",
                "zero_padding": r"^0+(\d+)$",
                "decimal_comma": r"^(\d+),(\d+)$"
            }
    
    def detect_trailing_minus_fields(self) -> List[FieldModification]:
        """後ろマイナスフィールドを検出"""
        print("=== 後ろマイナスフィールド検出 ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        modifications = []
        
        try:
            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
            tables = [row[0] for row in cursor.fetchall()]
            
            trailing_minus_pattern = self.sap_patterns.get("trailing_minus", r"^(\d+\.?\d*)-$")
            
            for table in tables:
                try:
                    # テーブル構造を取得
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    for col_info in columns:
                        col_name = col_info[1]
                        
                        # 金額・原価・単価系フィールドをチェック
                        if any(keyword in col_name for keyword in ['金額', '原価', '単価', 'AMOUNT', 'COST', 'PRICE']):
                            # 後ろマイナスデータをサンプリング
                            cursor.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} LIKE '%-' LIMIT 10")
                            samples = [row[0] for row in cursor.fetchall()]
                            
                            if samples:
                                # パターンマッチング確認
                                matching_samples = [s for s in samples if re.match(trailing_minus_pattern, str(s))]
                                
                                if matching_samples:
                                    # 全体の件数を確認
                                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} LIKE '%-'")
                                    total_count = cursor.fetchone()[0]
                                    
                                    confidence = ConfidenceLevel.HIGH if len(matching_samples) >= 5 else ConfidenceLevel.MEDIUM
                                    
                                    modification = FieldModification(
                                        file_name=f"{table}.txt",
                                        column_name=col_name,
                                        current_type=FieldType.TEXT,
                                        target_type=FieldType.REAL,
                                        action=ModificationAction.TRAILING_MINUS_FIX,
                                        confidence=confidence,
                                        reason=f"SAP後ろマイナス形式検出: {len(matching_samples)}件のサンプル",
                                        sample_data=matching_samples[:5],
                                        estimated_affected_rows=total_count
                                    )
                                    
                                    modifications.append(modification)
                                    print(f"検出: {table}.{col_name} - {total_count}件の後ろマイナス")
                
                except Exception as e:
                    print(f"テーブル処理エラー ({table}): {e}")
                    continue
        
        finally:
            conn.close()
        
        print(f"後ろマイナスフィールド検出完了: {len(modifications)}件")
        return modifications
    
    def detect_decimal_comma_fields(self) -> List[FieldModification]:
        """小数点カンマフィールドを検出"""
        print("=== 小数点カンマフィールド検出 ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        modifications = []
        
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
            tables = [row[0] for row in cursor.fetchall()]
            
            decimal_comma_pattern = self.sap_patterns.get("decimal_comma", r"^(\d+),(\d+)$")
            
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    
                    for col_info in columns:
                        col_name = col_info[1]
                        
                        # 数値系フィールドをチェック
                        if any(keyword in col_name for keyword in ['単価', 'レート', '係数', '率', 'RATE', 'RATIO']):
                            # カンマ区切り数値をサンプリング
                            cursor.execute(f"SELECT {col_name} FROM {table} WHERE {col_name} LIKE '%,%' LIMIT 10")
                            samples = [row[0] for row in cursor.fetchall()]
                            
                            if samples:
                                matching_samples = [s for s in samples if re.match(decimal_comma_pattern, str(s))]
                                
                                if matching_samples:
                                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} LIKE '%,%'")
                                    total_count = cursor.fetchone()[0]
                                    
                                    confidence = ConfidenceLevel.HIGH if len(matching_samples) >= 5 else ConfidenceLevel.MEDIUM
                                    
                                    modification = FieldModification(
                                        file_name=f"{table}.txt",
                                        column_name=col_name,
                                        current_type=FieldType.TEXT,
                                        target_type=FieldType.REAL,
                                        action=ModificationAction.DECIMAL_COMMA_FIX,
                                        confidence=confidence,
                                        reason=f"SAP小数点カンマ形式検出: {len(matching_samples)}件のサンプル",
                                        sample_data=matching_samples[:5],
                                        estimated_affected_rows=total_count
                                    )
                                    
                                    modifications.append(modification)
                                    print(f"検出: {table}.{col_name} - {total_count}件の小数点カンマ")
                
                except Exception as e:
                    print(f"テーブル処理エラー ({table}): {e}")
                    continue
        
        finally:
            conn.close()
        
        print(f"小数点カンマフィールド検出完了: {len(modifications)}件")
        return modifications
    
    def detect_code_fields(self) -> List[FieldModification]:
        """コード系フィールドを自動識別"""
        print("=== コード系フィールド自動識別 ===")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        modifications = []
        
        try:
            # column_masterからコード系フィールドを特定
            cursor.execute("""
                SELECT file_name, column_name, data_type 
                FROM column_master 
                WHERE (column_name LIKE '%コード%' OR column_name LIKE '%番号%' OR 
                       column_name LIKE '%ID%' OR column_name LIKE '%CODE%')
                AND data_type != 'TEXT'
            """)
            
            code_candidates = cursor.fetchall()
            
            for file_name, column_name, current_type in code_candidates:
                # 実際のデータをサンプリング
                table_name = file_name.replace('.txt', '').replace('.csv', '')
                
                try:
                    cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 20")
                    samples = [str(row[0]) for row in cursor.fetchall()]
                    
                    # 0で始まるデータの割合をチェック
                    zero_start_count = sum(1 for s in samples if s.startswith('0') and len(s) > 1)
                    zero_start_ratio = zero_start_count / len(samples) if samples else 0
                    
                    # 英数字混在をチェック
                    alphanumeric_count = sum(1 for s in samples if re.match(r'^[A-Za-z0-9]+$', s) and not s.isdigit())
                    alphanumeric_ratio = alphanumeric_count / len(samples) if samples else 0
                    
                    # コードフィールドの判定
                    is_code_field = (zero_start_ratio > 0.3 or alphanumeric_ratio > 0.1)
                    
                    if is_code_field and current_type != 'TEXT':
                        confidence = ConfidenceLevel.HIGH if zero_start_ratio > 0.5 else ConfidenceLevel.MEDIUM
                        
                        modification = FieldModification(
                            file_name=file_name,
                            column_name=column_name,
                            current_type=FieldType(current_type),
                            target_type=FieldType.TEXT,
                            action=ModificationAction.TYPE_CHANGE,
                            confidence=confidence,
                            reason=f"コードフィールド識別: 0始まり{zero_start_ratio:.1%}, 英数字{alphanumeric_ratio:.1%}",
                            sample_data=samples[:5],
                            estimated_affected_rows=len(samples)
                        )
                        
                        modifications.append(modification)
                        print(f"識別: {file_name}.{column_name} - コードフィールドとしてTEXT型に変更推奨")
                
                except Exception as e:
                    print(f"データサンプリングエラー ({table_name}.{column_name}): {e}")
                    continue
        
        finally:
            conn.close()
        
        print(f"コード系フィールド識別完了: {len(modifications)}件")
        return modifications
    
    def create_gui_rule_integration(self) -> Dict[str, Any]:
        """GUI ルール追加→自動反映機能の設計"""
        print("=== GUI ルール統合機能設計 ===")
        
        integration_spec = {
            "gui_interface": {
                "rule_creation_form": {
                    "fields": [
                        {"name": "rule_name", "type": "text", "required": True},
                        {"name": "description", "type": "textarea", "required": True},
                        {"name": "pattern", "type": "text", "required": True, "validation": "regex"},
                        {"name": "target_type", "type": "select", "options": ["TEXT", "INTEGER", "REAL", "DATETIME"]},
                        {"name": "action", "type": "select", "options": ["type_change", "zero_padding_remove", "trailing_minus_fix", "date_format_fix", "decimal_comma_fix"]},
                        {"name": "confidence_threshold", "type": "number", "min": 0.0, "max": 1.0, "default": 0.7},
                        {"name": "field_patterns", "type": "text", "multiple": True, "description": "適用対象フィールド名パターン"}
                    ]
                },
                "rule_testing": {
                    "test_data_input": "textarea",
                    "pattern_validation": "real_time",
                    "match_preview": "table"
                },
                "rule_management": {
                    "rule_list": "table_with_actions",
                    "enable_disable": "toggle",
                    "edit_rule": "modal_form",
                    "delete_rule": "confirmation_dialog"
                }
            },
            "auto_application": {
                "trigger_events": [
                    "new_rule_created",
                    "rule_enabled",
                    "data_import_completed",
                    "manual_scan_requested"
                ],
                "processing_pipeline": [
                    "scan_database_for_matching_fields",
                    "apply_pattern_matching",
                    "calculate_confidence_scores",
                    "create_modification_suggestions",
                    "present_to_user_for_approval"
                ],
                "approval_workflow": {
                    "auto_apply_threshold": 0.9,
                    "require_approval_threshold": 0.7,
                    "reject_threshold": 0.5
                }
            },
            "integration_points": {
                "pattern_rules_data.json": "rule_storage",
                "column_master": "field_metadata",
                "modification_engine": "rule_execution",
                "backup_system": "safety_net"
            }
        }
        
        # 設計仕様をファイルに保存
        with open('gui_rule_integration_spec.json', 'w', encoding='utf-8') as f:
            json.dump(integration_spec, f, ensure_ascii=False, indent=2)
        
        print("GUI ルール統合機能設計完了: gui_rule_integration_spec.json")
        return integration_spec
    
    def execute_sap_special_rules_batch(self) -> Dict[str, Any]:
        """SAP特殊ルールを一括実行"""
        print("=== SAP特殊ルール一括実行 ===")
        
        # 各種特殊ルールを検出
        trailing_minus_mods = self.detect_trailing_minus_fields()
        decimal_comma_mods = self.detect_decimal_comma_fields()
        code_field_mods = self.detect_code_fields()
        
        all_modifications = trailing_minus_mods + decimal_comma_mods + code_field_mods
        
        if not all_modifications:
            return {
                "success": True,
                "message": "適用可能なSAP特殊ルールが見つかりませんでした",
                "executed_modifications": 0
            }
        
        # バッチを作成
        batch = ModificationBatch(
            batch_id=f"sap_special_rules_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name="SAP特殊ルール一括適用",
            description=f"後ろマイナス、小数点カンマ、コードフィールド識別の一括処理",
            modifications=all_modifications
        )
        
        # バッチ実行
        result = self.modification_engine.execute_batch(batch)
        
        print(f"SAP特殊ルール実行完了: {result}")
        return result

def main():
    """テスト実行"""
    print("=== SAP特殊ルールエンジンテスト ===")
    
    if not Path("output/master.db").exists():
        print("テスト用データベースが見つかりません")
        return
    
    engine = SAPSpecialRulesEngine("output/master.db")
    
    # 各種検出テスト
    trailing_minus_fields = engine.detect_trailing_minus_fields()
    print(f"後ろマイナスフィールド: {len(trailing_minus_fields)}件")
    
    decimal_comma_fields = engine.detect_decimal_comma_fields()
    print(f"小数点カンマフィールド: {len(decimal_comma_fields)}件")
    
    code_fields = engine.detect_code_fields()
    print(f"コード系フィールド: {len(code_fields)}件")
    
    # GUI統合機能設計
    integration_spec = engine.create_gui_rule_integration()
    print(f"GUI統合機能設計完了")
    
    # 実際の実行（コメントアウト - テスト時のみ有効化）
    # result = engine.execute_sap_special_rules_batch()
    # print(f"一括実行結果: {result}")

if __name__ == "__main__":
    main()