#!/usr/bin/env python3
"""
T002 Analyzer: データ型修正サポートツール
4つの問題パターンを詳細分析し、修正ルールを特定する
"""

import pandas as pd
import os
import sys
from collections import defaultdict, Counter

def analyze_compare_report(csv_path):
    """compare_report.csvの詳細分析"""
    
    print("=== T002: データ型問題パターン分析 ===\n")
    
    if not os.path.exists(csv_path):
        print(f"❌ compare_report.csv が見つかりません: {csv_path}")
        return
    
    df = pd.read_csv(csv_path)
    total_records = len(df)
    mismatches = df[df['Inferred_Type'] != df['Actual_Type']]
    mismatch_count = len(mismatches)
    
    print(f"[DATA] 総レコード数: {total_records:,}")
    print(f"[DATA] 不一致件数: {mismatch_count:,} ({mismatch_count/total_records*100:.1f}%)")
    print()
    
    # === 問題1: 未登録型パターン ===
    print("[ISSUE1] Inferred_Type = '未登録' の分析")
    unregistered = df[df['Inferred_Type'] == '未登録']
    print(f"   件数: {len(unregistered)} 件")
    
    if len(unregistered) > 0:
        print("   ファイル別内訳:")
        file_counts = unregistered['File'].value_counts()
        for file_name, count in file_counts.items():
            print(f"     {file_name}: {count}件")
        
        print("   フィールド名パターン (上位10件):")
        field_counts = unregistered['Column'].value_counts().head(10)
        for field, count in field_counts.items():
            print(f"     {field}: {count}件")
    print()
    
    # === 問題2: DATETIME → TEXT 変換問題 ===
    print("[ISSUE2] DATETIME -> TEXT 変換問題")
    datetime_to_text = df[(df['Inferred_Type'] == 'DATETIME') & (df['Actual_Type'] == 'TEXT')]
    datetime_to_datetime = df[(df['Inferred_Type'] == 'DATETIME') & (df['Actual_Type'] == 'DATETIME')]
    
    print(f"   DATETIME→TEXT: {len(datetime_to_text)} 件")
    print(f"   DATETIME→DATETIME: {len(datetime_to_datetime)} 件")
    print(f"   正解率: {len(datetime_to_datetime)/(len(datetime_to_text)+len(datetime_to_datetime))*100:.1f}%")
    
    if len(datetime_to_text) > 0:
        print("   失敗ファイル (上位5件):")
        for file_name, count in datetime_to_text['File'].value_counts().head(5).items():
            print(f"     {file_name}: {count}件")
    print()
    
    # === 問題3: INTEGER判定問題 ===
    print("[ISSUE3] INTEGER判定問題")
    int_to_text = df[(df['Inferred_Type'] == 'INTEGER') & (df['Actual_Type'] == 'TEXT')]
    int_to_int = df[(df['Inferred_Type'] == 'INTEGER') & (df['Actual_Type'] == 'INTEGER')]
    text_to_int = df[(df['Inferred_Type'] == 'TEXT') & (df['Actual_Type'] == 'INTEGER')]
    
    print(f"   INTEGER→TEXT: {len(int_to_text)} 件 (本来INTEGER)")
    print(f"   INTEGER→INTEGER: {len(int_to_int)} 件 (正解)")
    print(f"   TEXT→INTEGER: {len(text_to_int)} 件 (本来TEXT)")
    
    if len(int_to_text) > 0:
        print("   INTEGER→TEXT フィールド名パターン (原価・単価系チェック):")
        suspect_fields = []
        for field in int_to_text['Column'].values:
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in ['原価', '単価', 'genka', 'tanka', 'price', 'cost', 'amount']):
                suspect_fields.append(field)
        
        if suspect_fields:
            suspect_counts = Counter(suspect_fields)
            for field, count in suspect_counts.most_common(5):
                print(f"     {field}: {count}件 [WARNING]")
        else:
            print("     原価・単価系フィールドは検出されませんでした")
    print()
    
    # === 問題4: 保管場所コード問題 ===
    print("[ISSUE4] 保管場所コード問題")
    storage_issues = df[
        (df['File'].str.contains('zm114', case=False, na=False)) &
        (df['Column'].str.contains('保管場所', case=False, na=False)) &
        (df['Inferred_Type'] == 'INTEGER')
    ]
    
    print(f"   zm114.txtの保管場所フィールド: {len(storage_issues)} 件")
    if len(storage_issues) > 0:
        for _, row in storage_issues.iterrows():
            print(f"     {row['File']}: {row['Column']} ({row['Inferred_Type']}→{row['Actual_Type']})")
    print()
    
    # === 全体的な改善提案 ===
    print("[SOLUTION] 改善提案")
    print("1. 未登録型対策:")
    print("   - 特殊ファイル形式の前処理ルール追加")
    print("   - エンコーディング・区切り文字の自動検出強化")
    
    print("2. DATETIME検出強化:")
    print("   - SAP日付形式の詳細パターン追加")
    print("   - 日付候補の厳格な検証ロジック実装")
    
    print("3. INTEGER/TEXT判定改善:")
    print("   - ビジネスロジック判定の実装")
    print("   - フィールド名による型推論ルール追加")
    
    print("4. コードフィールド識別:")
    print("   - 保管場所等のコード性質フィールドをTEXT扱い")
    print("   - 数値のみでもコードはTEXTルール実装")
    
    return {
        'total_records': total_records,
        'mismatch_count': mismatch_count,
        'unregistered_count': len(unregistered),
        'datetime_text_count': len(datetime_to_text),
        'integer_text_count': len(int_to_text),
        'storage_issues_count': len(storage_issues)
    }

def generate_fix_rules(analysis_result):
    """分析結果に基づく修正ルール生成"""
    
    print("\n=== T002: 修正ルール生成 ===")
    
    rules = {
        'unregistered_files': [
            '払出明細（大阪）_ZPR01201.txt',
            '払出明細（滋賀）_ZPR01201.txt', 
            'zs65.txt',
            'zs65_sss.txt'
        ],
        'datetime_patterns': [
            r'^\d{8}$',  # YYYYMMDD
            r'^\d{4}/\d{2}/\d{2}$',  # YYYY/MM/DD
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}\.\d{2}\.\d{4}$'  # DD.MM.YYYY
        ],
        'business_logic_fields': {
            'code_fields': ['保管場所', 'warehouse', 'storage', 'location'],
            'price_fields': ['原価', '単価', 'genka', 'tanka', 'price', 'cost', 'amount']
        }
    }
    
    print("[RULES] 生成された修正ルール:")
    print(f"   未登録対象ファイル: {len(rules['unregistered_files'])} 件")
    print(f"   日付パターン: {len(rules['datetime_patterns'])} 種類")
    print(f"   ビジネスロジック: {len(rules['business_logic_fields'])} カテゴリ")
    
    return rules

if __name__ == "__main__":
    # compare_report.csvのパス
    csv_path = "C:/Projects_workspace/03_python/output/compare_report.csv"
    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    
    # 分析実行
    analysis_result = analyze_compare_report(csv_path)
    
    if analysis_result:
        # 修正ルール生成
        fix_rules = generate_fix_rules(analysis_result)
        
        print(f"\n[COMPLETE] T002分析完了！")
        print(f"   対象: {analysis_result['mismatch_count']:,} 件の不一致を改善予定")
