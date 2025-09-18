#!/usr/bin/env python3
"""
数値型の問題を修正
"""

import sqlite3
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_numeric_type_issues():
    """数値型の問題を修正"""
    
    logger.info("=== 数値型問題修正開始 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 問題のあるファイルの数値フィールドを特定
    problem_files_fixes = [
        # zs65.txt - まだTEXT型のフィールド
        ('zs65.txt', '特殊在庫区分', 'INTEGER'),  # 区分は整数
        ('zs65.txt', '特殊在庫番号', 'TEXT'),     # 番号はTEXTのまま
        ('zs65.txt', '基本数量単位', 'TEXT'),     # 単位はTEXTのまま
        ('zs65.txt', '通貨コード', 'TEXT'),       # コードはTEXTのまま
        ('zs65.txt', '販売伝票', 'TEXT'),         # 伝票番号はTEXTのまま
        ('zs65.txt', '販売伝票明細', 'TEXT'),     # 明細番号はTEXTのまま
        ('zs65.txt', '棚番', 'TEXT'),             # 棚番はTEXTのまま
        ('zs65.txt', '勘定科目コード', 'TEXT'),   # コードはTEXTのまま
        ('zs65.txt', '勘定科目名', 'TEXT'),       # 名前はTEXTのまま
        ('zs65.txt', '品目タイプ', 'TEXT'),       # タイプはTEXTのまま
        ('zs65.txt', '評価クラス', 'TEXT'),       # クラスはTEXTのまま
        ('zs65.txt', '評価クラステキスト', 'TEXT'), # テキストはTEXTのまま
        ('zs65.txt', '調達タイプ', 'TEXT'),       # タイプはTEXTのまま
        ('zs65.txt', '調達タイプテキスト', 'TEXT'), # テキストはTEXTのまま
        ('zs65.txt', '評価減区分', 'TEXT'),       # 区分はTEXTのまま
        
        # zs65_sss.txt - 同じ修正
        ('zs65_sss.txt', '特殊在庫区分', 'INTEGER'),
        ('zs65_sss.txt', '特殊在庫番号', 'TEXT'),
        ('zs65_sss.txt', '基本数量単位', 'TEXT'),
        ('zs65_sss.txt', '通貨コード', 'TEXT'),
        ('zs65_sss.txt', '販売伝票', 'TEXT'),
        ('zs65_sss.txt', '販売伝票明細', 'TEXT'),
        ('zs65_sss.txt', '棚番', 'TEXT'),
        ('zs65_sss.txt', '勘定科目コード', 'TEXT'),
        ('zs65_sss.txt', '勘定科目名', 'TEXT'),
        ('zs65_sss.txt', '品目タイプ', 'TEXT'),
        ('zs65_sss.txt', '評価クラス', 'TEXT'),
        ('zs65_sss.txt', '評価クラステキスト', 'TEXT'),
        ('zs65_sss.txt', '調達タイプ', 'TEXT'),
        ('zs65_sss.txt', '調達タイプテキスト', 'TEXT'),
        ('zs65_sss.txt', '評価減区分', 'TEXT'),
    ]
    
    # 修正実行
    success_count = 0
    error_count = 0
    
    logger.info("数値型修正実行中...")
    
    for file_name, column_name, target_type in problem_files_fixes:
        try:
            # 現在の型を確認
            cursor.execute("""
                SELECT data_type FROM column_master 
                WHERE file_name = ? AND column_name = ?
            """, (file_name, column_name))
            
            result = cursor.fetchone()
            if result:
                current_type = result[0]
                
                # 型が異なる場合のみ更新
                if current_type != target_type:
                    cursor.execute("""
                        UPDATE column_master 
                        SET data_type = ?
                        WHERE file_name = ? AND column_name = ?
                    """, (target_type, file_name, column_name))
                    
                    logger.info(f"✅ {file_name}:{column_name} {current_type} → {target_type}")
                    success_count += 1
                else:
                    logger.info(f"⏭️  {file_name}:{column_name} 既に{target_type}型")
            else:
                logger.warning(f"⚠️  {file_name}:{column_name} - レコードが見つかりません")
                error_count += 1
                
        except Exception as e:
            logger.error(f"❌ {file_name}:{column_name} - エラー: {e}")
            error_count += 1
    
    # 変更をコミット
    conn.commit()
    
    # 修正結果の確認
    logger.info("\n修正結果の確認:")
    logger.info("-" * 50)
    
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
        total_file_fields = sum(count for _, count in results)
        
        type_summary = ", ".join([f"{dtype}:{count}" for dtype, count in results])
        logger.info(f"{file_name} ({total_file_fields}フィールド): {type_summary}")
        
        # TEXT型の割合を計算
        text_count = next((count for dtype, count in results if dtype == 'TEXT'), 0)
        text_rate = (text_count / total_file_fields) * 100 if total_file_fields > 0 else 0
        
        if text_rate > 80:
            logger.warning(f"  ⚠️  TEXT型が多すぎます: {text_rate:.1f}%")
        else:
            logger.info(f"  ✅ TEXT型割合: {text_rate:.1f}%")
    
    # 全体の型統一率を再計算
    cursor.execute("SELECT COUNT(*) FROM column_master")
    total_fields = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM column_master WHERE data_type != 'TEXT'")
    typed_fields = cursor.fetchone()[0]
    
    type_rate = (typed_fields / total_fields) * 100
    logger.info(f"\n全体の型統一率: {type_rate:.1f}% ({typed_fields}/{total_fields})")
    
    logger.info(f"\n=== 数値型問題修正完了 ===")
    logger.info(f"成功: {success_count}件")
    logger.info(f"エラー: {error_count}件")
    
    conn.close()

if __name__ == "__main__":
    fix_numeric_type_issues()