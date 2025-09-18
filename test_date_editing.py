#!/usr/bin/env python3
"""
日付編集テスト
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_date_editing():
    """日付編集のテスト"""
    
    logger.info("=== 日付編集テスト ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 日付フィールドがあるテーブルを探す
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
    tables = [row[0] for row in cursor.fetchall()]
    
    test_table = None
    test_date_column = None
    
    # 適切なテーブルと日付カラムを見つける
    for table in tables[:5]:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            date_columns = [col[1] for col in columns if col[2] == 'DATETIME']
            
            if date_columns:
                test_table = table
                test_date_column = date_columns[0]
                break
        except Exception:
            continue
    
    if not test_table or not test_date_column:
        logger.error("テスト用の日付テーブル/カラムが見つかりません")
        conn.close()
        return
    
    logger.info(f"テスト対象: {test_table}.{test_date_column}")
    
    try:
        # 現在のデータを確認
        cursor.execute(f"SELECT rowid, {test_date_column} FROM {test_table} WHERE {test_date_column} IS NOT NULL LIMIT 5")
        original_data = cursor.fetchall()
        
        logger.info("元データ:")
        for rowid, date_value in original_data:
            logger.info(f"  rowid={rowid}: {date_value}")
        
        if original_data:
            # 最初のレコードで編集テスト
            test_rowid, original_date = original_data[0]
            
            # 新しい日付値でテスト更新
            test_date = '2024-01-15 00:00:00.000000'
            
            logger.info(f"テスト更新: rowid={test_rowid}, {original_date} → {test_date}")
            
            cursor.execute(f"UPDATE {test_table} SET {test_date_column} = ? WHERE rowid = ?", 
                         (test_date, test_rowid))
            
            # 更新結果を確認
            cursor.execute(f"SELECT {test_date_column} FROM {test_table} WHERE rowid = ?", (test_rowid,))
            updated_value = cursor.fetchone()[0]
            
            logger.info(f"更新後の値: {updated_value}")
            
            if updated_value == '0':
                logger.error("❌ 日付が0になりました！")
            elif updated_value == test_date:
                logger.info("✅ 日付更新成功")
            else:
                logger.warning(f"⚠️  予期しない値: {updated_value}")
            
            # 元に戻す
            cursor.execute(f"UPDATE {test_table} SET {test_date_column} = ? WHERE rowid = ?", 
                         (original_date, test_rowid))
            
            logger.info("元の値に復元しました")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"テストエラー: {e}")
        conn.rollback()
    
    conn.close()

if __name__ == "__main__":
    test_date_editing()