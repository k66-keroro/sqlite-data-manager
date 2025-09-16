#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
T002 - データ型修正パターン対応ツール

4つの特定された問題パターンの修正ルールを実装:
1. Inferred_Type_未登録 (4ファイル、実質2パターン)
2. Inferred_Type_DATETIME→TEXT修正必要
3. Inferred_Type_INTEGER→TEXT修正必要  
4. 保管場所コード問題（zm114.txt）

作成日: 2024-09-10
"""

import pandas as pd
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any
import logging
import os # 追加
import sqlite3 # 追加
from config import OUTPUT_DIR # 追加

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class T002PatternFixer:
    """T002問題パターン修正クラス"""
    
    def __init__(self, db_file: str = os.path.join(OUTPUT_DIR, "master.db")):
        """
        初期化
        
        Args:
            db_file: SQLiteデータベースファイルのパス
        """
        self.db_file = db_file
        self.pattern_rules = self._load_pattern_rules()
        self.df_compare = None
        
    def _load_pattern_rules(self) -> Dict[str, Any]:
        """修正パターンルールを読み込み"""
        pattern_rules = {
            # パターン1: 未登録型修正
            "unregistered_types": {
                "files": [
                    "払出明細（大阪）_ZPR01201.txt",
                    "払出明細（滋賀）_ZPR01201.txt", 
                    "zs65.txt",
                    "zs65_sss.txt"
                ],
                "rule": "register_missing_fields"
            },
            
            # パターン2: DATETIME→TEXT修正
            "datetime_to_text": {
                "condition": {
                    "inferred_type": "DATETIME",
                    "actual_type_text_ratio": "> 50"
                },
                "action": "change_to_text"
            },
            
            # パターン3: INTEGER→TEXT修正（特定フィールド）
            "integer_to_text": {
                "field_patterns": [
                    r".*原価.*",
                    r".*単価.*", 
                    r".*金額.*",
                    r".*価格.*"
                ],
                "condition": {
                    "inferred_type": "INTEGER",
                    "actual_type": "TEXT"
                },
                "action": "change_to_text"
            },
            
            # パターン4: 保管場所コード修正
            "storage_location_fix": {
                "files": ["zm114.txt"],
                "field_patterns": [r".*保管場所.*"],
                "condition": {
                    "inferred_type": "INTEGER",
                    "data_type": "numeric_code"
                },
                "action": "change_to_text"
            }
        }
        
        return pattern_rules
    
    def load_compare_report(self) -> pd.DataFrame:
        """column_masterテーブルを読み込み"""
        try:
            conn = sqlite3.connect(self.db_file)
            # column_masterテーブルからデータを読み込む
            # Actual_Typeは、analyzer.pyで推定されたInferred_Typeをそのまま使用
            self.df_compare = pd.read_sql_query("SELECT file_name AS File, column_name AS Column, initial_inferred_type AS Inferred_Type, data_type AS Actual_Type FROM column_master", conn)
            conn.close()
            # デバッグ用: df_compareの内容をCSVに出力
            debug_output_path = os.path.join(OUTPUT_DIR, "debug_df_compare.csv")
            self.df_compare.to_csv(debug_output_path, index=False, encoding="utf-8-sig")
            print(f"デバッグ: df_compareの内容を {debug_output_path} に出力しました。")
            print(f"column_masterテーブル読み込み完了: {len(self.df_compare)}行")
            return self.df_compare
        except Exception as e:
            logger.error(f"column_masterテーブル読み込みエラー: {e}")
            raise
    
    def analyze_pattern1_unregistered(self) -> pd.DataFrame:
        """パターン1: 未登録型の分析"""
        if self.df_compare is None:
            self.load_compare_report()
        
        # 未登録型（Inferred_Type_が空またはNaN）
        unregistered = self.df_compare[
            (self.df_compare['Inferred_Type'].isna()) | 
            (self.df_compare['Inferred_Type'] == '') |
            (self.df_compare['Inferred_Type'] == 'Unknown')
        ]
        
        logger.info(f"未登録型フィールド: {len(unregistered)}件")
        
        # ファイル別の集計
        file_summary = unregistered.groupby('File').agg({
            'Column': 'count',
            'Actual_Type': lambda x: (x == 'TEXT').mean()
        }).round(3)
        
        print("=== 未登録型ファイル別集計 ===")
        print(file_summary)
        
        return unregistered
    
    def analyze_pattern2_datetime_issues(self) -> pd.DataFrame:
        """パターン2: DATETIME型の問題分析"""
        if self.df_compare is None:
            self.load_compare_report()
        
        print(f"デバッグ: analyze_pattern2_datetime_issues - df_compare.columns: {self.df_compare.columns}")
        print(f"デバッグ: analyze_pattern2_datetime_issues - df_compare.head():\n{self.df_compare.head()}")

        # DATETIME推論だが実際はTEXTになっている
        condition = (
            (self.df_compare['Inferred_Type'] == 'DATETIME') &
            (self.df_compare['Actual_Type'] == 'TEXT')
        )
        print(f"デバッグ: analyze_pattern2_datetime_issues - condition.sum(): {condition.sum()}")
        datetime_issues = self.df_compare[condition]
        
        print(f"DATETIME問題フィールド: {len(datetime_issues)}件")
        
        # 詳細分析
        summary = datetime_issues[['File', 'Column', 'Inferred_Type', 'Actual_Type']].copy()
        
        print("=== DATETIME→TEXT修正対象 ===")
        print(summary.head(10))
        
        return datetime_issues
    
    def analyze_pattern3_integer_issues(self) -> pd.DataFrame:
        """パターン3: INTEGER型の問題分析"""
        if self.df_compare is None:
            self.load_compare_report()
        
        # INTEGER推論だが実際はTEXTが多い
        integer_issues = self.df_compare[
            (self.df_compare['Inferred_Type'] == 'INTEGER') &
            (self.df_compare['Actual_Type'] == 'TEXT')
        ]
        
        # 金額・価格・原価・単価関連フィールドをフィルタ
        price_related = integer_issues[
            integer_issues['Column'].str.contains(
                r'原価|単価|金額|価格|料金|費用', 
                regex=True, 
                na=False
            )
        ]
        
        logger.info(f"INTEGER→TEXT修正対象: {len(price_related)}件")
        
        print("=== INTEGER→TEXT修正対象（価格関連） ===")
        print(price_related[['File', 'Column', 'Inferred_Type', 'Actual_Type']].head(10))
        
        return price_related
    
    def analyze_pattern4_storage_location(self) -> pd.DataFrame:
        """パターン4: 保管場所コード問題分析"""
        if self.df_compare is None:
            self.load_compare_report()
        
        # zm114.txtの保管場所関連フィールド
        storage_issues = self.df_compare[
            (self.df_compare['File'] == 'zm114.txt') &
            (self.df_compare['Column'].str.contains('保管場所', na=False))
        ]
        
        logger.info(f"保管場所コード問題: {len(storage_issues)}件")
        
        print("=== 保管場所コード修正対象 ===")
        print(storage_issues[['Column', 'Inferred_Type', 'Actual_Type']])
        
        return storage_issues
    
    def generate_fix_rules(self) -> Dict[str, List[Dict]]:
        """修正ルールを生成"""
        fix_rules = {
            "pattern1_fixes": [],
            "pattern2_fixes": [],
            "pattern3_fixes": [],
            "pattern4_fixes": []
        }
        
        # パターン1: 未登録型修正
        unregistered = self.analyze_pattern1_unregistered()
        for _, row in unregistered.iterrows():
            # 実際の型から最適型を判定
            if row['Actual_Type'] == 'TEXT':
                suggested_type = 'TEXT'
            elif row['Actual_Type'] == 'INTEGER':
                suggested_type = 'INTEGER'  
            elif row['Actual_Type'] == 'REAL':
                suggested_type = 'REAL'
            else:
                suggested_type = 'TEXT'  # デフォルト
                
            fix_rules["pattern1_fixes"].append({
                "file_name": row['File'],
                "field_name": row['Column'],
                "from_type": "Unknown",
                "to_type": suggested_type,
                "confidence": 1.0  # 実際の型に基づくため確信度高
            })
        
        # パターン2: DATETIME→TEXT修正
        datetime_issues = self.analyze_pattern2_datetime_issues()
        for _, row in datetime_issues.iterrows():
            fix_rules["pattern2_fixes"].append({
                "file_name": row['File'],
                "field_name": row['Column'],
                "from_type": "DATETIME",
                "to_type": "TEXT",
                "reason": f"DATETIME推論エラー (実際は{row['Actual_Type']})"
            })
        
        # パターン3: INTEGER→TEXT修正
        integer_issues = self.analyze_pattern3_integer_issues()
        for _, row in integer_issues.iterrows():
            fix_rules["pattern3_fixes"].append({
                "file_name": row['File'],
                "field_name": row['Column'],
                "from_type": "INTEGER",
                "to_type": "TEXT",
                "reason": f"価格関連フィールド (実際は{row['Actual_Type']})"
            })
        
        # パターン4: 保管場所コード修正
        storage_issues = self.analyze_pattern4_storage_location()
        for _, row in storage_issues.iterrows():
            fix_rules["pattern4_fixes"].append({
                "file_name": row['File'],
                "field_name": row['Column'],
                "from_type": "INTEGER",
                "to_type": "TEXT",
                "reason": "保管場所コードは文字列として扱う"
            })
        
        return fix_rules
    
    def save_fix_rules(self, output_path: str = "pattern_rules.json") -> None:
        """修正ルールをJSONファイルに保存"""
        fix_rules = self.generate_fix_rules()
        
        # 統計情報を追加
        summary = {
            "generated_at": pd.Timestamp.now().isoformat(),
            "total_fixes": sum(len(fixes) for fixes in fix_rules.values()),
            "pattern_counts": {pattern: len(fixes) for pattern, fixes in fix_rules.items()}
        }
        
        output_data = {
            "summary": summary,
            "fix_rules": fix_rules
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"修正ルール保存完了: {output_path}")
        logger.info(f"総修正対象: {summary['total_fixes']}件")
        for pattern, count in summary['pattern_counts'].items():
            logger.info(f"  {pattern}: {count}件")
    
    def run_full_analysis(self) -> None:
        """全パターン分析実行"""
        logger.info("=== T002 修正パターン分析開始 ===")
        
        try:
            self.load_compare_report()
            
            print("\n" + "="*50)
            print("T002 データ型修正パターン分析結果")
            print("="*50)
            
            # 各パターン分析
            self.analyze_pattern1_unregistered()
            print()
            self.analyze_pattern2_datetime_issues()
            print()
            self.analyze_pattern3_integer_issues()
            print()
            self.analyze_pattern4_storage_location()
            
            # 修正ルール生成・保存
            self.save_fix_rules()
            
            logger.info("=== T002 修正パターン分析完了 ===")
            
        except Exception as e:
            logger.error(f"分析エラー: {e}")
            raise

def main():
    """メイン実行関数"""
    fixer = T002PatternFixer()
    fixer.run_full_analysis()

if __name__ == "__main__":
    main()
