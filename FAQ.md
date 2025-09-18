# SQLite Data Manager - よくある質問 (FAQ)

## 🔧 基本的な使用方法

### Q1: SQLite Data Manager とは何ですか？
**A:** SAP等の基幹システムから出力されたCSV/TXTファイルをSQLiteデータベースに統合し、データ型の自動修正・統一を行うPythonツールです。特にSAP特有のデータ形式（0パディング、後ろマイナス、小数点カンマ）の自動修正に対応しています。

### Q2: どのようなファイル形式に対応していますか？
**A:** 以下の形式に対応しています：
- CSV形式（カンマ区切り）
- TSV形式（タブ区切り）
- TXT形式（各種区切り文字）
- エンコーディング：UTF-8, CP932, Shift_JIS

### Q3: 最低限必要なファイルは何ですか？
**A:** 以下のファイルが必要です：
- `output/master.db` - メインデータベース
- `pattern_rules_data.json` - パターンルール設定
- 各種Pythonモジュール（t002_*.py, t004_*.py など）

## 📊 データ処理関連

### Q4: どのような型変換が自動で行われますか？
**A:** 以下の変換が自動実行されます：
- **日付データ**: `20241218` → `2024-12-18 00:00:00.000000` (DATETIME型)
- **数値データ**: `"123.45"` → `123.45` (REAL型)
- **整数データ**: `"123"` → `123` (INTEGER型)
- **0パディング**: `"0001234"` → `"1234"` (適切な型)
- **後ろマイナス**: `"123.45-"` → `"-123.45"` (REAL型)
- **小数点カンマ**: `"123,45"` → `"123.45"` (REAL型)

### Q5: コード系フィールドが数値型に変換されてしまいます
**A:** コード系フィールドは意図的にTEXT型で保持されます：
```python
# 品目コード、伝票番号などは自動的にTEXT型として識別
code_fields = ['品目コード', '受注伝票番号', '得意先コード']
```
0始まりのコードは先頭の0が重要な意味を持つため、TEXT型で保持されます。

### Q6: 大容量ファイルの処理でメモリエラーが発生します
**A:** チャンク処理を使用してください：
```python
# 大容量ファイルをチャンクで処理
chunk_size = 1000
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process_chunk(chunk)
```

## 🛠️ 設定とカスタマイズ

### Q7: 独自のパターンルールを追加できますか？
**A:** はい、可能です：
```python
from t002_rule_templates import RuleTemplateManager

manager = RuleTemplateManager()

# カスタムテンプレートを追加
custom_template = {
    "name": "カスタムルール",
    "rules": [{
        "rule_id": "custom_001",
        "pattern": r"^CUSTOM_(\d+)$",
        "action": "type_change",
        "target_type": "TEXT"
    }]
}

manager.add_custom_template("custom_rules", custom_template)
```

### Q8: 特定のファイルだけ処理したい場合は？
**A:** ファイルフィルタを使用できます：
```python
# 特定ファイルのみ処理
target_files = ['sales_data.txt', 'customer_data.txt']
batch = manager.create_batch_from_template("sap_data_cleaning", target_files)
```

### Q9: 処理結果を元に戻すことはできますか？
**A:** はい、バックアップ機能があります：
```python
from t002_backup_system import BackupManager

backup_manager = BackupManager()

# バックアップ一覧を確認
backups = backup_manager.list_backups()

# 特定のバックアップから復旧
success = backup_manager.restore_backup(backup_id, "output/master.db")
```

## ❌ エラー対処

### Q10: "database is locked" エラーが発生します
**A:** 以下の手順で解決してください：
1. DB Browser for SQLiteなどのツールを閉じる
2. 他のPythonプロセスを終了
3. ロックファイルを削除：
```bash
del output\master.db-wal
del output\master.db-shm
```

### Q11: 文字化けが発生します
**A:** エンコーディングを明示的に指定してください：
```python
# 日本語ファイルの場合
df = pd.read_csv(file_path, encoding='cp932')

# 複数のエンコーディングを試行
encodings = ['utf-8', 'cp932', 'shift_jis']
for encoding in encodings:
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        break
    except UnicodeDecodeError:
        continue
```

### Q12: "no such table" エラーが発生します
**A:** テーブル名の確認を行ってください：
```python
# 存在するテーブル一覧を確認
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("存在するテーブル:", [t[0] for t in tables])
```

## 🚀 パフォーマンス

### Q13: 処理速度を向上させる方法は？
**A:** 以下の最適化手法があります：
```python
# 1. インデックス追加
cursor.execute("CREATE INDEX idx_file_column ON column_master(file_name, column_name)")

# 2. バッチサイズ調整
batch_size = 50  # デフォルトより小さく

# 3. 並列処理
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(process_file, files)
```

### Q14: メモリ使用量を削減するには？
**A:** 以下の方法が効果的です：
```python
# 1. 不要な変数を削除
del large_dataframe
import gc
gc.collect()

# 2. カテゴリ型を使用
df['category_column'] = df['category_column'].astype('category')

# 3. チャンク処理
for chunk in pd.read_csv(file_path, chunksize=1000):
    process_chunk(chunk)
```

## 📋 運用・保守

### Q15: 定期的なメンテナンスは必要ですか？
**A:** 以下のメンテナンスを推奨します：
```python
# 月次メンテナンス
def monthly_maintenance():
    # データベース最適化
    cursor.execute("VACUUM")
    
    # 古いバックアップ削除
    backup_manager.cleanup_old_backups(keep_days=30)
    
    # 統計情報更新
    cursor.execute("ANALYZE")
```

### Q16: ログはどこに保存されますか？
**A:** 以下の場所にログが保存されます：
- 修正履歴: `modification_history.json`
- 検証レポート: `verification_reports/` フォルダ
- バックアップ情報: `backups/backup_index.json`

### Q17: 設定ファイルが破損した場合は？
**A:** 自動修復機能があります：
```python
def repair_config():
    # pattern_rules_data.json の修復
    from t002_rule_templates import RuleTemplateManager
    manager = RuleTemplateManager()
    manager.create_default_templates()  # デフォルト設定で復旧
```

## 🔍 トラブルシューティング

### Q18: 処理が途中で止まってしまいます
**A:** 以下を確認してください：
1. **メモリ使用量**: 8GB以上推奨
2. **ディスク容量**: データベースサイズの3倍以上
3. **プロセス監視**: タスクマネージャーでCPU使用率確認

### Q19: 型変換が期待通りに動作しません
**A:** デバッグ情報を確認してください：
```python
# パターンマッチングのテスト
from t002_rule_templates import RuleTemplateManager
manager = RuleTemplateManager()

test_data = ["0001", "0002", "ABC123"]
validation = manager.validate_rule_pattern(r"^0+(\d+)$", test_data)
print(f"マッチ率: {validation['match_rate']}")
print(f"マッチしたデータ: {validation['matches']}")
```

### Q20: バックアップファイルが破損しているようです
**A:** 整合性チェックを実行してください：
```python
# バックアップの整合性確認
for backup in backup_manager.list_backups():
    integrity = backup_manager.verify_backup_integrity(backup)
    print(f"{backup['backup_id']}: {'OK' if integrity else 'NG'}")
```

## 📈 高度な使用方法

### Q21: CSV形式で修正指示を一括実行できますか？
**A:** はい、可能です：
```csv
file_name,column_name,current_type,target_type,action,confidence,reason
sales.txt,amount,TEXT,REAL,type_change,high,金額フィールド
sales.txt,date,TEXT,DATETIME,date_format_fix,high,日付フィールド
```

```python
# CSV読み込みと実行
modifications = manager.load_modifications_from_csv("修正指示.csv")
batch = ModificationBatch("csv_batch", "CSV一括修正", modifications)
result = manager.execute_batch_with_progress(batch)
```

### Q22: 独自の検証ルールを追加できますか？
**A:** VerificationSystemを拡張できます：
```python
class CustomVerificationSystem(VerificationSystem):
    def custom_business_rule_check(self, batch):
        # 独自のビジネスルール検証
        pass
```

### Q23: 処理結果をレポート形式で出力できますか？
**A:** 検証レポートが自動生成されます：
```python
# 詳細レポートの生成
report = verification_system.verify_modification_batch(batch)

# レポート内容
print(f"全体ステータス: {report.overall_status}")
print(f"整合性チェック: {len(report.integrity_checks)}件")
print(f"異常値検出: {len(report.anomalies)}件")
```

## 🔮 今後の機能

### Q24: 今後追加予定の機能はありますか？
**A:** 以下の機能を開発予定です：
- **Streamlitダッシュボード**: Web UIでの操作
- **日次バッチ処理**: スケジュール実行
- **クラウド対応**: AWS/Azure対応
- **API機能**: REST API提供

### Q25: 機能要望はどこに送れますか？
**A:** GitHub Issuesで受け付けています：
- リポジトリ: https://github.com/k66-keroro/sqlite-data-manager
- Issues: 機能要望やバグ報告
- Discussions: 使用方法の質問

## 📞 サポート

### Q26: 技術サポートはありますか？
**A:** 以下のサポートを提供しています：
- **GitHub Issues**: バグ報告・機能要望
- **ドキュメント**: 操作マニュアル・トラブルシューティングガイド
- **サンプルコード**: 実装例の提供

### Q27: 商用利用は可能ですか？
**A:** ライセンス条項に従って利用可能です。詳細はLICENSEファイルを確認してください。

---

## 📚 関連ドキュメント

- [操作マニュアル](OPERATION_MANUAL.md)
- [トラブルシューティングガイド](TROUBLESHOOTING_GUIDE.md)
- [README](README.md)

## 🔄 更新情報

このFAQは継続的に更新されます。最新版はGitHubリポジトリで確認してください。

**最終更新**: 2024年12月18日