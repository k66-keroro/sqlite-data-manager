# SQLite Data Manager - トラブルシューティングガイド

## 🚨 緊急時対応

### データベース破損時の対応
1. **即座にバックアップから復旧**
   ```python
   from t002_backup_system import BackupManager
   backup_manager = BackupManager()
   
   # 最新のバックアップを確認
   backups = backup_manager.list_backups()
   latest_backup = backups[0]  # 最新のバックアップ
   
   # 復旧実行
   success = backup_manager.restore_backup(latest_backup['backup_id'], 'output/master.db')
   ```

2. **データベース整合性チェック**
   ```sql
   PRAGMA integrity_check;
   PRAGMA foreign_key_check;
   ```

### 処理が停止した場合
1. **プロセス強制終了**
   - Ctrl+C でプロセス終了
   - タスクマネージャーでPythonプロセス終了

2. **ロックファイル削除**
   ```bash
   # SQLiteロックファイルを削除
   del output\master.db-wal
   del output\master.db-shm
   ```

## ❌ エラー別対処法

### データベース関連エラー

#### `database is locked`
**原因**: 他のプロセスがデータベースを使用中
**対処法**:
1. DB Browser for SQLiteを閉じる
2. 他のPythonプロセスを終了
3. ロックファイルを削除
   ```python
   import os
   lock_files = ['output/master.db-wal', 'output/master.db-shm']
   for lock_file in lock_files:
       if os.path.exists(lock_file):
           os.remove(lock_file)
   ```

#### `no such table: table_name`
**原因**: テーブルが存在しない
**対処法**:
```python
# テーブル存在確認
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
if not cursor.fetchone():
    print(f"テーブル {table_name} が存在しません")
    # 必要に応じてテーブル作成
```

#### `no such column: column_name`
**原因**: カラムが存在しない
**対処法**:
```python
# カラム存在確認
cursor.execute(f"PRAGMA table_info({table_name})")
columns = [row[1] for row in cursor.fetchall()]
if column_name not in columns:
    print(f"カラム {column_name} が存在しません")
    print(f"利用可能なカラム: {columns}")
```

### ファイル読み込みエラー

#### `UnicodeDecodeError`
**原因**: 文字エンコーディングの不一致
**対処法**:
```python
# 複数のエンコーディングを試行
encodings = ['utf-8', 'cp932', 'shift_jis', 'iso-2022-jp']
for encoding in encodings:
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        print(f"成功: {encoding}")
        break
    except UnicodeDecodeError:
        continue
```

#### `ParserError: Error tokenizing data`
**原因**: CSV形式の問題（区切り文字、引用符など）
**対処法**:
```python
# 区切り文字を自動検出
import csv
with open(file_path, 'r', encoding='cp932') as f:
    sample = f.read(1024)
    sniffer = csv.Sniffer()
    delimiter = sniffer.sniff(sample).delimiter
    
df = pd.read_csv(file_path, delimiter=delimiter, encoding='cp932', engine='python')
```

### メモリ関連エラー

#### `MemoryError`
**原因**: メモリ不足
**対処法**:
```python
# チャンク処理で大容量ファイルを処理
chunk_size = 1000
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process_chunk(chunk)
    
# メモリ解放
import gc
gc.collect()
```

#### `OverflowError`
**原因**: 数値が範囲を超過
**対処法**:
```python
# データ型を明示的に指定
df = pd.read_csv(file_path, dtype={'large_number_field': 'str'})

# 必要に応じて後で変換
df['large_number_field'] = pd.to_numeric(df['large_number_field'], errors='coerce')
```

## 🔍 診断ツール

### システム状態チェック
```python
def system_health_check():
    """システム状態をチェック"""
    import psutil
    import sqlite3
    
    print("=== システム状態チェック ===")
    
    # メモリ使用量
    memory = psutil.virtual_memory()
    print(f"メモリ使用率: {memory.percent}%")
    print(f"利用可能メモリ: {memory.available / 1024**3:.2f} GB")
    
    # ディスク使用量
    disk = psutil.disk_usage('.')
    print(f"ディスク使用率: {disk.percent}%")
    print(f"空き容量: {disk.free / 1024**3:.2f} GB")
    
    # データベース状態
    try:
        conn = sqlite3.connect('output/master.db')
        cursor = conn.cursor()
        
        # データベースサイズ
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        print(f"データベースサイズ: {db_size / 1024**2:.2f} MB")
        
        # テーブル数
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"テーブル数: {table_count}")
        
        conn.close()
        print("データベース接続: OK")
        
    except Exception as e:
        print(f"データベース接続エラー: {e}")

system_health_check()
```

### ログ分析ツール
```python
def analyze_logs():
    """ログファイルを分析"""
    import json
    from pathlib import Path
    
    log_files = list(Path('.').glob('*.log'))
    if not log_files:
        print("ログファイルが見つかりません")
        return
    
    for log_file in log_files:
        print(f"\n=== {log_file} ===")
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        error_count = sum(1 for line in lines if 'ERROR' in line)
        warning_count = sum(1 for line in lines if 'WARNING' in line)
        
        print(f"総行数: {len(lines)}")
        print(f"エラー: {error_count}件")
        print(f"警告: {warning_count}件")
        
        # 最新のエラーを表示
        recent_errors = [line for line in lines[-100:] if 'ERROR' in line]
        if recent_errors:
            print("最新のエラー:")
            for error in recent_errors[-3:]:
                print(f"  {error.strip()}")

analyze_logs()
```

## 🛠️ 修復ツール

### データベース修復
```python
def repair_database():
    """データベースを修復"""
    import sqlite3
    import shutil
    
    # バックアップ作成
    shutil.copy2('output/master.db', 'output/master_backup.db')
    
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    try:
        # 整合性チェック
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()[0]
        
        if result != 'ok':
            print(f"整合性チェック失敗: {result}")
            
            # 修復試行
            cursor.execute("PRAGMA quick_check")
            cursor.execute("REINDEX")
            cursor.execute("VACUUM")
            
            print("データベース修復完了")
        else:
            print("データベースは正常です")
            
    except Exception as e:
        print(f"修復エラー: {e}")
        # バックアップから復元
        shutil.copy2('output/master_backup.db', 'output/master.db')
        print("バックアップから復元しました")
    
    finally:
        conn.close()

repair_database()
```

### 孤立データクリーンアップ
```python
def cleanup_orphaned_data():
    """孤立したデータをクリーンアップ"""
    conn = sqlite3.connect('output/master.db')
    cursor = conn.cursor()
    
    try:
        # column_masterに存在しないテーブルを特定
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'column_master'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        cursor.execute("SELECT DISTINCT file_name FROM column_master")
        registered_files = {row[0].replace('.txt', '').replace('.csv', '') for row in cursor.fetchall()}
        
        orphaned_tables = existing_tables - registered_files
        
        if orphaned_tables:
            print(f"孤立テーブル発見: {orphaned_tables}")
            for table in orphaned_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"削除: {table}")
        
        conn.commit()
        print("クリーンアップ完了")
        
    except Exception as e:
        print(f"クリーンアップエラー: {e}")
        conn.rollback()
    
    finally:
        conn.close()

cleanup_orphaned_data()
```

## 📊 パフォーマンス問題

### 処理速度が遅い場合

#### 原因分析
```python
import time
import cProfile

def profile_function(func, *args, **kwargs):
    """関数のプロファイリング"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    profiler.disable()
    profiler.print_stats(sort='cumulative')
    
    print(f"実行時間: {end_time - start_time:.2f}秒")
    return result
```

#### 最適化手法
1. **インデックス追加**
   ```sql
   CREATE INDEX idx_file_column ON column_master(file_name, column_name);
   CREATE INDEX idx_data_type ON column_master(data_type);
   ```

2. **バッチサイズ調整**
   ```python
   # 小さなバッチで処理
   batch_size = 50
   for i in range(0, len(modifications), batch_size):
       batch_mods = modifications[i:i+batch_size]
       process_batch(batch_mods)
   ```

3. **並列処理**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   with ThreadPoolExecutor(max_workers=4) as executor:
       futures = [executor.submit(process_file, file) for file in files]
       results = [future.result() for future in futures]
   ```

### メモリ使用量が多い場合

#### メモリ監視
```python
import tracemalloc

def monitor_memory():
    """メモリ使用量を監視"""
    tracemalloc.start()
    
    # 処理実行
    process_data()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"現在のメモリ使用量: {current / 1024**2:.2f} MB")
    print(f"ピーク時メモリ使用量: {peak / 1024**2:.2f} MB")
    
    tracemalloc.stop()
```

#### メモリ最適化
```python
def optimize_memory():
    """メモリ使用量を最適化"""
    import gc
    
    # 不要な変数を削除
    del large_dataframe
    
    # ガベージコレクション実行
    gc.collect()
    
    # DataFrameのメモリ使用量を削減
    df = df.copy()  # フラグメンテーション解消
    
    # カテゴリ型を使用
    df['category_column'] = df['category_column'].astype('category')
```

## 🔧 設定問題

### 設定ファイルエラー

#### pattern_rules_data.json の修復
```python
def repair_pattern_rules():
    """パターンルール設定を修復"""
    import json
    
    default_rules = {
        "sap_patterns": {
            "trailing_minus": r"^(\d+\.?\d*)-$",
            "zero_padding": r"^0+(\d+)$",
            "decimal_comma": r"^(\d+),(\d+)$"
        },
        "datetime_formats": [
            "%Y%m%d",
            "%Y/%m/%d",
            "%Y-%m-%d"
        ],
        "unregistered_files": {}
    }
    
    try:
        with open('pattern_rules_data.json', 'r', encoding='utf-8') as f:
            current_rules = json.load(f)
        
        # 不足している設定を補完
        for key, value in default_rules.items():
            if key not in current_rules:
                current_rules[key] = value
                print(f"追加: {key}")
        
        # 修復済み設定を保存
        with open('pattern_rules_data.json', 'w', encoding='utf-8') as f:
            json.dump(current_rules, f, ensure_ascii=False, indent=2)
        
        print("パターンルール設定修復完了")
        
    except Exception as e:
        print(f"設定修復エラー: {e}")
        # デフォルト設定で上書き
        with open('pattern_rules_data.json', 'w', encoding='utf-8') as f:
            json.dump(default_rules, f, ensure_ascii=False, indent=2)
        print("デフォルト設定で復旧しました")

repair_pattern_rules()
```

## 📞 サポート情報

### ログ収集
問題報告時は以下の情報を収集してください：

```python
def collect_support_info():
    """サポート用情報を収集"""
    import platform
    import sys
    import sqlite3
    
    info = {
        "system": {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture()
        },
        "database": {},
        "files": {},
        "errors": []
    }
    
    # データベース情報
    try:
        conn = sqlite3.connect('output/master.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        info["database"]["table_count"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM column_master")
        info["database"]["field_count"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        info["errors"].append(f"Database error: {e}")
    
    # ファイル情報
    import os
    for file_name in ['pattern_rules_data.json', 'rule_templates.json']:
        info["files"][file_name] = os.path.exists(file_name)
    
    # 情報をファイルに保存
    import json
    with open('support_info.json', 'w', encoding='utf-8') as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    
    print("サポート情報を support_info.json に保存しました")

collect_support_info()
```

### よくある質問 (FAQ)

#### Q: 処理が途中で止まってしまいます
A: 以下を確認してください：
- メモリ使用量（8GB以上推奨）
- ディスク容量（データベースサイズの3倍以上）
- 他のプロセスによるDBロック

#### Q: 文字化けが発生します
A: エンコーディング設定を確認：
```python
# 日本語ファイルの場合
df = pd.read_csv(file_path, encoding='cp932')
```

#### Q: バックアップから復旧できません
A: バックアップファイルの整合性を確認：
```python
backup_manager.verify_backup_integrity(backup_info)
```

### 緊急連絡先
- GitHub Issues: https://github.com/k66-keroro/sqlite-data-manager/issues
- 技術サポート: 開発チームまでお問い合わせください

---

このガイドで解決しない問題がある場合は、support_info.json と共に問題を報告してください。