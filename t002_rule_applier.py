#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T002 - 修正ルール適用ツール

生成された修正ルール（pattern_rules.json）を実際のデータに適用し、
型推定の精度を向上させる。

作成日: 2024-09-12
"""

import json
import sqlite3
import pandas as pd
from config import OUTPUT_DIR, DB_FILE
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class T002RuleApplier:
    """修正ルールを実際のSQLiteスキーマに適用するクラス"""
    
    def __init__(self, rules_file="pattern_rules.json"):
        self.rules_file = rules_file
        self.db_file = DB_FILE
        self.rules_data = self._load_rules()
        
    def _load_rules(self):
        """修正ルールを読み込み"""
        if not os.path.exists(self.rules_file):
            logger.error(f"修正ルールファイルが見つかりません: {self.rules_file}")
            return None
            
        with open(self.rules_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def analyze_current_schema(self):
        """現在のSQLiteスキーマの分析"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # テーブル一覧取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = {}
        for table_name in tables:
            table_name = table_name[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            schema_info[table_name] = {
                col[1]: col[2] for col in columns  # column_name: type
            }
        
        conn.close()
        return schema_info
    
    def apply_datetime_fixes(self):
        """DATETIME修正ルールの適用"""
        logger.info("DATETIME修正ルール適用開始...")
        
        if not self.rules_data:
            return False
            
        datetime_fixes = self.rules_data['fix_rules']['pattern2_fixes']
        logger.info(f"適用対象: {len(datetime_fixes)}件")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        success_count = 0
        for fix in datetime_fixes:
            file_name = fix['file_name']
            field_name = fix['field_name']
            
            # テーブル名を正規化
            table_name = file_name.replace('.txt', '').replace('.csv', '').replace('.xlsx', '')
            table_name = table_name.replace('-', '_').replace('（', '_').replace('）', '_')
            
            try:
                # column_masterのdata_typeをTEXTに変更
                cursor.execute("""
                    UPDATE column_master
                    SET data_type = ?
                    WHERE file_name = ? AND column_name = ?
                """, ("TEXT", file_name, field_name))
                success_count += 1
                logger.info(f"column_master更新: {file_name}:{field_name} DATETIME -> TEXT")
                
            except Exception as e:
                logger.warning(f"column_master更新スキップ {file_name}.{field_name}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"DATETIME修正完了: {success_count}/{len(datetime_fixes)}件")
        return True
    
    def apply_storage_code_fixes(self):
        """保管場所コード修正ルールの適用"""
        logger.info("保管場所コード修正ルール適用開始...")
        
        if not self.rules_data:
            return False
            
        storage_fixes = self.rules_data['fix_rules']['pattern4_fixes']
        logger.info(f"適用対象: {len(storage_fixes)}件")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        success_count = 0
        for fix in storage_fixes:
            file_name = fix['file_name']
            column_name = fix['field_name']
            to_type = fix['to_type']
            try:
                cursor.execute("""
                    UPDATE column_master
                    SET data_type = ?
                    WHERE file_name = ? AND column_name = ?
                """, (to_type, file_name, column_name))
                success_count += 1
                logger.info(f"column_master更新: {file_name}:{column_name} -> {to_type}")
            except Exception as e:
                logger.warning(f"column_master更新スキップ {file_name}:{column_name}: {e}")

        conn.commit()
        conn.close()
        logger.info(f"保管場所コード修正完了: {success_count}/{len(storage_fixes)}件")
        return True
    
    def apply_unregistered_fixes(self):
        """未登録型修正ルールの適用 (column_masterを更新)"""
        logger.info("未登録型修正ルール適用開始 (column_master更新)... ")
        
        if not self.rules_data:
            return False
            
        unregistered_fixes = self.rules_data['fix_rules']['pattern1_fixes']
        logger.info(f"適用対象: {len(unregistered_fixes)}件")
        
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        success_count = 0
        for fix in unregistered_fixes:
            file_name = fix['file_name']
            column_name = fix['field_name']
            to_type = fix['to_type']
            
            try:
                cursor.execute("""
                    UPDATE column_master
                    SET data_type = ?
                    WHERE file_name = ? AND column_name = ?
                """, (to_type, file_name, column_name))
                success_count += 1
                logger.info(f"column_master更新: {file_name}:{column_name} -> {to_type}")
            except Exception as e:
                logger.warning(f"column_master更新スキップ {file_name}:{column_name}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"未登録型修正完了 (column_master更新): {success_count}/{len(unregistered_fixes)}件")
        return True
    
    def generate_loader_updates(self):
        """loader.pyのパターンルール更新情報を生成"""
        if not self.rules_data:
            return
            
        logger.info("loader.py更新情報生成...")
        
        # DATETIME修正対象フィールドのリスト
        datetime_fields = []
        for fix in self.rules_data['fix_rules']['pattern2_fixes']:
            datetime_fields.append({
                'file': fix['file_name'],
                'field': fix['field_name'],
                'action': 'force_text'
            })
        
        # 保管場所修正対象
        storage_fields = []
        for fix in self.rules_data['fix_rules']['pattern4_fixes']:
            storage_fields.append({
                'file': fix['file_name'], 
                'field': fix['field_name'],
                'action': 'force_text'
            })
        
        update_info = {
            'datetime_override_fields': datetime_fields,
            'storage_code_fields': storage_fields,
            'total_overrides': len(datetime_fields) + len(storage_fields)
        }
        
        # 更新情報をJSONで保存
        with open('t002_loader_updates.json', 'w', encoding='utf-8') as f:
            json.dump(update_info, f, indent=2, ensure_ascii=False)
            
        logger.info(f"loader.py更新情報保存完了: t002_loader_updates.json")
        logger.info(f"  DATETIME強制TEXT化: {len(datetime_fields)}件")
        logger.info(f"  保管場所コード強制TEXT化: {len(storage_fields)}件")
        
        return update_info
    
    def run_full_application(self):
        """全修正ルールの適用"""
        logger.info("=== T002修正ルール適用開始 ===")
        
        try:
            # 現在のスキーマ分析
            schema_info = self.analyze_current_schema()
            logger.info(f"データベース内テーブル数: {len(schema_info)}")
            
            # 各修正ルールの適用
            self.apply_datetime_fixes()
            self.apply_storage_code_fixes()
            self.apply_unregistered_fixes() # 未登録型修正の適用を追加
            
            # loader.py更新情報生成
            update_info = self.generate_loader_updates()
            
            logger.info("=== T002修正ルール適用完了 ===")
            logger.info(f"総修正件数: {update_info['total_overrides']}件")
            
            return True
            
        except Exception as e:
            logger.error(f"修正ルール適用エラー: {e}")
            return False

def main():
    """メイン実行"""
    applier = T002RuleApplier()
    applier.run_full_application()

if __name__ == "__main__":
    main()
