#!/usr/bin/env python3
"""
T002修正ルール適用テスト
analyzer.pyの修正版での型推定を検証
"""

import sys
import os
import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(os.getcwd())

from analyzer import infer_sqlite_type

def test_t002_corrections():
    """T002修正ルールのテスト"""
    
    print("=== T002修正ルール適用テスト ===\n")
    
    # テスト1: 保管場所コード（zm114.txt）
    print("[TEST1] 保管場所コード修正")
    storage_data = pd.Series(['1001', '1002', '2001', '3001'])
    result1_old = infer_sqlite_type(storage_data, '保管場所')  # ファイル名なし（旧ロジック）
    result1_new = infer_sqlite_type(storage_data, '保管場所', 'zm114.txt')  # T002修正適用
    print(f"  旧: {result1_old} → 新: {result1_new}")
    print(f"  判定: {'✅ 修正適用' if result1_new == 'TEXT' else '❌ 修正失敗'}")
    print()
    
    # テスト2: 原価フィールド
    print("[TEST2] 原価フィールド修正")  
    price_data = pd.Series(['1500', '2000', '3500', '1200'])
    result2_old = infer_sqlite_type(price_data, '製品原価')
    result2_new = infer_sqlite_type(price_data, '製品原価', 'pricing.txt')
    print(f"  旧: {result2_old} → 新: {result2_new}")
    print(f"  判定: {'✅ 修正適用' if result2_new in ['INTEGER', 'REAL'] else '❌ 修正失敗'}")
    print()
    
    # テスト3: 日付フィールド強化
    print("[TEST3] DATETIME検出強化")
    date_data = pd.Series(['20240101', '20240102', '20240103', '20240104'])
    result3_old = infer_sqlite_type(date_data, '売上日')
    result3_new = infer_sqlite_type(date_data, '売上日', 'sales.txt')
    print(f"  旧: {result3_old} → 新: {result3_new}")
    print(f"  判定: {'✅ 修正適用' if result3_new == 'DATETIME' else '❌ 修正失敗'}")
    print()
    
    # テスト4: 特殊ファイル（zs65.txt）
    print("[TEST4] 特殊ファイル処理")
    special_data = pd.Series(['A001', 'B002', 'C003'])
    result4_old = infer_sqlite_type(special_data, 'コード')
    result4_new = infer_sqlite_type(special_data, 'コード', 'zs65.txt')
    print(f"  旧: {result4_old} → 新: {result4_new}")
    print(f"  判定: {'✅ 修正適用' if result4_new == 'TEXT' else '❌ 修正失敗'}")
    print()
    
    # テスト5: INTEGER → TEXT の具体例
    print("[TEST5] INTEGER→TEXT 問題フィールド")
    amount_data = pd.Series([1500, 2000, 3500])  # 実際の数値データ
    result5_old = infer_sqlite_type(amount_data, '数量')
    result5_new = infer_sqlite_type(amount_data, '購入数量', 'purchase.txt')
    print(f"  旧: {result5_old} → 新: {result5_new}")
    print(f"  判定: {'✅ 数量フィールド検出' if result5_new in ['INTEGER', 'REAL'] else '❌ 検出失敗'}")
    print()
    
    print("T002修正ルールテスト完了！")

if __name__ == "__main__":
    test_t002_corrections()
