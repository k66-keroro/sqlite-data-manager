#!/usr/bin/env python3
"""
Pattern Rules for T002: データ型修正ルール実装
4つの問題パターンに対する自動修正ルールを提供
"""

import re
import pandas as pd
from datetime import datetime
import logging
import json
import os

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TypeCorrectionRules:
    """データ型修正ルールのメインクラス"""
    
    def __init__(self):
        """修正ルールの初期化"""
        self.rules_file = "pattern_rules_data.json"
        self._load_rules_data()

    def _load_rules_data(self):
        """JSONファイルからルールデータをロードする"""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                self._rules_data = json.load(f)
            logger.info(f"ルールデータを {self.rules_file} からロードしました。")
        else:
            # ファイルが存在しない場合はデフォルト値を設定し、保存する
            self._rules_data = {
                "unregistered_files": {
                    '払出明細（大阪）_ZPR01201.txt': {'encoding': 'shift_jis', 'separator': '\t'},
                    '払出明細（滋賀）_ZPR01201.txt': {'encoding': 'shift_jis', 'separator': '\t'},
                    'zs65.txt': {'encoding': 'utf-8', 'separator': '\t'},
                    'zs65_sss.txt': {'encoding': 'utf-8', 'separator': '\t'}
                },
                "datetime_patterns": [
                    r'^\d{8}$',
                    r'^\d{4}/\d{2}/\d{2}$',
                    r'^\d{4}-\d{2}-\d{2}$',
                    r'^\d{2}\.\d{2}\.\d{4}$',
                    r'^\d{4}\d{2}\d{2}$',
                    r'^\d{2}/\d{2}/\d{4}$',
                    r'^\d{4}\.\d{2}\.\d{2}$'
                ],
                "datetime_formats": [
                    "%Y%m%d",
                    "%Y/%m/%d",
                    "%Y-%m-%d",
                    "%d.%m.%Y",
                    "%m/%d/%Y",
                    "%Y.%m.%d"
                ],
                "business_logic_rules": {
                    'code_fields': [
                        '保管場所', 'warehouse', 'storage', 'location',
                        '得意先', 'customer', 'client', 'shop',
                        '品目', 'item', 'material', 'product',
                        '工場', 'plant', 'factory', 'site',
                        '会社', 'company', 'comp'
                    ],
                    'amount_fields': [
                        '原価', '単価', 'genka', 'tanka', 'price', 'cost', 'amount',
                        '金額', 'kingaku', '価格', 'kakaku', '値段', 'nedan',
                        '料金', 'ryoukin', 'fee', 'charge'
                    ],
                    'quantity_fields': [
                        '数量', 'suuryou', 'qty', 'quantity', 'amount',
                        '個数', 'kosuu', 'count', 'number',
                        '重量', 'juuryou', 'weight', 'wt'
                    ]
                },
                "sap_patterns": {
                    'trailing_minus': r'^(\d+)-$' ,
                    'zero_padding': r'^0+(\d+)$' ,
                    'decimal_comma': r'^(\d+),(\d+)$'
                }
            }
            self._save_rules_data()
            logger.info(f"デフォルトのルールデータを {self.rules_file} に保存しました。")

    def _save_rules_data(self):
        """ルールデータをJSONファイルに保存する"""
        with open(self.rules_file, 'w', encoding='utf-8') as f:
            json.dump(self._rules_data, f, indent=2, ensure_ascii=False)
        logger.info(f"ルールデータを {self.rules_file} に保存しました。")
    
    def apply_file_specific_rules(self, file_name, data_sample):
        """ファイル固有のルール適用"""
        
        if file_name in self._rules_data['unregistered_files']:
            logger.info(f"特殊ファイル処理: {file_name}")
            rules = self._rules_data['unregistered_files'][file_name]
            
            # 特殊ファイルの場合、基本的にすべてTEXT扱い
            # ただし明らかに数値・日付の列は適切に判定
            return {
                'default_type': 'TEXT',
                'encoding': rules['encoding'],
                'separator': rules['separator']
            }
        
        return None
    
    def enhance_datetime_detection(self, column_data, column_name):
        """DATETIME検出の強化"""
        
        if column_data is None or len(column_data) == 0:
            return 'TEXT'
        
        # サンプルデータの取得（空でない値のみ）
        sample_values = [str(v) for v in column_data if pd.notna(v) and str(v).strip() != '']
        
        if not sample_values:
            return 'TEXT'
        
        # 日付パターンマッチング
        datetime_match_count = 0
        total_samples = min(len(sample_values), 100)  # 最大100サンプル
        
        for value in sample_values[:total_samples]:
            value_str = str(value).strip()
            
            # 各日付パターンでチェック
            for pattern in self._rules_data['datetime_patterns']:
                if re.match(pattern, value_str):
                    # さらに実際の日付として有効かチェック
                    if self._is_valid_date(value_str):
                        datetime_match_count += 1
                        break
        
        # 80%以上が日付パターンにマッチした場合はDATETIME
        match_ratio = datetime_match_count / total_samples
        
        if match_ratio >= 0.8:
            logger.info(f"DATETIME検出強化: {column_name} ({match_ratio:.1%} マッチ)")
            return 'DATETIME'
        
        return None  # 判定なし（他のロジックに委ねる）
    
    def _is_valid_date(self, date_string):
        """日付文字列の妥当性チェック"""
        
        # 設定ファイルから日付フォーマットのリストを読み込む
        date_formats = self._rules_data.get('datetime_formats', [])
        
        for fmt in date_formats:
            try:
                datetime.strptime(date_string, fmt)
                return True
            except ValueError:
                continue
        
        return False
    
    def apply_business_logic(self, column_name, column_data, inferred_type):
        """ビジネスロジックによる型判定"""
        
        column_lower = column_name.lower()
        
        # コードフィールドの判定
        for code_pattern in self._rules_data['business_logic_rules']['code_fields']:
            if code_pattern in column_lower:
                logger.info(f"コードフィールド検出: {column_name} → TEXT")
                return 'TEXT'
        
        # 金額フィールドの判定
        for amount_pattern in self._rules_data['business_logic_rules']['amount_fields']:
            if amount_pattern in column_lower:
                # 小数点を含むかチェック
                sample_values = [str(v) for v in column_data if pd.notna(v)][:50]
                has_decimal = any('.' in str(v) or ',' in str(v) for v in sample_values)
                
                result_type = 'REAL' if has_decimal else 'INTEGER'
                logger.info(f"金額フィールド検出: {column_name} → {result_type}")
                return result_type
        
        # 数量フィールドの判定
        for qty_pattern in self._rules_data['business_logic_rules']['quantity_fields']:
            if qty_pattern in column_lower:
                # 小数点を含むかチェック
                sample_values = [str(v) for v in column_data if pd.notna(v)][:50]
                has_decimal = any('.' in str(v) or ',' in str(v) for v in sample_values)
                
                result_type = 'REAL' if has_decimal else 'INTEGER'
                logger.info(f"数量フィールド検出: {column_name} → {result_type}")
                return result_type
        
        return None  # ビジネスロジック判定なし
    
    def normalize_sap_data(self, value):
        """SAPデータの正規化"""
        
        if pd.isna(value):
            return value
        
        value_str = str(value).strip()
        
        # 後ろマイナスの処理
        minus_match = re.match(self._rules_data['sap_patterns']['trailing_minus'], value_str)
        if minus_match:
            return f"-{minus_match.group(1)}"
        
        # ゼロパディングの処理（ただしコードフィールドは除く）
        zero_match = re.match(self._rules_data['sap_patterns']['zero_padding'], value_str)
        if zero_match and len(value_str) > 3:  # 3桁以上のゼロパディングのみ
            return zero_match.group(1)
        
        # カンマ小数点の処理
        comma_match = re.match(self._rules_data['sap_patterns']['decimal_comma'], value_str)
        if comma_match:
            return f"{comma_match.group(1)}.{comma_match.group(2)}"
        
        return value_str
    
    def correct_type(self, file_name, column_name, column_data, original_inferred_type):
        """総合的な型修正判定"""
        
        logger.info(f"型修正判定: {file_name}:{column_name} (初期推定: {original_inferred_type})")
        
        # 1. t002_loader_updates.jsonからのオーバーライドを最優先でチェック
        #    (loader.pyが生成するt002_loader_updates.jsonを読み込む想定)
        #    ここでは、analyzer.pyがTypeCorrectionRulesを呼び出す際に、
        #    t002_loader_updates.jsonのルールを適用するロジックは含まれていないため、
        #    この部分はコメントアウトまたは別の方法で処理する必要があります。
        #    現在のanalyzer.pyのロジックでは、t002_loader_updates.jsonはloader.pyで読み込まれます。
        #    ここでは、pattern_rules.jsonにルールを生成するための判定を行います。

        # 2. ファイル固有ルール (未登録ファイルなど)
        file_rules = self.apply_file_specific_rules(file_name, column_data)
        if file_rules and file_rules.get('default_type'):
            logger.info(f"ファイル固有ルール適用: {column_name} → {file_rules['default_type']}")
            return file_rules['default_type']
        
        # 3. ビジネスロジック適用 (コード、金額、数量など)
        business_result = self.apply_business_logic(column_name, column_data, original_inferred_type)
        if business_result:
            logger.info(f"ビジネスロジック適用: {column_name} → {business_result}")
            return business_result

        # 4. DATETIME検出強化 (初期推定がDATETIMEでない場合にのみ適用)
        #    t002_pattern_fixer.pyがDATETIME→TEXTのルールを生成するために、
        #    ここではDATETIMEと推定されたものをそのまま返す。
        #    DATETIME→TEXTへの強制変換はt002_loader_updates.jsonの役割。
        datetime_result = self.enhance_datetime_detection(column_data, column_name)
        if datetime_result == 'DATETIME' and original_inferred_type != 'DATETIME':
            logger.info(f"DATETIME検出強化: {column_name} → DATETIME")
            return 'DATETIME'
        
        # 5. その他の修正ルールがない場合、元の推定を維持
        return original_inferred_type


# 使用例とテスト用関数
def test_correction_rules():
    """修正ルールのテスト実行"""
    
    print("=== T002 Pattern Rules テスト ===\n")
    
    corrector = TypeCorrectionRules()
    
    # テストケース1: 保管場所コード
    test_data1 = pd.Series(['1001', '1002', '2001', '3001'])
    result1 = corrector.correct_type('zm114.txt', '保管場所', test_data1, 'INTEGER')
    print(f"テスト1 - 保管場所: INTEGER → {result1}")
    
    # テストケース2: 原価フィールド
    test_data2 = pd.Series([1500, 2000, 3500, 1200])
    result2 = corrector.correct_type('pricing.txt', '製品原価', test_data2, 'TEXT')
    print(f"テスト2 - 製品原価: TEXT → {result2}")
    
    # テストケース3: 日付フィールド
    test_data3 = pd.Series(['20240101', '20240102', '20240103'])
    result3 = corrector.correct_type('sales.txt', '売上日付', test_data3, 'TEXT')
    print(f"テスト3 - 売上日付: TEXT → {result3}")
    
    # テストケース4: 特殊ファイル
    test_data4 = pd.Series(['A001', 'B002', 'C003'])
    result4 = corrector.correct_type('zs65.txt', 'コード', test_data4, 'INTEGER')
    print(f"テスト4 - 特殊ファイル: INTEGER → {result4}")
    
    print("\n修正ルール実装完了！")

if __name__ == "__main__":
    test_correction_rules()
