#!/usr/bin/env python3
"""
T001: compare_report.csv詳細分析ツール

Type推定の問題を詳細に調査し、修正方針を決定する
"""

import pandas as pd
import os
import numpy as np
from config import OUTPUT_DIR

def analyze_compare_report():
    """compare_report.csvの詳細分析を実行"""
    
    print(" T001: compare_report.csv 詳細分析開始")
    print("=" * 60)
    
    # ファイル読み込み
    compare_file = os.path.join(OUTPUT_DIR, 'compare_report.csv')
    if not os.path.exists(compare_file):
        print(f" compare_report.csvが見つかりません: {compare_file}")
        return
    
    df = pd.read_csv(compare_file, encoding='utf-8')
    
    # 基本情報
    print(f" 基本情報")
    print(f"  総フィールド数: {len(df):,}")
    print(f"  処理ファイル数: {df['File'].nunique()}")
    print(f"  ユニーク列名数: {df['Column'].nunique()}")
    print()
    
    # 重大な問題：Actual_Typeの調査
    print(f" 重大な問題発見")
    print(f"  Actual_Type の分布:")
    actual_types = df['Actual_Type'].value_counts()
    for dtype, count in actual_types.items():
        print(f"    {dtype}: {count:,} ({count/len(df)*100:.1f}%)")
    print()
    
    if len(actual_types) == 1 and 'TEXT' in actual_types.index:
        print("    全てのActual_TypeがTEXTになっています！")
        print("   型推定ロジックに致命的な問題があります")
        print()
    
    # 型一致率の詳細
    print(f" 型一致状況")
    match_dist = df['Match'].value_counts()
    total = len(df)
    match_rate = (df['Match'] == '○').sum() / total * 100
    print(f"  一致: {match_dist.get('○', 0):,} ({match_dist.get('○', 0)/total*100:.1f}%)")
    print(f"  不一致: {match_dist.get('×', 0):,} ({match_dist.get('×', 0)/total*100:.1f}%)")
    print(f"  一致率: {match_rate:.1f}%")
    print()
    
    # 推定型の分布
    print(f" 推定型の分布")
    inferred_dist = df['Inferred_Type'].value_counts()
    for dtype, count in inferred_dist.items():
        print(f"  {dtype}: {count:,} ({count/len(df)*100:.1f}%)")
    print()
    
    # ファイル別分析
    print(f" ファイル別分析（上位10件）")
    file_analysis = df.groupby('File').agg({
        'Column': 'count',
        'Match': lambda x: (x == '○').sum(),
        'Encoding': lambda x: x.iloc[0],
        'Delimiter': lambda x: x.iloc[0]
    }).rename(columns={'Column': 'total_fields', 'Match': 'matched_fields'})
    
    file_analysis['match_rate'] = file_analysis['matched_fields'] / file_analysis['total_fields'] * 100
    file_analysis = file_analysis.sort_values('match_rate')
    
    print("  ワースト10ファイル (一致率順):")
    for file, row in file_analysis.head(10).iterrows():
        print(f"    {file[:30]:30} | {row['matched_fields']:3}/{row['total_fields']:3} ({row['match_rate']:5.1f}%) | {row['Encoding']} | {row['Delimiter']}")
    print()
    
    # 型不一致パターンの詳細
    print(f" 型不一致パターンの詳細")
    mismatch_df = df[df['Match'] != '○']
    if len(mismatch_df) > 0:
        patterns = mismatch_df.groupby(['Inferred_Type', 'Actual_Type']).size().sort_values(ascending=False)
        print("  主要な不一致パターン:")
        for (inferred, actual), count in patterns.head(15).items():
            print(f"    {inferred:12}  {actual:12}: {count:4,} フィールド ({count/len(mismatch_df)*100:5.1f}%)")
    print()
    
    # SAPデータ特殊パターンの検出
    print(f" SAPデータ特殊パターンの検出")
    # 0パディング可能性
    zero_padding_candidates = df[
        (df['Column'].str.contains('CODE|CD|NO|NUM', case=False, na=False)) &
        (df['Inferred_Type'] == 'TEXT')
    ]
    print(f"  0パディング候補: {len(zero_padding_candidates)} フィールド")
    
    # 後ろマイナス可能性（数値だが推定がTEXTのもの）
    minus_candidates = df[
        (df['Inferred_Type'] != 'TEXT') & 
        (df['Actual_Type'] == 'TEXT')
    ]
    print(f"  後ろマイナス候補: {len(minus_candidates)} フィールド")
    print()
    
    # エンコーディング・区切り文字分析
    print(f" ファイル形式分析")
    print("  エンコーディング分布:")
    enc_dist = df['Encoding'].value_counts()
    for enc, count in enc_dist.items():
        unique_files = df[df['Encoding'] == enc]['File'].nunique()
        print(f"    {enc:10}: {count:4,} フィールド ({unique_files} ファイル)")
    
    print("  区切り文字分布:")
    delim_dist = df['Delimiter'].value_counts()
    for delim, count in delim_dist.items():
        unique_files = df[df['Delimiter'] == delim]['File'].nunique()
        delim_display = repr(delim) if delim in ['\t', '\n', '\r'] else delim
        print(f"    {delim_display:10}: {count:4,} フィールド ({unique_files} ファイル)")
    print()
    
    # 重複フィールド名の検出
    print(f" 重複フィールド名の検出")
    column_counts = df['Column'].value_counts()
    duplicates = column_counts[column_counts > 1]
    
    print(f"  重複フィールド名数: {len(duplicates)}")
    if len(duplicates) > 0:
        print("  上位重複フィールド:")
        for col, count in duplicates.head(10).items():
            files_with_col = df[df['Column'] == col]['File'].nunique()
            print(f"    {col:30}: {count:3} 回出現 ({files_with_col} ファイル)")
    print()
    
    # 推奨アクション
    print(f" 推奨アクション")
    print("  1.  緊急: Actual_Type推定ロジックの修正")
    print("      analyzer.py の型推定関数を確認")
    print("      実際のデータサンプルでテスト")
    print()
    print("  2.  SAPデータ特殊ルールの実装")
    print(f"      0パディング候補: {len(zero_padding_candidates)} フィールド")
    print(f"      後ろマイナス候補: {len(minus_candidates)} フィールド")
    print()
    print("  3.  重複フィールドの統合計画")
    print(f"      重複フィールド: {len(duplicates)} 種類")
    print()
    print("  4. 🧪 段階的修正の実施")
    print("      まず1ファイルでテスト")
    print("      成功後に全体適用")
    
    print("\n" + "=" * 60)
    print(" T001分析完了 - 次のタスク: analyzer.py の型推定ロジック調査")


if __name__ == "__main__":
    analyze_compare_report()
