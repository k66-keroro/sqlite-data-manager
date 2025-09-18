#!/usr/bin/env python3
"""
数値フィールドをREAL型に修正するスクリプト
"""

import sqlite3
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_numeric_fields():
    """数値フィールドをREAL型に修正"""
    
    logger.info("=== 数値フィールドの型修正開始 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 修正対象フィールドの定義
    numeric_field_fixes = [
        # zs65.txt
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
        
        # zs65_sss.txt (同じフィールド)
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
        
        # 払出明細ファイル
        ('払出明細（大阪）_ZPR01201.txt', 'プラント在庫数量', 'REAL'),
        ('払出明細（大阪）_ZPR01201.txt', '利用可能数量', 'REAL'),
        ('払出明細（滋賀）_ZPR01201.txt', 'プラント在庫数量', 'REAL'),
        ('払出明細（滋賀）_ZPR01201.txt', '利用可能数量', 'REAL'),
    ]
    
    # 修正前の状況確認
    logger.info("修正前の状況確認:")
    for file_name, column_name, new_type in numeric_field_fixes[:5]:  # 最初の5件だけ表示
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
            # column_masterを更新
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
    cursor.execute("""
        SELECT file_name, COUNT(*) as count
        FROM column_master 
        WHERE data_type = 'REAL'
        AND file_name IN ('zs65.txt', 'zs65_sss.txt', 
                         '払出明細（大阪）_ZPR01201.txt', '払出明細（滋賀）_ZPR01201.txt')
        GROUP BY file_name
        ORDER BY file_name
    """)
    
    results = cursor.fetchall()
    total_real_fields = 0
    
    for file_name, count in results:
        logger.info(f"  {file_name}: {count}件のREAL型フィールド")
        total_real_fields += count
    
    logger.info(f"=== 修正完了 ===")
    logger.info(f"成功: {success_count}件")
    logger.info(f"エラー: {error_count}件")
    logger.info(f"対象ファイルのREAL型フィールド総数: {total_real_fields}件")
    
    conn.close()

if __name__ == "__main__":
    fix_numeric_fields()