#!/usr/bin/env python3
"""
0パディング問題を修正
"""

import sqlite3
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_zero_padding():
    """0パディング問題を修正"""
    
    logger.info("=== 0パディング修正開始 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 0パディングの正規表現パターン
    zero_padding_pattern = r'^0+(\d+)$'
    
    # 修正対象テーブルとフィールドを特定
    target_fixes = [
        ('ZS58MONTH', '受注伝票番号'),
        ('ZS58MONTH', '受注明細番号'),
    ]
    
    total_fixed = 0
    
    for table_name, column_name in target_fixes:
        logger.info(f"修正中: {table_name}.{column_name}")
        
        try:
            # テーブルが存在するか確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table_name,))
            if not cursor.fetchone():
                logger.warning(f"テーブル {table_name} が見つかりません")
                continue
            
            # カラムが存在するか確認
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if column_name not in columns:
                logger.warning(f"カラム {table_name}.{column_name} が見つかりません")
                continue
            
            # 0パディングデータを取得（0で始まる数値データ）
            cursor.execute(f"SELECT rowid, {column_name} FROM {table_name} WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
            zero_padded_rows = cursor.fetchall()
            
            # Pythonで正規表現フィルタリング
            filtered_rows = []
            for rowid, value in zero_padded_rows:
                if re.match(zero_padding_pattern, str(value)):
                    filtered_rows.append((rowid, value))
            
            zero_padded_rows = filtered_rows
            
            logger.info(f"  0パディングデータ: {len(zero_padded_rows)}件")
            
            if zero_padded_rows:
                # サンプル表示
                for i, (rowid, value) in enumerate(zero_padded_rows[:5], 1):
                    match = re.match(zero_padding_pattern, value)
                    if match:
                        cleaned_value = match.group(1)
                        logger.info(f"    例{i}: {value} → {cleaned_value}")
                
                # 実際の修正実行
                fixed_count = 0
                for rowid, value in zero_padded_rows:
                    match = re.match(zero_padding_pattern, value)
                    if match:
                        cleaned_value = match.group(1)
                        
                        # 更新実行
                        cursor.execute(f"UPDATE {table_name} SET {column_name} = ? WHERE rowid = ?", 
                                     (cleaned_value, rowid))
                        fixed_count += 1
                
                logger.info(f"  修正完了: {fixed_count}件")
                total_fixed += fixed_count
            
        except Exception as e:
            logger.error(f"エラー: {table_name}.{column_name} - {e}")
    
    # 変更をコミット
    conn.commit()
    
    # 修正結果の確認
    logger.info("修正結果の確認:")
    
    for table_name, column_name in target_fixes:
        try:
            cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT 10")
            samples = [row[0] for row in cursor.fetchall()]
            logger.info(f"  {table_name}.{column_name}: {samples}")
            
            # 0パディングが残っているかチェック
            cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
            potential_remaining = cursor.fetchone()[0]
            
            # Pythonで正確にチェック
            if potential_remaining > 0:
                cursor.execute(f"SELECT {column_name} FROM {table_name} WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
                potential_values = [row[0] for row in cursor.fetchall()]
                remaining_count = sum(1 for v in potential_values if re.match(zero_padding_pattern, str(v)))
            else:
                remaining_count = 0
            
            if remaining_count > 0:
                logger.warning(f"    ⚠️  まだ0パディングが残っています: {remaining_count}件")
            else:
                logger.info(f"    ✅ 0パディング修正完了")
                
        except Exception as e:
            logger.error(f"確認エラー: {table_name}.{column_name} - {e}")
    
    logger.info(f"=== 0パディング修正完了 ===")
    logger.info(f"総修正件数: {total_fixed}件")
    
    conn.close()

if __name__ == "__main__":
    fix_zero_padding()