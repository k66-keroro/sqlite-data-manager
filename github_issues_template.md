# GitHub Issues Creation Template

## Phase 1: データ型統合・修正ツール開発 (Week 1-3)

### Epic: Data Type Integration & Correction Tool
**Label**: `epic`, `phase-1`, `high-priority`

---

## Issue #1: T001 - compare_report.csvの詳細分析
**Title**: [T001] データ型比較結果の詳細分析と可視化  
**Labels**: `enhancement`, `phase-1`, `sprint-1`, `data-analysis`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
compare_report.csvの分析を行い、型不一致パターンを分類・可視化する。

### Tasks
- [ ] compare_report.csvの詳細分析
- [ ] 型不一致パターンの分類
- [ ] 重複フィールドの検出ロジック実装
- [ ] SAPデータ特殊パターンの識別

### Acceptance Criteria
- [ ] 型不一致パターンが明確に分類されている
- [ ] 重複フィールドが自動検出できる
- [ ] SAPデータ特殊パターン（0パディング、後ろマイナス）が識別できる
- [ ] 分析結果がレポート形式で出力される

### Definition of Done
- [ ] コードレビュー完了
- [ ] テスト実行完了
- [ ] ドキュメント更新完了

---

## Issue #2: T002 - データ型修正支援ツール基盤
**Title**: [T002] 一括データ型修正支援ツールの基盤開発  
**Labels**: `enhancement`, `phase-1`, `sprint-1`, `architecture`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
データ型を一括修正するためのツール基盤を構築する。

### Tasks
- [ ] 一括修正用のデータ構造設計
- [ ] 修正ルールのテンプレート作成
- [ ] バックアップ機能の実装
- [ ] ロールバック機能の実装

### Acceptance Criteria
- [ ] 修正ルールがテンプレート化されている
- [ ] 修正前のデータバックアップが自動作成される
- [ ] 修正に失敗した場合のロールバック機能がある
- [ ] 修正履歴が記録される

---

## Issue #3: T003 - 型統合レポート機能
**Title**: [T003] データ型統合レポート機能の実装  
**Labels**: `enhancement`, `phase-1`, `sprint-1`, `reporting`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
型統合の前後比較と修正候補を自動提案するレポート機能を実装する。

### Tasks
- [ ] 統合前後の比較表示
- [ ] 修正候補の自動提案
- [ ] 信頼度スコアの算出
- [ ] レポートのExcel出力機能

### Acceptance Criteria
- [ ] 統合前後の差分が分かりやすく表示される
- [ ] 修正候補が信頼度とともに提案される
- [ ] レポートがExcel形式で出力できる
- [ ] レポート生成時間が10分以内

---

## Issue #4: T004 - 型修正エンジンの開発
**Title**: [T004] 安全な型修正エンジンの実装  
**Labels**: `enhancement`, `phase-1`, `sprint-2`, `core-engine`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
データ型を安全に変換する修正エンジンを開発する。

### Tasks
- [ ] 安全な型変換処理
- [ ] ロールバック機能
- [ ] 修正履歴の記録
- [ ] エラーハンドリング

### Acceptance Criteria
- [ ] データ損失なしで型変換が行われる
- [ ] 変換に失敗した場合は自動ロールバックされる
- [ ] 全ての修正履歴が追跡可能
- [ ] エラー時の詳細ログが出力される

---

## Issue #5: T005 - SAPデータ特殊ルールの実装
**Title**: [T005] SAPデータ特殊ルール（0パディング・後ろマイナス）の対応  
**Labels**: `enhancement`, `phase-1`, `sprint-2`, `sap-specific`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
SAP特有のデータ形式（0パディング、後ろマイナス）を正規化する機能を実装する。

### Tasks
- [ ] 0パディングの統一処理
- [ ] 後ろマイナスの正規化
- [ ] コード系フィールドの自動識別
- [ ] SAPルール設定の外部化

### Acceptance Criteria
- [ ] 0パディングが統一的に処理される
- [ ] 後ろマイナスが適切に数値変換される
- [ ] コード系フィールドが自動識別される
- [ ] SAPルールが設定ファイルで管理される

---

## Issue #6: T006 - バッチ修正機能
**Title**: [T006] CSV指示によるバッチ型修正機能  
**Labels**: `enhancement`, `phase-1`, `sprint-2`, `batch-processing`  
**Assignee**: k66-keroro  
**Milestone**: Phase 1 - Data Type Integration

### Description
CSV形式で修正指示を読み込み、バッチで型修正を実行する機能を実装する。

### Tasks
- [ ] CSV形式での修正指示読み込み
- [ ] プログレス表示
- [ ] エラーハンドリング
- [ ] バッチ実行ログ出力

### Acceptance Criteria
- [ ] CSV形式で修正指示が読み込める
- [ ] 処理進捗がリアルタイムで表示される
- [ ] エラー発生時も処理が継続される
- [ ] 詳細な実行ログが出力される

---

## Milestones

### Phase 1 - Data Type Integration (Week 3)
**Due Date**: 2025年9月25日
**Description**: 2,400フィールドの型統合完了

**Success Criteria**:
- [ ] 型統合完了率 95%以上
- [ ] 自動推定精度 90%以上
- [ ] 手動修正工数 1週間以内

**Issues**: #1, #2, #3, #4, #5, #6, #7, #8, #9

---

## Labels to Create

### Priority Labels
- `high-priority` (red) - 最優先タスク
- `medium-priority` (orange) - 中優先タスク  
- `low-priority` (yellow) - 低優先タスク

### Type Labels
- `epic` (purple) - エピック
- `enhancement` (blue) - 機能追加
- `bug` (red) - バグ修正
- `documentation` (green) - ドキュメント

### Phase Labels  
- `phase-1` (lightblue) - Phase 1: データ型統合
- `phase-2` (lightgreen) - Phase 2: 自動化
- `phase-3` (lightyellow) - Phase 3: ダッシュボード

### Sprint Labels
- `sprint-1` (pink) - Sprint 1
- `sprint-2` (lightcoral) - Sprint 2
- `sprint-3` (lightgray) - Sprint 3

### Component Labels
- `data-analysis` (cyan) - データ分析
- `core-engine` (darkblue) - コアエンジン
- `sap-specific` (gold) - SAP固有処理
- `batch-processing` (darkgreen) - バッチ処理
- `reporting` (mediumpurple) - レポート機能

---

## Project Board Setup

### Columns
1. **📋 Backlog** - 未着手
2. **🚀 Sprint Planning** - スプリント計画
3. **👨‍💻 In Progress** - 作業中
4. **👀 Review** - レビュー中
5. **✅ Done** - 完了

### Cards
各IssueをProject Boardのカードとして追加し、進捗を可視化する。