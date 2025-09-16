k# SQLite Data Manager - 操作マニュアル

## 📖 目次
1. [システム概要](#システム概要)
2. [セットアップ・初期化](#セットアップ初期化)
3. [基本操作](#基本操作)
4. [データ型修正の手順](#データ型修正の手順)
5. [トラブルシューティング](#トラブルシューティング)
6. [ファイル構成](#ファイル構成)
7. [FAQ](#faq)

---

## システム概要

SAP生産データの自動取り込み・型推定・正規化を行うSQLite基盤のデータ管理システムです。

### 主な機能
- **データ自動読み込み**: 40種類のSAPデータファイルを一括処理
- **型推定・統合**: 2,400+フィールドの自動型推定と統合
- **データ正規化**: エンコーディング、区切り文字、SAPデータ特殊形式の統一
- **SQLite DB作成**: 統合されたマスターデータベースの生成

### システム要件
- Python 3.8以上
- 必要なライブラリ: pandas, sqlite3, chardet
- 推奨メモリ: 8GB以上
- ディスク容量: 最低5GB（データサイズによる）

---

## セットアップ・初期化

### 1. 開発環境での初期セットアップ

```bash
# リポジトリのクローン
git clone https://github.com/k66-keroro/sqlite-data-manager.git
cd sqlite-data-manager

# 必要なライブラリのインストール
pip install -r requirements.txt

# 開発環境の初期化
python init_dev.py
```

### 2. 本番環境での初期セットアップ

```bash
# 本番環境の初期化
python init_prod.py
```

### 3. ディレクトリ構成の確認

初期化後、以下の構成になっているか確認してください：

```
sqlite-data-manager/
├── main.py              # メインエントリポイント
├── config.py           # 設定ファイル
├── analyzer.py         # データ分析・型推定
├── loader.py           # ファイル読み込み
├── output/             # 出力ディレクトリ
│   ├── master.db      # SQLiteデータベース
│   └── compare_report.csv # 型比較結果
└── テキスト/           # 入力データディレクトリ（40ファイル）
```

---

	## 基本操作
	
	### 1. システムの実行
	
#### 基本実行（全工程）
```bash
# 1. 開発環境初期化（初回のみ）
python main.py init_dev

# 2. データファイル読み込み＋SQLite格納  
python main.py load

# 3. データ分析＋レポート生成
python main.py analyze
```

**注意**: `python main.py`だけでは実行されません。上記3段階の手順が必要です。

#### モジュール別実行
```bash
# データ読み込みのみ
python loader.py

# データ分析のみ
python analyzer.py

# データマッピングのみ
python mapper.py
```

### 2. 実行結果の確認

#### ログファイルの確認

**Windows環境:**
```powershell
# 最新のログを表示
Get-Content output/process.log -Tail 20

# リアルタイム監視（PowerShell 3.0以降）
Get-Content output/process.log -Wait -Tail 10
```

**Linux/Mac環境:**
```bash
# 最新のログを表示
tail -f output/process.log
```

#### データベースの確認

##### SQLiteコマンドラインでの確認
```bash
# SQLiteデータベースに接続
sqlite3 output/master.db

# テーブル一覧表示
.tables

# テーブル構造確認
.schema file_structures

# データ件数確認  
SELECT COUNT(*) FROM file_structures;

# 最初の10件表示
SELECT * FROM file_structures LIMIT 10;

# 終了
.quit
```

##### Pythonスクリプトでの確認
```bash
# t001_analyzer.pyで詳細分析
python t001_analyzer.py

# t002_analyzer.pyで問題特定
python t002_analyzer.py
```

#### 処理結果レポートの確認

**Windows環境:**
```powershell
# CSVファイルをExcelで開く
start output/compare_report.csv

# テキストエディタで開く
notepad output/compare_report.csv

# PowerShellで内容確認
Import-Csv output/compare_report.csv | Select-Object -First 10
```

**Linux/Mac環境:**
```bash
# CSVファイルを開く
open output/compare_report.csv   # Mac
xdg-open output/compare_report.csv  # Linux

# テキストで確認
head -10 output/compare_report.csv
```

### 3. 設定の変更

#### config.py の主要設定項目

```python
# データディレクトリ
DATA_DIR = "テキスト"

# 出力ディレクトリ
OUTPUT_DIR = "output"

# デフォルトエンコーディング
DEFAULT_ENCODING = "shift_jis"

# 処理対象ファイル数
MAX_FILES = 40

# メモリ制限（MB）
MEMORY_LIMIT = 4096
```

---

## GUIでの操作手順 (推奨)

本システムには、データ型のルールを直感的に編集し、データベースに適用するためのWebベースのGUIが用意されています。コマンドライン操作よりもこちらの使用を推奨します。

### 1. GUIの起動

プロジェクトのルートディレクトリで、以下のコマンドを実行します。

```bash
streamlit run streamlit_app.py
```

実行後、Webブラウザで http://localhost:8501 のようなアドレスが自動的に開きます。

### 2. 操作フロー

GUIでのデータ処理は、以下の3ステップで行います。

#### ステップ1: パターンルールの編集

画面左側のサイドバーにある「パターンルール管理」セクションで、データ型の判定ルールを編集します。

- **未登録ファイルルール**: 未知のファイルに対するエンコーディングや区切り文字を指定します。
- **日付パターンルール**: 日付と判定させたい文字列の**見た目**のパターン（正規表現）を追加・編集します。
- **日付フォーマット管理**: 日付文字列を**実際に日付として解釈**するためのフォーマット文字列（例: `%Y-%m-%d`）を追加・編集します。このリストにあるフォーマットで解釈できない文字列は、日付とみなされません。
- **ビジネスロジックルール**: `コード` や `金額` といった特定のキーワードを含む列名が、どのデータ型になるべきかを定義します。

ルールを追加・編集・削除すると、自動的に設定ファイル(`pattern_rules_data.json`)に保存されます。

#### ステップ2: ルール適用とマスタ更新

ルールを編集したら、その内容をデータベースのスキーマ定義（マスタ）に反映させる必要があります。

メイン画面の「**ルール適用とマスタ更新**」セクションにある「**最新ルールを適用してマスタを更新**」ボタンをクリックします。

これにより、以下の処理が実行されます。
1. `テキスト/` ディレクトリ内の全ファイルをスキャンします。
2. ステップ1で編集した最新のルールに基づいて、各ファイルの各列のデータ型を再判定します。
3. 判定結果が、データベース内の `column_master` テーブルに保存されます。ここには、どのファイルのどの列がどのデータ型であるべきかの情報が格納されます。

#### ステップ3: データロードと比較

マスタ情報が更新されたら、実際にデータを読み込み、テーブルを作成します。

「**データロードと比較**」セクションの「**データロードと比較実行**」ボタンをクリックします。

この操作により、`loader.py` が実行され、更新された `column_master` の定義に従って各データファイルが読み込まれ、SQLiteデータベース内にテーブルとして保存されます。

### 3. トラブルシューティング

- **GUIが起動しない**: `streamlit` ライブラリがインストールされているか確認してください (`pip install streamlit`)。
- **ルールを更新してもデータ型が変わらない**: ステップ2の「**最新ルールを適用してマスタを更新**」を必ずクリックしたか確認してください。この操作を行わないと、ルールへの変更がデータベース定義に反映されません。

---

## データ型修正の手順 (コマンドライン)

### T001分析ツール（詳細分析）

```bash
# compare_report.csvの詳細分析
python t001_analyzer.py
```

**出力結果**:
- 型不一致の詳細パターン分析
- SAPデータ特殊ルール（後ろマイナス、0パディング）の検出
- 重複フィールドの特定
- 一致率の算出

### T002分析ツール（問題特定）

```bash  
# 4つの主要問題パターンの特定
python t002_analyzer.py
```

**特定される問題**:
1. **未登録型**: Inferred_Type_未登録のファイル
2. **DATETIME問題**: DATETIMEと判定されるべきだがTEXTになってしまう問題
3. **INTEGER問題**: TEXT変更が必要なINTEGER型  
4. **保管場所コード**: 数値だがTEXTが適切なフィールド

### 1. 型比較結果の確認

```bash
# compare_report.csvを開いて内容確認
python -c "import pandas as pd; df=pd.read_csv('output/compare_report.csv'); print(df.head(10))"
```

### 2. 手動修正が必要な箇所の特定

#### 優先度の高い修正項目
1. **重複フィールド**: 同一データで異なる型が推定されている
2. **SAPコード系**: 0パディングが必要な数値データ
3. **後ろマイナス**: SAP特有の負数表現
4. **日付フィールド**: 複数の日付フォーマット混在

### 3. 型修正の実行

#### 個別修正
```bash
# 特定のファイル・フィールドを修正
python analyzer.py --fix-field "ファイル名" "フィールド名" "新しい型"
```

#### 一括修正
```bash
# 修正ルールCSVを使用して一括修正
python analyzer.py --batch-fix modification_rules.csv
```

### 4. 修正結果の確認

```bash
# 修正後の型比較レポート再生成
python analyzer.py --regenerate-report

# 修正前後の比較
python -c "
import pandas as pd
before = pd.read_csv('output/compare_report_backup.csv')
after = pd.read_csv('output/compare_report.csv')
print('修正件数:', len(before) - len(after))
"
```

---

## トラブルシューティング

### よくある問題と解決法

#### 1. ファイル読み込みエラー

**症状**: `UnicodeDecodeError` や `FileNotFoundError`
```bash
ERROR: ファイル読み込み失敗: テキスト/xxx.csv
```

**解決法**:
```bash
# エンコーディング確認
python -c "import chardet; print(chardet.detect(open('テキスト/xxx.csv', 'rb').read()))"

# 手動でエンコーディングを指定
python loader.py --encoding utf-8 --file テキスト/xxx.csv
```

#### 2. メモリ不足エラー

**症状**: `MemoryError` や処理が途中で停止
```bash
ERROR: メモリ不足により処理を中断します
```

**解決法**:
```bash
# 分割処理モードで実行
python main.py --chunk-size 1000

# メモリ制限を調整
python main.py --memory-limit 2048
```

#### 3. データベース接続エラー

**症状**: SQLiteデータベースにアクセスできない
```bash
ERROR: database is locked
```

**解決法**:
```bash
# データベースファイルの権限確認
ls -la output/master.db

# プロセスの確認・終了
ps aux | grep python
kill [プロセスID]

# データベースの修復
sqlite3 output/master.db "PRAGMA integrity_check;"
```

#### 4. 型推定の精度が低い

**症状**: 多くのフィールドが `TEXT` 型になってしまう

**解決法**:
```bash
# サンプルサイズを増加
python analyzer.py --sample-size 10000

# 型推定ルールを調整
python analyzer.py --strict-numeric True
```

### 緊急時の対応

#### データベースのバックアップ

**Windows環境:**
```powershell
# 手動バックアップ
$date = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "output/master.db" "output/master_backup_$date.db"

# Pythonスクリプトでバックアップ
python -c "
import shutil
import datetime
backup_name = f'output/master_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db'
shutil.copy('output/master.db', backup_name)
print(f'バックアップ作成: {backup_name}')
"
```

**Linux/Mac環境:**
```bash
# 毎日の自動バックアップ
cp output/master.db output/master_$(date +%Y%m%d).db

# 手動バックアップ
python -c "
import shutil
import datetime
backup_name = f'output/master_backup_{datetime.datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db'
shutil.copy('output/master.db', backup_name)
print(f'バックアップ作成: {backup_name}')
"
```

#### システムの初期化

**Windows環境:**
```powershell
# 出力ディレクトリをクリア
Remove-Item -Path "output/*" -Recurse -Force

# 初期化スクリプト実行
python init_dev.py
```

**Linux/Mac環境:**
```bash
# 出力ディレクトリをクリア
rm -rf output/*

# 初期化スクリプト実行
python init_dev.py
```

---

## ファイル構成

### コアファイル

| ファイル名 | 役割 | 手動編集 |
|------------|------|----------|
| `main.py` | メインエントリポイント | 🚫 |
| `config.py` | 設定管理 | ✅ |
| `analyzer.py` | データ分析・型推定 | 🚫 |
| `loader.py` | ファイル読み込み | 🚫 |
| `mapper.py` | データマッピング | 🚫 |
| `db.py` | データベース操作 | 🚫 |

### 設定・データファイル

| ファイル名 | 役割 | 手動編集 |
|------------|------|----------|
| `requirements.txt` | 依存ライブラリ | ✅ |
| `テキスト/` | 入力データディレクトリ | ✅ |
| `output/master.db` | SQLiteデータベース | 🚫 |
| `output/compare_report.csv` | 型比較結果 | 📖 |

### ドキュメント

| ファイル名 | 役割 | 更新頻度 |
|------------|------|----------|
| `README.md` | プロジェクト概要 | 定期 |
| `MANUAL.md` | 操作マニュアル | 定期 |
| `claude.md` | 開発状況記録 | 日次 |
| `tasks.md` | タスク管理 | 日次 |

---

## FAQ

### Q1: 処理時間はどのくらいかかりますか？
**A**: データサイズによりますが、標準的な40ファイル（合計200MB程度）で約15-30分です。

### Q2: 新しいファイルが追加された場合の対応は？
**A**: `テキスト/` ディレクトリにファイルを配置後、`python main.py` で自動的に処理されます。

### Q3: エラーが発生した場合、どこから再開できますか？
**A**: 各段階で中間ファイルが保存されるため、`--resume` オプションで途中から再開可能です。

### Q4: データの整合性はどう確認しますか？
**A**: `output/compare_report.csv` で型の一貫性、`output/process.log` で処理ログを確認してください。

### Q5: 手動修正が多すぎる場合は？
**A**: Phase 1のT002-T006で自動修正ツールを開発予定です。現在は優先度の高いものから手動対応してください。

### Q6: システムの性能を改善するには？
**A**: `config.py` でメモリ制限やチャンクサイズを調整、またはSSDの使用を推奨します。

---

## サポート情報

### 開発者連絡先
- **GitHub**: https://github.com/k66-keroro/sqlite-data-manager
- **Issues**: GitHubのIssuesページで質問・要望を受付

### 更新履歴
- **2024-XX-XX**: 初版作成
- **2024-XX-XX**: GitHub連携追加
- **2024-XX-XX**: T001-T006対応