#!/usr/bin/env python3
"""
日付が1になる問題を調査
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def investigate_date_1_issue():
    """日付が1になる問題を調査"""
    
    logger.info("=== 日付が1になる問題の調査 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # GetSekkeiWBSJissekiテーブルの詳細調査
    try:
        # テーブル構造を確認
        cursor.execute("PRAGMA table_info(GetSekkeiWBSJisseki)")
        columns = cursor.fetchall()
        
        logger.info("GetSekkeiWBSJissekiテーブル構造:")
        for col in columns:
            col_name, col_type = col[1], col[2]
            logger.info(f"  {col_name}: {col_type}")
        
        # 日付フィールドの詳細確認
        date_columns = [col[1] for col in columns if col[2] == 'DATETIME']
        
        for date_col in date_columns:
            logger.info(f"\n--- {date_col} の詳細調査 ---")
            
            # 全データの値の種類を確認
            cursor.execute(f"SELECT {date_col}, COUNT(*) FROM GetSekkeiWBSJisseki GROUP BY {date_col} ORDER BY COUNT(*) DESC LIMIT 10")
            value_counts = cursor.fetchall()
            
            logger.info("値の分布 (上位10件):")
            for value, count in value_counts:
                logger.info(f"  {value}: {count}件")
                
                # 1や0の値があるかチェック
                if str(value) in ['0', '1']:
                    logger.error(f"    ❌ 異常な値検出: {value}")
            
            # 特定の行の詳細確認（画像で見えた行3）
            cursor.execute(f"SELECT rowid, {date_col} FROM GetSekkeiWBSJisseki WHERE rowid = 3")
            row3_data = cursor.fetchone()
            
            if row3_data:
                rowid, date_value = row3_data
                logger.info(f"行3のデータ: rowid={rowid}, {date_col}={date_value}")
                
                if str(date_value) == '1':
                    logger.error(f"❌ 行3で異常な値検出: {date_value}")
                    
                    # この行の他のフィールドも確認
                    cursor.execute("SELECT * FROM GetSekkeiWBSJisseki WHERE rowid = 3")
                    full_row = cursor.fetchone()
                    logger.info(f"行3の全データ: {full_row}")
        
        # 異常な日付値の総数確認
        for date_col in date_columns:
            cursor.execute(f"SELECT COUNT(*) FROM GetSekkeiWBSJisseki WHERE {date_col} IN ('0', '1', '2', '3', '4', '5')")
            abnormal_count = cursor.fetchone()[0]
            
            if abnormal_count > 0:
                logger.error(f"{date_col}: 異常な値 {abnormal_count}件")
                
                # 異常な値のサンプルを表示
                cursor.execute(f"SELECT rowid, {date_col} FROM GetSekkeiWBSJisseki WHERE {date_col} IN ('0', '1', '2', '3', '4', '5') LIMIT 5")
                abnormal_samples = cursor.fetchall()
                
                for rowid, value in abnormal_samples:
                    logger.error(f"  rowid={rowid}: {value}")
            else:
                logger.info(f"{date_col}: 異常な値なし")
        
    except Exception as e:
        logger.error(f"調査エラー: {e}")
    
    conn.close()

if __name__ == "__main__":
    investigate_date_1_issue()