#!/usr/bin/env python3
"""
T003 - 統合型レポート機能
データ型修正の成果と統合状況を分析・レポート
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import json
from collections import defaultdict, Counter
from config import DB_FILE

class IntegrationReportGenerator:
    """データ型統合レポート生成クラス"""
    
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.conn = None
        
    def connect(self):
        """データベース接続"""
        try:
            self.conn = sqlite3.connect(self.db_file)
            print(f"データベース接続成功: {self.db_file}")
            return True
        except Exception as e:
            print(f"データベース接続失敗: {e}")
            return False
    
    def close(self):
        """データベース接続終了"""
        if self.conn:
            self.conn.close()
    
    def get_table_list(self) -> List[str]:
        """SQLiteの全テーブル一覧を取得"""
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_column_master_summary(self) -> pd.DataFrame:
        """column_masterからの推定型サマリーを取得"""
        if not self.conn:
            return pd.DataFrame()
        
        query = """
        SELECT 
            data_type,
            COUNT(*) as field_count,
            COUNT(DISTINCT file_name) as file_count
        FROM column_master 
        GROUP BY data_type 
        ORDER BY field_count DESC
        """
        return pd.read_sql_query(query, self.conn)
    
    def get_actual_table_schema_summary(self) -> Dict[str, int]:
        """実際のテーブルスキーマから型分布を取得"""
        if not self.conn:
            return {}
        
        tables = self.get_table_list()
        type_count = defaultdict(int)
        
        for table in tables:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                for col in columns:
                    col_type = col[2].upper()  # 型情報
                    type_count[col_type] += 1
                    
            except Exception as e:
                print(f"テーブル {table} の情報取得失敗: {e}")
                continue
        
        return dict(type_count)
    
    def analyze_type_consistency(self) -> pd.DataFrame:
        """推定型と実際の型の整合性分析"""
        if not self.conn:
            return pd.DataFrame()
        
        # テーブル一覧を取得
        tables = self.get_table_list