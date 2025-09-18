#!/usr/bin/env python3
"""
zs65ファイルのanalyzer.py処理をテスト
"""

import os
import pandas as pd
from pattern_rules import TypeCorrectionRules
from config import DATA_DIR

def test_zs65_analyzer():
    """zs65ファイルのanalyzer.py処理をテスト"""
    
    print("=== zs65ファイルのanalyzer.py処理テスト ===")
    
    # TypeCorrectionRulesを読み込み
    corrector = TypeCorrectionRules()
    unregistered_rules = corrector._rules_data.get('unregistered_files', {})
    
    print("未登録ファイルルール:")
    for file_name, rule in unregistered_rules.items():
        if 'zs65' in file_name:
            print(f"  {file_name}: {rule}")
    
    # 実際にzs65.txtを処理
    file_name = 'zs65.txt'
    file_path = os.path.join(DATA_DIR, file_name)
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        return
    
    print(f"\n--- {file_name}の処理テスト ---")
    
    # 未登録ファイルルールを適用
    if file_name in unregistered_rules:
        rule = unregistered_rules[file_name]
        enc, delimiter = rule['encoding'], rule['separator']
        print(f"未登録ファイルルール適用: encoding={enc}, delimiter='{delimiter}'")
        
        try:
            df = pd.read_csv(
                file_path, 
                delimiter=delimiter, 
                dtype=str, 
                nrows=5, 
                encoding=enc, 
                engine="python"
            )
            
            print(f"読み込み成功: shape={df.shape}")
            print(f"列名: {list(df.columns[:10])}")
            
            # 数値っぽい列を特定
            numeric_columns = []
            for col in df.columns:
                if any(keyword in col for keyword in ['数量', '在庫', '値', '金額', '日数']):
                    numeric_columns.append(col)
            
            print(f"数値っぽい列: {numeric_columns[:5]}")
            
            # 実際のデータサンプルを確認
            if numeric_columns:
                for col in numeric_columns[:3]:
                    sample_data = df[col].dropna().head(3).tolist()
                    print(f"  {col}: {sample_data}")
            
        except Exception as e:
            print(f"読み込み失敗: {e}")
    else:
        print("未登録ファイルルールが見つかりません")

if __name__ == "__main__":
    test_zs65_analyzer()