#!/usr/bin/env python3
"""
すべての0パディング問題を包括的に修正
"""

import sqlite3
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_all_zero_padding():
    """すべての0パディング問題を包括的に修正"""
    
    logger.info("=== 全0パディング修正開始 ===")
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    # 0パディングの正規表現パターン
    zero_padding_pattern = r'^0+(\d+)$'
    
    # ZS58MONTHテーブルの全番号系フィールドを修正
    target_fields = [
        '受注伝票番号', '受注明細番号', '請求伝票番号', '請求明細番号',
        '出荷伝票番号', '出荷明細番号', '得意先発注番号', 
        '出荷先郵便番号', '出荷先電話番号'
    ]
    
    total_fixed = 0
    
    for column_name in target_fields:
        logger.info(f"修正中: ZS58MONTH.{column_name}")
        
        try:
            # 0パディングデータを取得
            cursor.execute(f"SELECT rowid, {column_name} FROM ZS58MONTH WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
            zero_padded_rows = cursor.fetchall()
            
            # Pythonで正規表現フィルタリング
            filtered_rows = []
            for rowid, value in zero_padded_rows:
                # 電話番号は特別処理（0で始まるのが正常）
                if '電話番号' in column_name:
                    # 0562-40-4571 のような形式は除外
                    if '-' in str(value):
                        continue
                
                if re.match(zero_padding_pattern, str(value)):
                    filtered_rows.append((rowid, value))
            
            logger.info(f"  0パディングデータ: {len(filtered_rows)}件")
            
            if filtered_rows:
                # サンプル表示
                for i, (rowid, value) in enumerate(filtered_rows[:3], 1):
                    match = re.match(zero_padding_pattern, str(value))
                    if match:
                        cleaned_value = match.group(1)
                        logger.info(f"    例{i}: {value} → {cleaned_value}")
                
                # 実際の修正実行
                fixed_count = 0
                for rowid, value in filtered_rows:
                    match = re.match(zero_padding_pattern, str(value))
                    if match:
                        cleaned_value = match.group(1)
                        
                        # 更新実行
                        cursor.execute(f"UPDATE ZS58MONTH SET {column_name} = ? WHERE rowid = ?", 
                                     (cleaned_value, rowid))
                        fixed_count += 1
                
                logger.info(f"  修正完了: {fixed_count}件")
                total_fixed += fixed_count
            
        except Exception as e:
            logger.error(f"エラー: ZS58MONTH.{column_name} - {e}")
    
    # 変更をコミット
    conn.commit()
    
    # 修正結果の確認
    logger.info("\n修正結果の確認:")
    logger.info("-" * 50)
    
    for column_name in target_fields[:5]:  # 最初の5フィールドのみ確認
        try:
            cursor.execute(f"SELECT {column_name} FROM ZS58MONTH WHERE {column_name} IS NOT NULL LIMIT 5")
            samples = [row[0] for row in cursor.fetchall()]
            logger.info(f"  {column_name}: {samples}")
            
            # 0パディングが残っているかチェック
            cursor.execute(f"SELECT COUNT(*) FROM ZS58MONTH WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
            potential_remaining = cursor.fetchone()[0]
            
            # 電話番号は除外して正確にチェック
            if potential_remaining > 0:
                cursor.execute(f"SELECT {column_name} FROM ZS58MONTH WHERE {column_name} LIKE '0%' AND LENGTH({column_name}) > 1")
                potential_values = [row[0] for row in cursor.fetchall()]
                
                remaining_count = 0
                for v in potential_values:
                    # 電話番号の特別処理
                    if '電話番号' in column_name and '-' in str(v):
                        continue
                    if re.match(zero_padding_pattern, str(v)):
                        remaining_count += 1
            else:
                remaining_count = 0
            
            if remaining_count > 0:
                logger.warning(f"    ⚠️  まだ0パディングが残っています: {remaining_count}件")
            else:
                logger.info(f"    ✅ 0パディング修正完了")
                
        except Exception as e:
            logger.error(f"確認エラー: {column_name} - {e}")
    
    logger.info(f"\n=== 全0パディング修正完了 ===")
    logger.info(f"総修正件数: {total_fixed}件")
    
    conn.close()

if __name__ == "__main__":
    fix_all_zero_padding()