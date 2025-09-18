#!/usr/bin/env python3
"""
実際の問題を詳細調査
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def investigate_actual_issues():
    """実際の問題を詳細調査"""
    
    logger.info("=== 実際の問題の詳細調査 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 1. 日付が0になる問題の調査
    logger.info("\n1. 日付が0になる問題の調査")
    logger.info("-" * 50)
    
    # GetSekkeiWBSJissekiテーブルの日付フィールドを確認
    try:
        cursor.execute("SELECT STA_SCH_DT, COMP_SCH_DT FROM GetSekkeiWBSJisseki LIMIT 10")
        date_samples = cursor.fetchall()
        
        logger.info("GetSekkeiWBSJisseki日付サンプル:")
        for i, (sta_date, comp_date) in enumerate(date_samples, 1):
            logger.info(f"  {i}: STA_SCH_DT={sta_date}, COMP_SCH_DT={comp_date}")
            
            # 0や1になっているデータをチェック
            if str(sta_date) in ['0', '1'] or str(comp_date) in ['0', '1']:
                logger.error(f"    ❌ 異常な日付値検出: STA_SCH_DT={sta_date}, COMP_SCH_DT={comp_date}")
        
        # 0や1の値の総数を確認
        cursor.execute("SELECT COUNT(*) FROM GetSekkeiWBSJisseki WHERE STA_SCH_DT IN ('0', '1')")
        zero_sta_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM GetSekkeiWBSJisseki WHERE COMP_SCH_DT IN ('0', '1')")
        zero_comp_count = cursor.fetchone()[0]
        
        if zero_sta_count > 0 or zero_comp_count > 0:
            logger.error(f"異常な日付値: STA_SCH_DT={zero_sta_count}件, COMP_SCH_DT={zero_comp_count}件")
        else:
            logger.info("日付フィールドは正常です")
            
    except Exception as e:
        logger.error(f"日付調査エラー: {e}")
    
    # 2. ZS58MONTHの0パディング問題調査
    logger.info("\n2. ZS58MONTHの0パディング問題調査")
    logger.info("-" * 50)
    
    try:
        # すべての番号系フィールドを確認
        cursor.execute("PRAGMA table_info(ZS58MONTH)")
        columns = cursor.fetchall()
        
        number_columns = [col[1] for col in columns if '番号' in col[1] or 'コード' in col[1]]
        
        logger.info(f"番号系フィールド: {number_columns}")
        
        for col in number_columns:
            cursor.execute(f"SELECT {col} FROM ZS58MONTH WHERE {col} LIKE '0%' AND LENGTH({col}) > 1 LIMIT 5")
            zero_padded = cursor.fetchall()
            
            if zero_padded:
                samples = [row[0] for row in zero_padded]
                logger.warning(f"  {col}: 0パディング残存 {samples}")
            else:
                logger.info(f"  {col}: 0パディングなし")
                
    except Exception as e:
        logger.error(f"0パディング調査エラー: {e}")
    
    # 3. zs45テーブルの数値型問題調査
    logger.info("\n3. zs45テーブルの数値型問題調査")
    logger.info("-" * 50)
    
    try:
        # column_masterでzs45の型を確認
        cursor.execute("SELECT column_name, data_type FROM column_master WHERE file_name = 'zs45.txt' ORDER BY column_name")
        zs45_fields = cursor.fetchall()
        
        logger.info(f"zs45.txt フィールド数: {len(zs45_fields)}")
        
        # 型別集計
        type_counts = {}
        for col, dtype in zs45_fields:
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
        
        logger.info("型分布:")
        for dtype, count in type_counts.items():
            logger.info(f"  {dtype}: {count}件")
        
        # 数値っぽいフィールドでTEXT型のものを確認
        numeric_text_fields = [
            (col, dtype) for col, dtype in zs45_fields 
            if dtype == 'TEXT' and any(keyword in col for keyword in ['数量', '金額', '単価', '原価', '重量', '値'])
        ]
        
        if numeric_text_fields:
            logger.warning(f"数値っぽいのにTEXT型: {len(numeric_text_fields)}件")
            for col, dtype in numeric_text_fields[:5]:
                logger.warning(f"  {col} ({dtype})")
        
        # 実際のテーブルが存在するか確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'zs45'")
        if cursor.fetchone():
            logger.info("zs45テーブル存在確認: ✅")
        else:
            logger.warning("zs45テーブルが見つかりません")
            
    except Exception as e:
        logger.error(f"zs45調査エラー: {e}")
    
    # 4. 全体的な問題の確認
    logger.info("\n4. 全体的な問題の確認")
    logger.info("-" * 50)
    
    try:
        # 型統一率の再計算
        cursor.execute("SELECT COUNT(*) FROM column_master")
        total_fields = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type != 'TEXT'")
        typed_fields = cursor.fetchone()[0]
        
        type_rate = (typed_fields / total_fields) * 100
        logger.info(f"現在の型統一率: {type_rate:.1f}% ({typed_fields}/{total_fields})")
        
        # 問題のあるテーブルの特定
        cursor.execute("""
            SELECT file_name, COUNT(*) as total, 
                   SUM(CASE WHEN data_type = 'TEXT' THEN 1 ELSE 0 END) as text_count
            FROM column_master 
            GROUP BY file_name 
            HAVING text_count > total * 0.8
            ORDER BY text_count DESC
            LIMIT 10
        """)
        
        problem_files = cursor.fetchall()
        logger.info("TEXT型が多いファイル (80%以上):")
        for file_name, total, text_count in problem_files:
            text_rate = (text_count / total) * 100
            logger.warning(f"  {file_name}: {text_rate:.1f}% ({text_count}/{total})")
            
    except Exception as e:
        logger.error(f"全体調査エラー: {e}")
    
    conn.close()

if __name__ == "__main__":
    investigate_actual_issues()