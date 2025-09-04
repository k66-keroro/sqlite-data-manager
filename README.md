# SQLite Data Manager

**SAPデータ自動取り込み・型推定・正規化システム**

SQLiteベースのデータ管理システムで、SAPから出力される多様な形式のデータファイルを自動処理し、統一されたデータベースを構築します。

## 🎯 プロジェクト概要

- **目的**: 2,400+フィールドのSAPデータを自動処理・統合
- **課題解決**: エンコーディング、区切り文字、拡張子、フィールド名の統一性なしデータの処理
- **現状**: 39/40ファイル処理成功、Phase 1（データ型統合）進行中

## ✨ 主な機能

### 🔄 データ処理
- **多様なファイル形式対応** (CSV, TXT, XLS, XLSX)
- **自動エンコーディング検出** (UTF-8, CP932, Shift_JIS, UTF-16)
- **自動区切り文字検出** (カンマ, タブ, パイプ, セミコロン)
- **SAPデータ特殊ルール対応** (0パディング, 後ろマイナス処理)

### 🧠 データ型推定・統合
- **自動データ型推定** (INTEGER, REAL, TEXT, DATETIME)
- **同一データ重複検出・統合**
- **型統合結果の永続化**
- **手動修正サポート**

### 📊 監視・分析
- **ファイル処理状況記録**
- **データ品質チェック**
- **処理統計表示**
- **異常検出アラート**

## 🚀 クイックスタート

### 前提条件
- Python 3.8以上
- Windows 10/11
- メモリ8GB以上推奨

### インストール

```bash
git clone https://github.com/k66-keroro/sqlite-data-manager.git
cd sqlite-data-manager
pip install -r requirements.txt
```

### 基本的な使い方

```bash
# 開発環境初期化
python main.py init_dev

# ファイル分析実行
python main.py analyze

# データ読み込み・比較
python main.py load

# 本番環境初期化
python main.py init_prod
```

## 📁 プロジェクト構成

```
sqlite-data-manager/
├── main.py              # エントリポイント
├── config.py           # 設定管理
├── analyzer.py         # データ分析・型推定
├── loader.py           # ファイル読み込み
├── init_dev.py         # 開発環境初期化
├── init_prod.py        # 本番環境初期化
├── mapper.py           # データマッピング
├── db.py              # SQLite操作
├── master_manager.py   # マスタ管理
├── file_analyzer.py    # ファイル解析
├── output/            # 出力ディレクトリ
│   ├── master.db     # SQLiteデータベース
│   └── compare_report.csv # 型比較結果
├── テキスト/          # 入力データ（40ファイル）
└── docs/             # ドキュメント
    ├── design.md     # 設計書
    ├── tasks.md      # タスク管理
    └── requirements.md # 要件定義
```

## 🎯 開発ロードマップ

### Phase 1: データ型統合・修正ツール開発 (Week 1-3)
- [x] 基本ファイル読み込み機能 (39/40成功)
- [ ] データ型比較・分析ツール
- [ ] 一括型修正機能
- [ ] 修正結果検証機能

### Phase 2: 日次バッチ処理の自動化 (Week 4-5)
- [ ] スケジューラー実装
- [ ] 増分更新機能
- [ ] 監視・ログ強化
- [ ] 自動回復機能

### Phase 3: Streamlitダッシュボード (Week 6-7)
- [ ] データ概要画面
- [ ] 型統合状況の可視化
- [ ] 手動修正インターface
- [ ] エクスポート機能

## 🔧 技術スタック

- **Backend**: Python + SQLite
- **Data Processing**: pandas, numpy
- **Frontend (予定)**: Streamlit
- **Version Control**: GitHub
- **Database**: SQLite 3.x

## 📈 現在の進捗

- ✅ **ファイル読み込み**: 39/40ファイル成功（97.5%）
- 🔄 **データ型統合**: Phase 1進行中
- ⏳ **自動化**: Phase 2準備中
- ⏳ **ダッシュボード**: Phase 3準備中

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

### 開発の流れ
1. このリポジトリをフォーク
2. feature ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチをプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

## 📝 ライセンス

MIT License

## 📞 サポート・連絡先

- **Issues**: GitHub Issues でバグ報告・機能要望
- **Documentation**: `/docs` ディレクトリ参照
- **Project Status**: tasks.md で進捗確認

## ⚠️ 注意事項

- SAPデータには機密情報が含まれる可能性があります
- 大容量ファイル（251MB）処理時はメモリ使用量に注意
- 日次バッチ処理は業務時間外での実行を推奨

---

**Status**: 🚧 開発中 (Phase 1: データ型統合・修正ツール開発)  
**Last Updated**: 2025年9月4日