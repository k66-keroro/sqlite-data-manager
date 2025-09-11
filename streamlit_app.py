import streamlit as st
import sys
import os

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, CANDIDATE_CSV, DB_FILE
from init_dev import init_db_dev
from init_prod import init_db_prod
from analyzer import analyze_files
from loader import load_and_compare
import pattern_rules # パターンルール管理のためにインポート

st.set_page_config(layout="wide", page_title="SQLite Data Manager GUI")

st.title("SQLite Data Manager GUI")

# TypeCorrectionRulesのインスタンスを作成
# Streamlitのセッションステートに保存して、再実行時に再初期化されないようにする
if 'corrector' not in st.session_state:
    st.session_state.corrector = pattern_rules.TypeCorrectionRules()

# --- サイドバー ---
st.sidebar.header("操作メニュー")

# DB初期化セクション
st.sidebar.subheader("データベース初期化")
if st.sidebar.button("開発用DB初期化"):
    st.sidebar.info("開発用データベースを初期化中...")
    try:
        init_db_dev()
        st.sidebar.success("開発用データベースの初期化が完了しました。")
    except Exception as e:
        st.sidebar.error(f"開発用DB初期化中にエラーが発生しました: {e}")

if st.sidebar.button("本番用DB初期化"):
    st.sidebar.info("本番用データベースを初期化中...")
    try:
        init_db_prod()
        st.sidebar.success("本番用データベースの初期化が完了しました。")
    except Exception as e:
        st.sidebar.error(f"本番用DB初期化中にエラーが発生しました: {e}")

# パターンルール管理セクション
st.sidebar.subheader("パターンルール管理")

# ルールデータを表示
with st.sidebar.expander("未登録ファイルルール"):
    st.json(st.session_state.corrector._rules_data['unregistered_files'])

with st.sidebar.expander("日付パターンルール"):
    st.json(st.session_state.corrector._rules_data['datetime_patterns'])

with st.sidebar.expander("ビジネスロジックルール"):
    st.json(st.session_state.corrector._rules_data['business_logic_rules'])

with st.sidebar.expander("SAP特殊パターンルール"):
    st.json(st.session_state.corrector._rules_data['sap_patterns'])

# ルール変更を保存するボタン
if st.sidebar.button("ルール変更を保存"):
    try:
        st.session_state.corrector._save_rules_data()
        st.sidebar.success("ルールが正常に保存されました。")
    except Exception as e:
        st.sidebar.error(f"ルールの保存中にエラーが発生しました: {e}")

# --- メインコンテンツ ---
st.header("データ処理")

# ファイル分析セクション
st.subheader("ファイル分析")
st.write(f"分析対象データディレクトリ: `{DATA_DIR}`")
if st.button("ファイル分析実行"):
    st.info("ファイル分析を実行中...")
    try:
        # analyze_files関数は結果を返すので、それを表示
        report = analyze_files(DATA_DIR, CANDIDATE_CSV, DB_FILE)
        st.success("ファイル分析が完了しました。")
        st.write("### 分析レポート概要")
        st.json(report) # 仮にJSON形式で表示
    except Exception as e:
        st.error(f"ファイル分析中にエラーが発生しました: {e}")

# データロードと比較セクション
st.subheader("データロードと比較")
if st.button("データロードと比較実行"):
    st.info("データロードと比較を実行中...")
    try:
        load_and_compare()
        st.success("データロードと比較が完了しました。")
    except Exception as e:
        st.error(f"データロードと比較中にエラーが発生しました: {e}")

st.markdown("---")
st.write("アプリケーションの状態やログはここに表示されます。")
