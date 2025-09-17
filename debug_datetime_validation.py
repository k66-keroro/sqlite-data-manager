#!/usr/bin/env python3
"""
日付妥当性チェックのデバッグ
"""

from pattern_rules import TypeCorrectionRules
import re

def debug_datetime_validation():
    """日付妥当性チェックの問題を調査"""
    
    print("=== 日付妥当性チェック デバッグ ===")
    
    corrector = TypeCorrectionRules()
    
    # テストデータ
    test_dates = [
        "20240101", "20240202", "20240303",  # YYYYMMDD形式
        "2024/01/01", "2024/02/02", "2024/03/03",  # YYYY/MM/DD形式
        "2024-01-01", "2024-02-02", "2024-03-03",  # YYYY-MM-DD形式
        "",  # 空文字
        "invalid_date",  # 無効な日付
    ]
    
    print("1. パターンマッチングテスト:")
    patterns = corrector._rules_data['datetime_patterns']
    for date_str in test_dates:
        print(f"\n  テスト日付: '{date_str}'")
        for pattern in patterns:
            if re.match(pattern, date_str):
                print(f"    ✓ パターン {pattern} にマッチ")
                
                # _is_valid_dateメソッドをテスト
                is_valid = corrector._is_valid_date(date_str)
                print(f"    妥当性チェック: {is_valid}")
                
                if not is_valid:
                    # どのフォーマットで失敗しているかチェック
                    formats = corrector._rules_data.get('datetime_formats', [])
                    print(f"    試行フォーマット: {formats}")
                    
                    from datetime import datetime
                    for fmt in formats:
                        try:
                            result = datetime.strptime(date_str, fmt)
                            print(f"      ✓ フォーマット {fmt} で成功: {result}")
                        except ValueError as e:
                            print(f"      ✗ フォーマット {fmt} で失敗: {e}")
                break
        else:
            print(f"    ✗ どのパターンにもマッチしない")
    
    print("\n2. enhance_datetime_detection の詳細テスト:")
    
    # 実際のenhance_datetime_detectionメソッドを詳細にテスト
    sample_data = ["20240101", "20240202", "20240303", "20240404", "20240505"]
    
    print(f"  サンプルデータ: {sample_data}")
    
    # メソッド内部の処理を手動で実行
    datetime_match_count = 0
    total_samples = len(sample_data)
    
    for value in sample_data:
        value_str = str(value).strip()
        print(f"\n  処理中: '{value_str}'")
        
        # 各日付パターンでチェック
        for pattern in patterns:
            if re.match(pattern, value_str):
                print(f"    パターンマッチ: {pattern}")
                # さらに実際の日付として有効かチェック
                if corrector._is_valid_date(value_str):
                    datetime_match_count += 1
                    print(f"    ✓ 妥当性チェック成功")
                    break
                else:
                    print(f"    ✗ 妥当性チェック失敗")
                    break
    
    match_ratio = datetime_match_count / total_samples
    print(f"\n  マッチ率: {datetime_match_count}/{total_samples} = {match_ratio:.1%}")
    print(f"  閾値: 80%")
    print(f"  結果: {'DATETIME' if match_ratio >= 0.8 else 'TEXT'}")

if __name__ == "__main__":
    debug_datetime_validation()