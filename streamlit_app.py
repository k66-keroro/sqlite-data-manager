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

# 未登録ファイルルール
with st.sidebar.expander("未登録ファイルルール"):
    st.write("### 未登録ファイルルール管理")
    
    # 新しいルールを追加
    st.subheader("新しいルールを追加")
    new_file_name = st.text_input("ファイル名", key="new_unregistered_file_name")
    new_encoding = st.selectbox("エンコーディング", options=["cp932", "utf-8", "utf-16", "shift_jis"], index=0, key="new_unregistered_encoding")
    new_separator = st.selectbox("セパレータ", options=["\t", ",", ";", " "], index=0, key="new_unregistered_separator")
    
    if st.button("ルール追加", key="add_unregistered_rule_button"):
        if new_file_name and new_encoding and new_separator:
            if new_file_name not in st.session_state.corrector._rules_data['unregistered_files']:
                st.session_state.corrector._rules_data['unregistered_files'][new_file_name] = {
                    "encoding": new_encoding,
                    "separator": new_separator
                }
                st.session_state.corrector._save_rules_data()
                st.success(f"ファイル '{new_file_name}' のルールを追加しました。")
                st.rerun()
            else:
                st.warning(f"ファイル '{new_file_name}' のルールは既に存在します。")
        else:
            st.warning("すべてのフィールドを入力してください。")

    st.write("---")
    st.write("### 既存の未登録ファイルルール")
    
    # 既存のルールを表示・編集・削除
    if st.session_state.corrector._rules_data['unregistered_files']:
        for file_name, rules in st.session_state.corrector._rules_data['unregistered_files'].items():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.write(f"**ファイル名:** `{file_name}`")
                st.write(f"**エンコーディング:** `{rules['encoding']}`")
                st.write(f"**セパレータ:** `{rules['separator']}`")
            with col3:
                if st.button("編集", key=f"edit_unregistered_rule_{file_name}"):
                    st.session_state.editing_unregistered_file_name = file_name
                    st.session_state.editing_unregistered_encoding = rules['encoding']
                    st.session_state.editing_unregistered_separator = rules['separator']
                    st.rerun()
            with col4:
                if st.button("削除", key=f"delete_unregistered_rule_{file_name}"):
                    del st.session_state.corrector._rules_data['unregistered_files'][file_name]
                    st.session_state.corrector._save_rules_data()
                    st.success(f"ファイル '{file_name}' のルールを削除しました。")
                    st.rerun()
            st.markdown("---")

    # 編集モード
    if 'editing_unregistered_file_name' in st.session_state and st.session_state.editing_unregistered_file_name is not None:
        st.write("---")
        st.subheader(f"ルール編集 (ファイル名: {st.session_state.editing_unregistered_file_name})")
        
        edited_file_name = st.text_input("ファイル名 (変更不可)", value=st.session_state.editing_unregistered_file_name, disabled=True, key="edited_unregistered_file_name_display")
        encoding_options = ["cp932", "utf-8", "utf-16", "shift_jis"]
        current_encoding_index = encoding_options.index(st.session_state.editing_unregistered_encoding) if st.session_state.editing_unregistered_encoding in encoding_options else 0
        edited_encoding = st.selectbox("エンコーディング", options=encoding_options, index=current_encoding_index, key="edited_unregistered_encoding_input")
        edited_separator = st.selectbox("セパレータ", options=["\t", ",", ";", " "], index=["\t", ",", ";", " "].index(st.session_state.editing_unregistered_separator), key="edited_unregistered_separator_input")
        
        col_edit_save, col_edit_cancel = st.columns(2)
        with col_edit_save:
            if st.button("変更を保存", key="save_edited_unregistered_rule_button"):
                if edited_encoding and edited_separator:
                    st.session_state.corrector._rules_data['unregistered_files'][st.session_state.editing_unregistered_file_name] = {
                        "encoding": edited_encoding,
                        "separator": edited_separator
                    }
                    st.session_state.corrector._save_rules_data()
                    st.success(f"ファイル '{st.session_state.editing_unregistered_file_name}' のルールを更新しました。")
                    del st.session_state.editing_unregistered_file_name
                    del st.session_state.editing_unregistered_encoding
                    del st.session_state.editing_unregistered_separator
                    st.rerun()
                else:
                    st.warning("エンコーディングとセパレータを入力してください。")
        with col_edit_cancel:
            if st.button("キャンセル", key="cancel_edit_unregistered_rule_button"):
                del st.session_state.editing_unregistered_file_name
                del st.session_state.editing_unregistered_encoding
                del st.session_state.editing_unregistered_separator
                st.rerun()

with st.sidebar.expander("日付パターンルール"):
    st.write("### 日付パターン管理")
    
    # 新しいパターンを追加
    new_datetime_pattern = st.text_input("新しい日付パターンを追加", key="new_datetime_pattern_input")
    if st.button("パターン追加", key="add_datetime_pattern_button"):
        if new_datetime_pattern and new_datetime_pattern not in st.session_state.corrector._rules_data['datetime_patterns']:
            st.session_state.corrector._rules_data['datetime_patterns'].append(new_datetime_pattern)
            st.session_state.corrector._save_rules_data()
            st.success(f"パターン '{new_datetime_pattern}' を追加しました。")
            st.rerun() # 変更を反映するために再実行
        elif new_datetime_pattern in st.session_state.corrector._rules_data['datetime_patterns']:
            st.warning(f"パターン '{new_datetime_pattern}' は既に存在します。")
        else:
            st.warning("追加するパターンを入力してください。")

    st.write("---")
    st.write("### 既存の日付パターン")
    
    # 既存のパターンを表示・編集・削除
    for i, pattern in enumerate(st.session_state.corrector._rules_data['datetime_patterns']):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"**{i+1}.** `{pattern}`")
        with col2:
            if st.button("編集", key=f"edit_datetime_pattern_{i}"):
                st.session_state.editing_datetime_pattern_index = i
                st.session_state.editing_datetime_pattern_value = pattern
                st.rerun()
        with col3:
            if st.button("削除", key=f"delete_datetime_pattern_{i}"):
                st.session_state.corrector._rules_data['datetime_patterns'].pop(i)
                st.session_state.corrector._save_rules_data()
                st.success(f"パターン '{pattern}' を削除しました。")
                st.rerun() # 変更を反映するために再実行

    # 編集モード
    if 'editing_datetime_pattern_index' in st.session_state and st.session_state.editing_datetime_pattern_index is not None:
        st.write("---")
        st.subheader(f"パターン編集 (インデックス: {st.session_state.editing_datetime_pattern_index + 1})")
        edited_pattern = st.text_input("パターンを編集", value=st.session_state.editing_datetime_pattern_value, key="edited_datetime_pattern_input")
        
        col_edit_save, col_edit_cancel = st.columns(2)
        with col_edit_save:
            if st.button("変更を保存", key="save_edited_datetime_pattern_button"):
                if edited_pattern:
                    st.session_state.corrector._rules_data['datetime_patterns'][st.session_state.editing_datetime_pattern_index] = edited_pattern
                    st.session_state.corrector._save_rules_data()
                    st.success(f"パターンを '{edited_pattern}' に更新しました。")
                    del st.session_state.editing_datetime_pattern_index
                    del st.session_state.editing_datetime_pattern_value
                    st.rerun()
                else:
                    st.warning("編集するパターンを入力してください。")
        with col_edit_cancel:
            if st.button("キャンセル", key="cancel_edit_datetime_pattern_button"):
                del st.session_state.editing_datetime_pattern_index
                del st.session_state.editing_datetime_pattern_value
                st.rerun()

with st.sidebar.expander("ビジネスロジックルール"):
    st.write("### ビジネスロジックルール管理")

    rule_categories = ['code_fields', 'amount_fields', 'quantity_fields']

    for category in rule_categories:
        st.subheader(f"{category.replace('_fields', '').capitalize()} フィールド")
        
        # 新しいキーワードを追加
        new_keyword = st.text_input(f"新しいキーワードを追加 ({category})", key=f"new_keyword_input_{category}")
        if st.button(f"キーワード追加 ({category})", key=f"add_keyword_button_{category}"):
            if new_keyword and new_keyword not in st.session_state.corrector._rules_data['business_logic_rules'][category]:
                st.session_state.corrector._rules_data['business_logic_rules'][category].append(new_keyword)
                st.session_state.corrector._save_rules_data()
                st.success(f"キーワード '{new_keyword}' を {category} に追加しました。")
                st.session_state[f"new_keyword_input_{category}"] = "" # 入力フィールドをクリア
                st.rerun()
            elif new_keyword in st.session_state.corrector._rules_data['business_logic_rules'][category]:
                st.warning(f"キーワード '{new_keyword}' は既に {category} に存在します。")
            else:
                st.warning("追加するキーワードを入力してください。")

        st.write("#### 既存のキーワード")
        
        # 既存のキーワードを表示・編集・削除
        if st.session_state.corrector._rules_data['business_logic_rules'][category]:
            for i, keyword in enumerate(st.session_state.corrector._rules_data['business_logic_rules'][category]):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{i+1}.** `{keyword}`")
                with col2:
                    if st.button("編集", key=f"edit_keyword_{category}_{i}"):
                        st.session_state.editing_business_logic_category = category
                        st.session_state.editing_business_logic_index = i
                        st.session_state.editing_business_logic_value = keyword
                        st.rerun()
                with col3:
                    if st.button("削除", key=f"delete_keyword_{category}_{i}"):
                        st.session_state.corrector._rules_data['business_logic_rules'][category].pop(i)
                        st.session_state.corrector._save_rules_data()
                        st.success(f"キーワード '{keyword}' を {category} から削除しました。")
                        st.rerun()
            st.markdown("---")
        
        # 編集モード (各カテゴリのリスト表示の直後に配置)
        if 'editing_business_logic_category' in st.session_state and st.session_state.editing_business_logic_category == category and st.session_state.editing_business_logic_index is not None:
            st.write("---")
            category_to_edit = st.session_state.editing_business_logic_category
            index_to_edit = st.session_state.editing_business_logic_index
            st.subheader(f"キーワード編集 ({category_to_edit.replace('_fields', '').capitalize()} フィールド - インデックス: {index_to_edit + 1})")
            edited_keyword = st.text_input("キーワードを編集", value=st.session_state.editing_business_logic_value, key=f"edited_business_logic_keyword_input_inline_{category}") # キーをユニークにする
            
            col_edit_save, col_edit_cancel = st.columns(2)
            with col_edit_save:
                if st.button("変更を保存", key=f"save_edited_business_logic_keyword_button_inline_{category}"):
                    if edited_keyword:
                        st.session_state.corrector._rules_data['business_logic_rules'][category_to_edit][index_to_edit] = edited_keyword
                        st.session_state.corrector._save_rules_data()
                        st.success(f"キーワードを '{edited_keyword}' に更新しました。")
                        del st.session_state.editing_business_logic_category
                        del st.session_state.editing_business_logic_index
                        del st.session_state.editing_business_logic_value
                        st.rerun()
                    else:
                        st.warning("編集するキーワードを入力してください。")
            with col_edit_cancel:
                if st.button("キャンセル", key=f"cancel_edit_business_logic_keyword_button_inline_{category}"):
                    del st.session_state.editing_business_logic_category
                    del st.session_state.editing_business_logic_index
                    del st.session_state.editing_business_logic_value
                    st.rerun()
            st.markdown("---") # 編集フォームの区切り

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
