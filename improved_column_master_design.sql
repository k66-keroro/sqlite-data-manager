-- 改善されたcolumn_master設計

CREATE TABLE column_master (
    file_name TEXT,
    column_name TEXT,
    
    -- 推論情報
    inferred_type TEXT,           -- システム推論値
    inferred_confidence REAL,     -- 推論の信頼度 (0.0-1.0)
    
    -- ルール適用情報
    rule_applied TEXT,            -- 適用されたルール名 (NULL=推論のみ)
    rule_type TEXT,               -- ルール種別 ('pattern', 'business', 'sap')
    rule_result_type TEXT,        -- ルール適用結果の型
    
    -- 個別マッピング情報
    manual_override TEXT,         -- 手動上書き型 (NULL=自動)
    override_reason TEXT,         -- 上書き理由
    override_date DATETIME,       -- 上書き日時
    
    -- 最終決定型
    final_type TEXT,              -- 最終的に使用する型
    type_source TEXT,             -- 型の決定ソース ('inferred', 'rule', 'manual')
    
    -- メタ情報
    encoding TEXT,
    delimiter TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (file_name, column_name)
);

-- 型決定の優先順位を明確化
-- 1. manual_override (最優先)
-- 2. rule_result_type (ルール適用)
-- 3. inferred_type (推論値)

-- 使用例クエリ
-- 最終型を取得
SELECT 
    file_name,
    column_name,
    COALESCE(manual_override, rule_result_type, inferred_type) as final_type,
    CASE 
        WHEN manual_override IS NOT NULL THEN 'manual'
        WHEN rule_result_type IS NOT NULL THEN 'rule'
        ELSE 'inferred'
    END as type_source
FROM column_master;

-- 推論のみのフィールド
SELECT * FROM column_master 
WHERE rule_applied IS NULL AND manual_override IS NULL;

-- ルール適用フィールド
SELECT * FROM column_master 
WHERE rule_applied IS NOT NULL AND manual_override IS NULL;

-- 個別マッピングフィールド
SELECT * FROM column_master 
WHERE manual_override IS NOT NULL;