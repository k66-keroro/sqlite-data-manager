# GitHub Issues 作成手順書

## 🎯 Phase 1のIssues作成ガイド

### Step 1: Milestonesの作成
GitHubリポジトリ → Issues → Milestones → New milestone

**Milestone 1**:
- Title: `Phase 1 - Data Type Integration`
- Due date: `2025年9月25日`
- Description: `2,400フィールドの型統合完了（完了率95%以上、手動修正工数1週間以内）`

### Step 2: Labelsの作成  
GitHubリポジトリ → Issues → Labels → New label

以下のラベルを作成：

#### Priority Labels
- `high-priority` #d73a4a (赤)
- `medium-priority` #ff9500 (オレンジ)  
- `low-priority` #fbca04 (黄)

#### Type Labels
- `epic` #7057ff (紫)
- `enhancement` #0075ca (青)
- `bug` #d73a4a (赤)
- `documentation` #0e8a16 (緑)

#### Phase Labels
- `phase-1` #54aeff (水色)
- `phase-2` #7ddf64 (薄緑)
- `phase-3` #fff2cc (薄黄)

#### Sprint Labels
- `sprint-1` #ff69b4 (ピンク)
- `sprint-2` #f08080 (薄い赤)
- `sprint-3` #d3d3d3 (薄灰)

#### Component Labels
- `data-analysis` #00ffff (シアン)
- `core-engine` #00008b (濃青)
- `sap-specific` #ffd700 (金)
- `batch-processing` #006400 (濃緑)
- `reporting` #9370db (中紫)

### Step 3: Project Boardの作成
GitHubリポジトリ → Projects → New project → Board

**Board Name**: `SQLite Data Manager - Development`

**Columns**:
1. 📋 Backlog
2. 🚀 Sprint Planning  
3. 👨‍💻 In Progress
4. 👀 Review
5. ✅ Done

### Step 4: Issues作成の順番

**優先順位順に作成：**

1. **[T001] データ型比較結果の詳細分析と可視化**
   - Labels: `enhancement`, `phase-1`, `sprint-1`, `data-analysis`, `high-priority`
   - Milestone: Phase 1 - Data Type Integration
   - 内容: github_issues_template.md の Issue #1 をコピー

2. **[T002] 一括データ型修正支援ツールの基盤開発**
   - Labels: `enhancement`, `phase-1`, `sprint-1`, `architecture`, `high-priority`
   - Milestone: Phase 1 - Data Type Integration
   - 内容: github_issues_template.md の Issue #2 をコピー

3. **[T003] データ型統合レポート機能の実装**
   - Labels: `enhancement`, `phase-1`, `sprint-1`, `reporting`, `medium-priority`
   - Milestone: Phase 1 - Data Type Integration
   - 内容: github_issues_template.md の Issue #3 をコピー

*以下、同様にT004-T006も作成*

### Step 5: Project BoardにIssuesを追加
作成したIssuesを「📋 Backlog」列に追加し、Sprint計画に応じて移動

## 🚀 今すぐ実行するアクション

### まず最初にやること（5分）
1. **T001のIssue作成** - 最優先タスク
   - Title: `[T001] compare_report.csvの詳細分析と可視化`
   - 本日から着手予定

2. **Milestone作成** - 進捗管理用
   - Phase 1の完了目標を明確化

3. **基本Label作成** - 最低限必要なもの
   - `high-priority`, `enhancement`, `phase-1`, `data-analysis`

### 今週中にやること
1. Sprint 1の全Issues作成（T001-T003）
2. Project Board設定
3. 週次レビューの設定

## 💡 活用のコツ

### Issues活用法
- **1つのタスクは3日以内**で完了する粒度にする
- **Definition of Done**を必ず記載
- **進捗コメント**で状況を随時更新

### Project Board活用法
- **毎朝**Board確認で今日のタスク確認
- **毎夕**進捗更新でカード移動
- **毎週金曜**スプリントレビュー

### Milestone活用法
- **週次**でMilestone進捗レビュー
- **月次**でPhase全体見直し
- **完了時**次Phaseの準備開始

---

## 次の行動：まずT001から始めましょう！

GitHub Web UIで以下を実行：
1. https://github.com/k66-keroro/sqlite-data-manager にアクセス
2. Issues タブをクリック
3. New issue ボタンをクリック
4. T001の内容をコピー&ペースト
5. 適切なLabels, Milestoneを設定
6. Create issue