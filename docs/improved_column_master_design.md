# Column Master 改善設計

## 現状の問題

現在の`column_master`テーブル構造：
```sql
CREATE TABLE column_master (
    file_name TEXT,
    column_name TEXT,
    data_type TEXT,           -- 最終決定型
    initial_inferred_type TEXT, -- 推論型
    encoding TEXT,
    delimiter TEXT
);
```

**問題点**:
- どの処理で`data_type`が決まったかが不明
- 推論→ルール→マッピングの適用履歴が追跡できない

## 改善案: 拡張Column Master

```sql
CREATE TABLE column_master_v2 (
    file_name TEXT,
    column_name TEXT,
    
    -- 推論結果
    initial_inferred_type TEXT,
    
    -- ルール適用結果
    rule_applied_type TEXT,
    applied_rule_name TEXT,
    
    -- 個別マッピング結果
    manual_override_type TEXT,
    override_reason TEXT,
    
    -- 最終決定型
    final_data_type TEXT,
    decision_source TEXT,  -- 'inference', 'rule', 'manual'
    
    -- メタデータ
    encoding TEXT,
    delimiter TEXT,
    last_updated DATETIME,
    
    PRIMARY KEY (file_name, column_name)
);
```

## 処理フロー

### 1. 推論段階
```sql
INSERT INTO column_master_v2 (
    file_name, column_name, 
    initial_inferred_type, 
    final_data_type, 
    decision_source
) VALUES (
    'zs65.txt', '品質検査中在庫', 
    'INTEGER', 
    'INTEGER', 
    'inference'
);
```

### 2. ルール適用段階
```sql
UPDATE column_master_v2 
SET 
    rule_applied_type = 'TEXT',
    applied_rule_name = 'sap_code_fields',
    final_data_type = 'TEXT',
    decision_source = 'rule'
WHERE file_name = 'zs65.txt' 
AND column_name LIKE '%コード%';
```

### 3. 個別マッピング段階
```sql
UPDATE column_master_v2 
SET 
    manual_override_type = 'REAL',
    override_reason = '小数点データ確認のため',
    final_data_type = 'REAL',
    decision_source = 'manual'
WHERE file_name = 'zs65.txt' 
AND column_name = '利用可能数量';
```

## 利点

### 1. トレーサビリティ
- どの処理で型が決まったかが明確
- 変更履歴の追跡が可能

### 2. デバッグ容易性
- 推論が正しいのにルールで上書きされた場合を特定
- 個別マッピングの必要性を評価

### 3. 自動化促進
- ルールでカバーできていない部分を特定
- 個別マッピングをルール化する判断材料

### 4. 品質向上
- 推論精度の評価が可能
- ルールの効果測定が可能

## 実装方針

### Phase 1: 現状分析
- 現在の`column_master`から処理種別を逆算
- `data_type`と`initial_inferred_type`の差分分析

### Phase 2: 拡張テーブル作成
- `column_master_v2`テーブル作成
- 既存データの移行ロジック実装

### Phase 3: 処理フロー更新
- analyzer.py の更新
- loader.py の更新
- GUI の更新

## 移行戦略

### 1. 既存データ分析
```sql
-- 推論のみで決まったもの
SELECT * FROM column_master 
WHERE data_type = initial_inferred_type;

-- ルールで変更されたもの（推定）
SELECT * FROM column_master 
WHERE data_type != initial_inferred_type
AND data_type IN ('TEXT', 'DATETIME');

-- 個別マッピングが必要なもの（推定）
SELECT * FROM column_master 
WHERE data_type != initial_inferred_type
AND data_type NOT IN ('TEXT', 'DATETIME');
```

### 2. 段階的移行
1. 新テーブル作成
2. 既存データ移行
3. 新フローでの処理開始
4. 旧テーブル廃止

## 期待効果

- **メンテナンス性向上**: 型決定ロジックの可視化
- **品質向上**: 推論とルールの精度向上
- **自動化促進**: 個別マッピングの削減
- **トラブルシューティング**: 問題の根本原因特定

この設計により、「推論→ルール→マッピング」の処理フローが完全に追跡可能になります。