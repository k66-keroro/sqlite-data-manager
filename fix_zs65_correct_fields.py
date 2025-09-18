#!/usr/bin/env python3
"""
zs65ファイルの正確な列名で数値フィールドを修正
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_zs65_correct_fields():
    """正確な列名でzs65ファイルの数値フィールドを修正"""
    
    logger.info("=== zs65ファイル数値フィールド修正（正確な列名） ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 正確な列名での修正対象フィールド
    numeric_field_fixes = [
        # zs65.txt - 真の数値フィールドのみ
        ('zs65.txt', '利用可能評価在庫', 'REAL'),
        ('zs65.txt', '利用可能値', 'REAL'),
        ('zs65.txt', '転送中在庫（保管場所間）', 'REAL'),
        ('zs65.txt', '積送/輸送中の値', 'REAL'),
        ('zs65.txt', '品質検査中在庫', 'REAL'),
        ('zs65.txt', '品質検査値', 'REAL'),
        ('zs65.txt', '非利用可能ロットの全在庫合計', 'REAL'),
        ('zs65.txt', '制限値', 'REAL'),
        ('zs65.txt', '保留在庫', 'REAL'),
        ('zs65.txt', '保留在庫値', 'REAL'),
        ('zs65.txt', '返品保留在庫', 'REAL'),
        ('zs65.txt', '保留返品金額', 'REAL'),
        ('zs65.txt', '滞留日数', 'REAL'),
        
        # zs65_sss.txt - 同じフィールド
        ('zs65_sss.txt', '利用可能評価在庫', 'REAL'),
        ('zs65_sss.txt', '利用可能値', 'REAL'),
        ('zs65_sss.txt', '転送中在庫（保管場所間）', 'REAL'),
        ('zs65_sss.txt', '積送/輸送中の値', 'REAL'),
        ('zs65_sss.txt', '品質検査中在庫', 'REAL'),
        ('zs65_sss.txt', '品質検査値', 'REAL'),
        ('zs65_sss.txt', '非利用可能ロットの全在庫合計', 'REAL'),
        ('zs65_sss.txt', '制限値', 'REAL'),
        ('zs65_sss.txt', '保留在庫', 'REAL'),
        ('zs65_sss.txt', '保留在庫値', 'REAL'),
        ('zs65_sss.txt', '返品保留在庫', 'REAL'),
        ('zs65_sss.txt', '保留返品金額', 'REAL'),
        ('zs65_sss.txt', '滞留日数', 'REAL'),
    ]
    
    # 修正前の確認
    logger.info("修正前の確認:")
    for file_name, column_name, new_type in numeric_field_fixes[:5]:
        cursor.execute("""
            SELECT data_type FROM column_master 
            WHERE file_name = ? AND column_name = ?
        """, (file_name, column_name))
        
        result = cursor.fetchone()
        if result:
            current_type = result[0]
            logger.info(f"  {file_name}:{column_name} = {current_type}")
        else:
            logger.warning(f"  {file_name}:{column_name} = 見つかりません")
    
    # 修正実行
    success_count = 0
    error_count = 0
    
    logger.info("修正実行中...")
    
    for file_name, column_name, new_type in numeric_field_fixes:
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
                error_count += 1
                
        except Exception as e:
            logger.error(f"❌ {file_name}:{column_name} - エラー: {e}")
            error_count += 1
    
    # 払出明細ファイルも修正
    payout_fixes = [
        ('払出明細（大阪）_ZPR01201.txt', 'プラント在庫数量', 'REAL'),
        ('払出明細（大阪）_ZPR01201.txt', '利用可能数量', 'REAL'),
        ('払出明細（滋賀）_ZPR01201.txt', 'プラント在庫数量', 'REAL'),
        ('払出明細（滋賀）_ZPR01201.txt', '利用可能数量', 'REAL'),
    ]
    
    logger.info("払出明細ファイル修正中...")
    
    for file_name, column_name, new_type in payout_fixes:
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
                error_count += 1
                
        except Exception as e:
            logger.error(f"❌ {file_name}:{column_name} - エラー: {e}")
            error_count += 1
    
    # 結果をコミット
    conn.commit()
    
    # 修正結果の確認
    logger.info("修正結果の確認:")
    
    problem_files = ['zs65.txt', 'zs65_sss.txt', '払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt']
    
    for file_name in problem_files:
        cursor.execute("""
            SELECT COUNT(*) FROM column_master 
            WHERE file_name = ? AND data_type = 'REAL'
        """, (file_name,))
        
        real_count = cursor.fetchone()[0]
        logger.info(f"  {file_name}: {real_count}件のREAL型フィールド")
    
    logger.info(f"=== 修正完了 ===")
    logger.info(f"成功: {success_count}件")
    logger.info(f"エラー: {error_count}件")
    
    conn.close()

if __name__ == "__main__":
    fix_zs65_correct_fields()