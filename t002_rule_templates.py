#!/usr/bin/env python3
"""
T002: 修正ルールのテンプレート作成機能
"""

import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from t002_data_structures import ModificationRule, ModificationAction, FieldType, ConfidenceLevel

class RuleTemplateManager:
    """修正ルールテンプレート管理クラス"""
    
    def __init__(self, template_file: str = "rule_templates.json"):
        self.template_file = template_file
        self.templates: Dict[str, Dict] = {}
        self.load_templates()
    
    def load_templates(self) -> None:
        """テンプレートファイルを読み込み"""
        if Path(self.template_file).exists():
            try:
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    self.templates = json.load(f)
            except Exception as e:
                print(f"テンプレート読み込みエラー: {e}")
                self.templates = {}
        
        # デフォルトテンプレートがない場合は作成
        if not self.templates:
            self.create_default_templates()
    
    def create_default_templates(self) -> None:
        """デフォルトテンプレートを作成"""
        self.templates = {
            "sap_data_cleaning": {
                "name": "SAPデータクリーニング",
                "description": "SAP特有のデータ形式を標準形式に変換",
                "rules": [
                    {
                        "rule_id": "sap_zero_padding",
                        "name": "SAP 0パディング除去",
                        "description": "SAPの伝票番号等の先頭0を除去",
                        "pattern": r"^0{2,}(\d+)$",
                        "action": "zero_padding_remove",
                        "target_type": "TEXT",  # 伝票番号は文字列として保持
                        "confidence_threshold": 0.9,
                        "field_patterns": [".*伝票番号.*", ".*明細番号.*", ".*コード.*"]
                    },
                    {
                        "rule_id": "sap_trailing_minus",
                        "name": "SAP 後ろマイナス修正",
                        "description": "SAP会計データの末尾マイナスを先頭に移動",
                        "pattern": r"^(\d+\.?\d*)-$",
                        "action": "trailing_minus_fix",
                        "target_type": "REAL",
                        "confidence_threshold": 0.95,
                        "field_patterns": [".*金額.*", ".*原価.*", ".*単価.*"]
                    },
                    {
                        "rule_id": "sap_decimal_comma",
                        "name": "SAP 小数点カンマ修正",
                        "description": "ヨーロッパ式小数点表記を標準形式に変換",
                        "pattern": r"^(\d+),(\d+)$",
                        "action": "decimal_comma_fix",
                        "target_type": "REAL",
                        "confidence_threshold": 0.85,
                        "field_patterns": [".*単価.*", ".*レート.*", ".*係数.*"]
                    }
                ]
            },
            "date_normalization": {
                "name": "日付正規化",
                "description": "様々な日付形式をDATETIME型に統一",
                "rules": [
                    {
                        "rule_id": "date_yyyymmdd",
                        "name": "YYYYMMDD形式",
                        "description": "8桁数値日付をDATETIME型に変換",
                        "pattern": r"^(19|20)\d{6}$",
                        "action": "date_format_fix",
                        "target_type": "DATETIME",
                        "confidence_threshold": 0.9,
                        "field_patterns": [".*日付.*", ".*日.*", ".*DATE.*"]
                    },
                    {
                        "rule_id": "date_yyyy_mm_dd",
                        "name": "YYYY/MM/DD形式",
                        "description": "スラッシュ区切り日付をDATETIME型に変換",
                        "pattern": r"^(19|20)\d{2}/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])$",
                        "action": "date_format_fix",
                        "target_type": "DATETIME",
                        "confidence_threshold": 0.95,
                        "field_patterns": [".*日付.*", ".*日.*", ".*DATE.*"]
                    },
                    {
                        "rule_id": "date_dd_mm_yyyy",
                        "name": "DD.MM.YYYY形式",
                        "description": "ドット区切り日付をDATETIME型に変換",
                        "pattern": r"^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$",
                        "action": "date_format_fix",
                        "target_type": "DATETIME",
                        "confidence_threshold": 0.9,
                        "field_patterns": [".*日付.*", ".*日.*", ".*DATE.*"]
                    }
                ]
            },
            "numeric_conversion": {
                "name": "数値変換",
                "description": "テキスト形式の数値を適切な数値型に変換",
                "rules": [
                    {
                        "rule_id": "pure_integer",
                        "name": "純粋な整数",
                        "description": "整数のみのテキストをINTEGER型に変換",
                        "pattern": r"^-?\d+$",
                        "action": "type_change",
                        "target_type": "INTEGER",
                        "confidence_threshold": 0.95,
                        "field_patterns": [".*数量.*", ".*個数.*", ".*件数.*", ".*COUNT.*"]
                    },
                    {
                        "rule_id": "decimal_number",
                        "name": "小数点数値",
                        "description": "小数点を含む数値をREAL型に変換",
                        "pattern": r"^-?\d+\.\d+$",
                        "action": "type_change",
                        "target_type": "REAL",
                        "confidence_threshold": 0.9,
                        "field_patterns": [".*金額.*", ".*単価.*", ".*重量.*", ".*AMOUNT.*"]
                    },
                    {
                        "rule_id": "percentage",
                        "name": "パーセンテージ",
                        "description": "%記号付き数値をREAL型に変換",
                        "pattern": r"^(\d+\.?\d*)%$",
                        "action": "type_change",
                        "target_type": "REAL",
                        "confidence_threshold": 0.8,
                        "field_patterns": [".*率.*", ".*パーセント.*", ".*RATE.*"]
                    }
                ]
            },
            "code_field_handling": {
                "name": "コードフィールド処理",
                "description": "コード系フィールドの適切な型設定",
                "rules": [
                    {
                        "rule_id": "keep_leading_zeros",
                        "name": "先頭0保持",
                        "description": "コード系フィールドは先頭0を保持してTEXT型に",
                        "pattern": r"^0\d+$",
                        "action": "type_change",
                        "target_type": "TEXT",
                        "confidence_threshold": 0.8,
                        "field_patterns": [".*コード.*", ".*番号.*", ".*ID.*", ".*CODE.*"]
                    },
                    {
                        "rule_id": "alphanumeric_code",
                        "name": "英数字コード",
                        "description": "英数字混在コードをTEXT型に設定",
                        "pattern": r"^[A-Za-z0-9]+$",
                        "action": "type_change",
                        "target_type": "TEXT",
                        "confidence_threshold": 0.9,
                        "field_patterns": [".*コード.*", ".*ID.*", ".*CODE.*"]
                    }
                ]
            }
        }
        self.save_templates()
    
    def save_templates(self) -> None:
        """テンプレートをファイルに保存"""
        try:
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"テンプレート保存エラー: {e}")
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """指定されたテンプレートを取得"""
        return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """利用可能なテンプレート名一覧を取得"""
        return list(self.templates.keys())
    
    def create_rules_from_template(self, template_name: str) -> List[ModificationRule]:
        """テンプレートから修正ルールを作成"""
        template = self.get_template(template_name)
        if not template:
            return []
        
        rules = []
        for rule_data in template.get("rules", []):
            try:
                rule = ModificationRule(
                    rule_id=rule_data["rule_id"],
                    name=rule_data["name"],
                    description=rule_data["description"],
                    pattern=rule_data["pattern"],
                    action=ModificationAction(rule_data["action"]),
                    target_type=FieldType(rule_data["target_type"]),
                    confidence_threshold=rule_data["confidence_threshold"]
                )
                rules.append(rule)
            except Exception as e:
                print(f"ルール作成エラー ({rule_data.get('rule_id', 'unknown')}): {e}")
        
        return rules
    
    def add_custom_template(self, template_name: str, template_data: Dict) -> None:
        """カスタムテンプレートを追加"""
        self.templates[template_name] = template_data
        self.save_templates()
    
    def validate_rule_pattern(self, pattern: str, test_data: List[str]) -> Dict[str, Any]:
        """ルールパターンの妥当性を検証"""
        try:
            compiled_pattern = re.compile(pattern)
            matches = []
            non_matches = []
            
            for data in test_data:
                if compiled_pattern.match(str(data)):
                    matches.append(data)
                else:
                    non_matches.append(data)
            
            match_rate = len(matches) / len(test_data) if test_data else 0
            
            return {
                "valid": True,
                "match_rate": match_rate,
                "matches": matches[:10],  # 最初の10件
                "non_matches": non_matches[:10],  # 最初の10件
                "total_tested": len(test_data)
            }
        
        except re.error as e:
            return {
                "valid": False,
                "error": str(e),
                "match_rate": 0,
                "matches": [],
                "non_matches": [],
                "total_tested": 0
            }
    
    def suggest_rules_for_field(self, field_name: str, sample_data: List[str]) -> List[Dict]:
        """フィールド名とサンプルデータから適用可能なルールを提案"""
        suggestions = []
        
        for template_name, template in self.templates.items():
            for rule_data in template.get("rules", []):
                # フィールド名パターンチェック
                field_match = False
                for field_pattern in rule_data.get("field_patterns", []):
                    if re.search(field_pattern, field_name, re.IGNORECASE):
                        field_match = True
                        break
                
                if field_match:
                    # データパターンチェック
                    validation = self.validate_rule_pattern(rule_data["pattern"], sample_data)
                    
                    if validation["valid"] and validation["match_rate"] > 0.5:
                        suggestions.append({
                            "template": template_name,
                            "rule": rule_data,
                            "match_rate": validation["match_rate"],
                            "confidence": min(validation["match_rate"], rule_data["confidence_threshold"])
                        })
        
        # 信頼度順でソート
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)
        return suggestions

def main():
    """テスト実行"""
    manager = RuleTemplateManager()
    
    print("=== 修正ルールテンプレート管理システム ===")
    print(f"利用可能なテンプレート: {manager.list_templates()}")
    
    # SAPデータクリーニングルールを作成
    sap_rules = manager.create_rules_from_template("sap_data_cleaning")
    print(f"\nSAPデータクリーニングルール: {len(sap_rules)}件")
    for rule in sap_rules:
        print(f"  - {rule.name}: {rule.description}")
    
    # フィールド提案テスト
    test_field = "受注伝票番号"
    test_data = ["0000123456", "0000789012", "0001234567"]
    suggestions = manager.suggest_rules_for_field(test_field, test_data)
    
    print(f"\n'{test_field}'フィールドへの提案:")
    for suggestion in suggestions:
        print(f"  - {suggestion['rule']['name']}: 信頼度{suggestion['confidence']:.2f}")

if __name__ == "__main__":
    main()