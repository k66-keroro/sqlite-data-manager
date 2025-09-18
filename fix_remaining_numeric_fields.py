#!/usr/bin/env python3
"""
残りの数値フィールドを修正
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_remaining_fields():
    """残りの数値フィールドを修正"""
    
    logger.info("=== 残りの数値フィールド修正 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 残りの修正対象フィールド
    remaining_fixes = [
        # zs65.txt
        ('zs65.txt', '基本数量単位', 'TEXT'),  # これは単位なのでTEXTのまま
        ('zs65.txt', '特殊在庫の評価', 'REAL'),
        ('zs65.txt', '特殊在庫区分', 'TEXT'),  # 区分コードなのでTEXTのまま
        ('zs65.txt', '特殊在庫番号', 'TEXT'),  # 番号なのでTEXTのまま
        
        # zs65_sss.txt (同じ)
        ('zs65_sss.txt', '基本数量単位', 'TEXT'),
        ('zs65_sss.txt', '特殊在庫の評価', 'REAL'),
        ('zs65_sss.txt', '特殊在庫区分', 'TEXT'),
        ('zs65_sss.txt', '特殊在庫番号', 'TEXT'),
    ]
    
    # 実際に修正が必要なもののみ実行
    actual_fixes = [(f, c, t) for f, c, t in remaining_fixes if t == 'REAL']
    
    logger.info(f"修正対象: {len(actual_fixes)}件")
    
    success_count = 0
    for file_name, column_name, new_type in actual_fixes:
        try:
            cursor.execute("""
                UPDATE column_master 
                SET data_type = ?
                WHERE file_name = ? AND column_name = ?
            """, (new_type, file_name, column_name))
            
            if cursor.rowcount > 0:
                logger.info(f"✅ {file_name}:{column_name} → {new_type}")
                success_count += 1
            else:
                logger.warning(f"⚠️  {file_name}:{column_name} - レコードが見つかりません")
                
        except Exception as e:
            logger.error(f"❌ {file_name}:{column_name} - エラー: {e}")
    
    conn.commit()
    
    # 最終確認
    logger.info("=== 最終確認 ===")
    
    # REAL型フィールドの総数
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type = 'REAL'")
    real_count = cursor.fetchone()[0]
    logger.info(f"REAL型フィールド総数: {real_count}件")
    
    # DATETIME型フィールドの総数
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type = 'DATETIME'")
    datetime_count = cursor.fetchone()[0]
    logger.info(f"DATETIME型フィールド総数: {datetime_count}件")
    
    # 問題ファイルの型分布
    problem_files = ['zs65.txt', 'zs65_sss.txt', '払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt']
    
    for file_name in problem_files:
        cursor.execute("""
            SELECT data_type, COUNT(*) 
            FROM column_master 
            WHERE file_name = ?
            GROUP BY data_type
            ORDER BY data_type
        """, (file_name,))
        
        results = cursor.fetchall()
        type_summary = ", ".join([f"{dtype}:{count}" for dtype, count in results])
        logger.info(f"{file_name}: {type_summary}")
    
    logger.info(f"修正完了: {success_count}件")
    
    conn.close()

if __name__ == "__main__":
    fix_remaining_fields()