# SQLite Data Manager - 操作マニュアル

## 概要

SQLite Data Manager は、SAP等の基幹システムから出力されたCSV/TXTファイルをSQLiteデータベースに統合し、データ型の自動修正・統一を行うツールです。

## 主な機能

### 🔧 データ型修正・統一機能
- 日付フィールドの自動DATETIME型変換
- 数値フィールドの自動REAL/INTEGER型変換
- SAP特殊形式（0パディング、後ろマイナス、小数点カンマ）の自動修正
- コード系フィールドの適切な型設定

### 📊 バッチ処理機能
- CSV形式での修正指示一括読み込み
- 進捗表示付きバッチ実行
- エラーハンドリングとロールバック機能

### 🛡️ 安全性機能
- 自動バックアップ作成
- 修正前後の整合性チェック
- 異常値検出とアラート

### 📈 レポート機能
- 修正結果の詳細レポート
- 統計情報の比較表示
- 型統一率の算出

## インストール・セットアップ

### 必要な環境
- Python 3.8以上
- SQLite3
- 必要なPythonパッケージ：
  ```bash
  pip install pandas sqlalchemy pathlib
  ```

### ファイル構成
```
sqlite-data-manager/
├── t002_data_structures.py      # データ構造定義
├── t002_rule_templates.py       # ルールテンプレート管理
├── t002_backup_system.py        # バックアップシステム
├── t004_modification_engine.py  # 修正エンジン
├── t005_sap_special_rules.py    # SAP特殊ルール処理
├── t006_batch_modification.py   # バッチ修正機能
├── t007_verification_system.py  # 検証システム
├── t008_integration_tests.py    # 統合テスト
├── pattern_rules_data.json      # パターンルール設定
├── rule_templates.json          # ルールテンプレート
└── output/master.db             # メインデータベース
```

## 基本的な使用方法

### 1. データ型修正の基本フロー

#### ステップ1: 修正対象の特定
```python
from t005_sap_special_rules import SAPSpecialRulesEngine

# SAP特殊ルールエンジンを初期化
engine = SAPSpecialRulesEngine("output/master.db")

# 後ろマイナスフィールドを検出
trailing_minus_fields = engine.detect_trailing_minus_fields()

# 小数点カンマフィールドを検出
decimal_comma_fields = engine.detect_decimal_comma_fields()

# コード系フィールドを自動識別
code_fields = engine.detect_code_fields()
```

#### ステップ2: バッチ作成と実行
```python
from t006_batch_modification import BatchModificationManager
from t002_data_structures import ModificationBatch

# バッチ修正マネージャーを初期化
manager = BatchModificationManager("output/master.db")

# テンプレートからバッチを作成
batch = manager.create_batch_from_template("sap_data_cleaning")

# バッチ実行前の検証
validation = manager.validate_batch_before_execution(batch)

if validation["valid"]:
    # 進捗表示付きでバッチ実行
    result = manager.execute_batch_with_progress(batch)
    print(f"実行結果: {result}")
```

#### ステップ3: 結果検証
```python
from t007_verification_system import VerificationSystem

# 検証システムを初期化
verification = VerificationSystem("output/master.db")

# 修正結果を検証
report = verification.verify_modification_batch(batch, backup_path)

print(f"検証結果: {report.overall_status}")
print(f"整合性チェック: {len(report.integrity_checks)}件")
```

### 2. CSV形式での一括修正

#### 修正指示CSVの作成
```csv
file_name,column_name,current_type,target_type,action,confidence,reason
sales_data.txt,amount,TEXT,REAL,type_change,high,金額フィールドをREAL型に変更
sales_data.txt,date_field,TEXT,DATETIME,date_format_fix,high,日付フィールドをDATETIME型に変更
```

#### CSV読み込みと実行
```python
# CSV形式の修正指示を読み込み
modifications = manager.load_modifications_from_csv("修正指示.csv")

# バッチを作成
batch = ModificationBatch(
    batch_id="csv_batch_001",
    name="CSV一括修正",
    description="CSV形式の修正指示による一括処理",
    modifications=modifications
)

# 実行
result = manager.execute_batch_with_progress(batch)
```

### 3. ルールテンプレートの活用

#### 利用可能なテンプレート
- `sap_data_cleaning`: SAP特殊形式の修正
- `date_normalization`: 日付形式の統一
- `numeric_conversion`: 数値型への変換
- `code_field_handling`: コードフィールドの適切な型設定

#### カスタムテンプレートの作成
```python
from t002_rule_templates import RuleTemplateManager

manager = RuleTemplateManager()

# カスタムテンプレートを追加
custom_template = {
    "name": "カスタム修正ルール",
    "description": "特定の業務要件に対応した修正ルール",
    "rules": [
        {
            "rule_id": "custom_rule_001",
            "name": "カスタムルール",
            "description": "特定パターンの修正",
            "pattern": r"^CUSTOM_(\d+)$",
            "action": "type_change",
            "target_type": "TEXT",
            "confidence_threshold": 0.8
        }
    ]
}

manager.add_custom_template("custom_rules", custom_template)
```

## 高度な機能

### バックアップとリストア

#### 自動バックアップ
```python
from t002_backup_system import BackupManager

backup_manager = BackupManager()

# バッチ実行前に自動バックアップが作成される
# 手動でバックアップを作成する場合
backup_info = backup_manager.create_backup("output/master.db", batch, "手動バックアップ")
```

#### リストア
```python
# バックアップ一覧を確認
backups = backup_manager.list_backups()

# 特定のバックアップからリストア
success = backup_manager.restore_backup("backup_20241218_143022", "output/master.db")
```

### 検証とレポート

#### 詳細検証レポート
```python
# 検証レポートの詳細情報
print(f"バッチID: {report.batch_id}")
print(f"検証時刻: {report.verification_time}")
print(f"全体ステータス: {report.overall_status}")

# 整合性チェック結果
for check in report.integrity_checks:
    status = "✅" if check.passed else "❌"
    print(f"{status} {check.check_name}: {check.message}")

# 異常値検出結果
if report.anomalies:
    print(f"異常値検出: {len(report.anomalies)}件")
    for anomaly in report.anomalies:
        print(f"  - {anomaly['type']}: {anomaly.get('message', '')}")
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. データベースロックエラー
**症状**: `database is locked` エラーが発生
**解決方法**: 
- DB Browserなどのツールを閉じる
- 他のプロセスがDBを使用していないか確認

#### 2. 文字化け問題
**症状**: 日本語フィールド名が文字化けする
**解決方法**:
```python
# エンコーディングを明示的に指定
df = pd.read_csv(file_path, encoding='cp932')
```

#### 3. メモリ不足エラー
**症状**: 大容量ファイル処理時にメモリエラー
**解決方法**:
```python
# チャンク処理を使用
for chunk in pd.read_csv(file_path, chunksize=1000):
    process_chunk(chunk)
```

#### 4. 型変換エラー
**症状**: 特定のデータで型変換が失敗
**解決方法**:
- サンプルデータを確認
- パターンルールを調整
- 手動で例外データを修正

### ログとデバッグ

#### ログレベルの設定
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### デバッグ情報の確認
```python
# 修正履歴の確認
history = engine.get_modification_history()
for entry in history:
    print(f"{entry['executed_at']}: {entry['batch_name']} - {entry['status']}")
```

## パフォーマンス最適化

### 大容量データの処理

#### バッチサイズの調整
```python
# 小さなバッチに分割して処理
batch_size = 100
for i in range(0, len(modifications), batch_size):
    batch_modifications = modifications[i:i+batch_size]
    # バッチ処理
```

#### インデックスの活用
```python
# 頻繁に検索するカラムにインデックスを作成
cursor.execute("CREATE INDEX idx_file_column ON column_master(file_name, column_name)")
```

### メモリ使用量の最適化
```python
# 不要なデータの削除
del large_dataframe
import gc
gc.collect()
```

## セキュリティ考慮事項

### データ保護
- バックアップファイルの暗号化
- アクセス権限の適切な設定
- 機密データの匿名化

### 監査ログ
- すべての修正操作をログに記録
- 修正履歴の改ざん防止
- 定期的なログのアーカイブ

## 運用ガイドライン

### 定期メンテナンス
```python
# データベース最適化
cursor.execute("VACUUM")

# 古いバックアップの削除
deleted_count = backup_manager.cleanup_old_backups(keep_days=30)
```

### 監視項目
- データベースサイズの増加
- 処理時間の変化
- エラー発生率
- 型統一率の推移

## API リファレンス

### 主要クラス

#### DataStructureManager
- `add_modification(modification)`: 修正情報を追加
- `create_batch(name, description, modifications)`: バッチを作成
- `export_to_json(file_path)`: JSON形式でエクスポート

#### ModificationEngine
- `execute_batch(batch)`: バッチを実行
- `rollback_to_backup(backup_id)`: バックアップからロールバック

#### VerificationSystem
- `verify_modification_batch(batch, backup_path)`: バッチ結果を検証

### 設定ファイル

#### pattern_rules_data.json
```json
{
  "sap_patterns": {
    "trailing_minus": "^(\\d+\\.?\\d*)-$",
    "zero_padding": "^0+(\\d+)$",
    "decimal_comma": "^(\\d+),(\\d+)$"
  },
  "datetime_formats": [
    "%Y%m%d",
    "%Y/%m/%d",
    "%Y-%m-%d"
  ]
}
```

## サポート情報

### 更新履歴
- v1.0.0: 初回リリース
- v1.1.0: SAP特殊ルール対応
- v1.2.0: バッチ処理機能追加

### 既知の制限事項
- SQLiteの型システムの制約
- 大容量ファイル（1GB以上）の処理性能
- 複雑な外部キー制約への対応

### 今後の予定機能
- Streamlitダッシュボード
- 日次バッチ処理の自動化
- クラウド対応

---

このマニュアルは継続的に更新されます。最新版は GitHub リポジトリで確認してください。