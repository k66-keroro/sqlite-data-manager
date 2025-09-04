# SQLite Data Manager - System Design

## システム概要

### アーキテクチャ
```
[SAP生産データ] → [ファイル取り込み] → [型推定・正規化] → [SQLite DB] → [Streamlit Dashboard]
       ↓              ↓                    ↓              ↓            ↓
   - 40+ファイル    - エンコーディング     - 2,400+項目    - 統合DB     - 可視化
   - 複数形式      - 区切り文字検出       - 型統合        - 履歴管理   - 分析
   - 日次更新      - 異常検出             - 重複排除      - パフォーマンス最適化
```

## データフロー設計

### Phase 1: データ取り込み・型推定 ✅
```python
# 現在の処理フロー
1. ファイル検出 (analyzer.py)
2. エンコーディング判定 (loader.py) 
3. 区切り文字検出
4. データ型推定 (infer_sqlite_type)
5. SQLite格納
6. 比較レポート出力 (compare_report.csv)
```

### Phase 2: データ型統合・正規化 🚧 (現在作業中)
```python
# 予定する処理フロー
1. 型比較結果の分析
2. 同一データの重複検出
3. SAPルール適用 (0パディング等)
4. 手動修正のサポート
5. 統合スキーマの生成
```

### Phase 3: ダッシュボード 📋 (未着手)
```python
# Streamlit ダッシュボード
1. データ概要表示
2. 型統合状況の可視化  
3. 異常検出アラート
4. データ品質メトリクス
```

## データベース設計

### 現在のテーブル構造
```sql
-- マスタテーブル (analyzer.pyで作成)
column_master (
    file_name TEXT,
    column_name TEXT, 
    data_type TEXT,
    encoding TEXT,
    delimiter TEXT,
    PRIMARY KEY (file_name, column_name)
)

-- 各ファイルのテーブル (loader.pyで作成)
-- テーブル名: ファイル名から生成
-- 列: すべてTEXT型で格納
```

### 予定する拡張テーブル
```sql
-- 型統合管理テーブル
type_mapping (
    source_file TEXT,
    source_column TEXT,
    target_type TEXT,
    conversion_rule TEXT,
    manual_override BOOLEAN,
    created_at DATETIME,
    updated_at DATETIME
)

-- データ品質管理
data_quality (
    table_name TEXT,
    column_name TEXT,
    quality_score REAL,
    issues TEXT,
    checked_at DATETIME
)

-- ファイル処理履歴
file_processing_log (
    file_name TEXT,
    processing_date DATETIME,
    status TEXT,
    error_message TEXT,
    records_processed INTEGER
)
```

## SAPデータの特殊ルール

### 識別パターン
```python
# コード系フィールド (必ずTEXT)
CODE_PATTERNS = ["CD", "コード", "ID", "NO", "番号", "指図", "ネットワーク"]

# 0パディング検出
def has_zero_padding(series):
    return any(str(x).startswith("0") and str(x).isdigit() for x in series)

# 後ろマイナス検出 (SAP特有)  
def has_trailing_minus(series):
    return any(str(x).endswith("-") for x in series)
```

### 統合ルール
1. **同一データの重複**: ファイル名が違っても内容が同じ列を統合
2. **0パディングの統一**: 桁数を統一するかTEXT型に統一するか判断
3. **数値の正規化**: 後ろマイナスを前マイナスに変換

## エラーハンドリング戦略

### ファイル読み込みエラー
- エンコーディングエラー → 複数候補で再試行
- 区切り文字エラー → デフォルト値で継続
- データ形式エラー → ログ出力して次ファイル処理

### データ型推定エラー
- 混在型 → より安全な型を選択 (TEXT優先)
- 不明な型 → TEXTでフォールバック
- NULL値多数 → NULLable型として扱う

## パフォーマンス最適化

### 大容量ファイル対応
```python
# チャンク読み込み
for chunk in pd.read_csv(file_path, chunksize=10000):
    process_chunk(chunk)

# インデックス最適化
CREATE INDEX idx_file_column ON column_master(file_name, column_name);
```

### メモリ使用量削減
- 型推定は先頭1000行のサンプリング
- 不要なカラムの早期削除
- DataFrame の dtype 最適化

## 監視・メンテナンス

### 日次監視項目
- ファイル処理成功率
- データ型推定精度
- SQLite DB サイズ
- 新ファイル検出

### 定期メンテナンス
- VACUUM によるDB最適化
- 古いログファイルの削除  
- 統計情報の更新
