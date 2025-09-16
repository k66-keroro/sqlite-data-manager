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
from t002_pattern_fixer import T002PatternFixer # 追加
from t002_rule_applier import T002RuleApplier # 追加
import master_manager # 追加
import mapper # 追加
from t003_rule_integration import RuleIntegrationManager # T003統合機能

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
    # メッセージ表示用のプレースホルダーを作成
    status_message = st.sidebar.empty()
    status_message.info("開発用データベースを初期化中...")
    
    if init_db_dev():
        status_message.success("開発用データベースの初期化が完了しました。")
    else:
        status_message.error("開発用DB初期化中にエラーが発生しました。ログを確認してください。")

if st.sidebar.button("本番用DB初期化"):
    # メッセージ表示用のプレースホルダーを作成
    status_message = st.sidebar.empty()
    status_message.info("本番用データベースを初期化中...")
    
    if init_db_prod():
        status_message.success("本番用データベースの初期化が完了しました。")
    else:
        status_message.error("本番用DB初期化中にエラーが発生しました。ログを確認してください。")

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
        with st.form(key=f"add_keyword_form_{category}"):
            new_keyword = st.text_input(f"新しいキーワードを追加 ({category})", key=f"new_keyword_input_{category}")
            add_button = st.form_submit_button(f"キーワード追加 ({category})")

            if add_button:
                if new_keyword and new_keyword not in st.session_state.corrector._rules_data['business_logic_rules'][category]:
                    st.session_state.corrector._rules_data['business_logic_rules'][category].append(new_keyword)
                    st.session_state.corrector._save_rules_data()
                    st.success(f"キーワード '{new_keyword}' を {category} に追加しました。")
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

# マスタデータ管理セクション
st.sidebar.subheader("マスタデータ管理")
if st.sidebar.button("マスタDB初期化"):
    status_message = st.sidebar.empty()
    status_message.info("マスタDBを初期化中...")
    try:
        master_manager.init_master()
        status_message.success("マスタDBの初期化が完了しました。")
    except Exception as e:
        status_message.error(f"マスタDB初期化中にエラーが発生しました: {e}")

if st.sidebar.button("マスタデータ表示"):
    try:
        master_df = master_manager.load_master()
        st.sidebar.write("### 現在のマスタデータ")
        st.sidebar.dataframe(master_df)
    except Exception as e:
        st.sidebar.error(f"マスタデータの読み込み中にエラーが発生しました: {e}")

# ルール変更を保存するボタン
if st.sidebar.button("ルール変更を保存"):
    try:
        st.session_state.corrector._save_rules_data()
        st.sidebar.success("ルールが正常に保存されました。")
    except Exception as e:
        st.sidebar.error(f"ルールの保存中にエラーが発生しました: {e}")

# --- メインコンテンツ ---
st.header("データ処理")

# パターン修正ルールの生成と適用セクション
st.subheader("パターン修正ルールの生成と適用")
st.write("データ型修正のためのパターンルールを生成し、適用します。")

col_fixer, col_applier = st.columns(2)

with col_fixer:
    if st.button("パターン修正ルールを生成"):
        status_message = st.empty()
        status_message.info("パターン修正ルールを生成中... (compare_report.csvが必要です)")
        try:
            fixer = T002PatternFixer()
            fixer.run_full_analysis()
            status_message.success("パターン修正ルールの生成が完了しました。 (pattern_rules.json)")
        except Exception as e:
            status_message.error(f"パターン修正ルールの生成中にエラーが発生しました: {e}")

with col_applier:
    if st.button("生成されたルールを適用"):
        status_message = st.empty()
        status_message.info("生成されたルールを適用中... (t002_loader_updates.jsonを生成)")
        try:
            applier = T002RuleApplier()
            applier.run_full_application()
            status_message.success("ルールの適用が完了しました。 (t002_loader_updates.json)")
        except Exception as e:
            status_message.error(f"ルールの適用中にエラーが発生しました: {e}")

st.markdown("---")

# ファイル分析セクション

st.subheader("ファイル分析")
st.write(f"分析対象データディレクトリ: `{DATA_DIR}`")
if st.button("ファイル分析実行"):
    status_message = st.empty()
    status_message.info("ファイル分析を実行中...")
    try:
        # analyze_files関数は結果を返すので、それを表示
        analysis_df = analyze_files(DATA_DIR, CANDIDATE_CSV, DB_FILE)
        status_message.success("ファイル分析が完了しました。")
        st.write("### 分析レポート概要")
        st.dataframe(analysis_df) # DataFrameとして表示
        st.session_state.analysis_df = analysis_df # セッションステートに保存
    except Exception as e:
        status_message.error(f"ファイル分析中にエラーが発生しました: {e}")

# データロードと比較セクション
st.subheader("データロードと比較")
if st.button("データロードと比較実行"):
    status_message = st.empty()
    status_message.info("データロードと比較を実行中...")
    try:
        load_and_compare()
        status_message.success("データロードと比較が完了しました。")
    except Exception as e:
        status_message.error(f"データロードと比較中にエラーが発生しました: {e}")

st.markdown("---")

# データマッピングと型比較セクション
st.header("データマッピングと型比較")

if st.button("マスタと比較して差分を検出"):
    status_message = st.empty()
    if 'analysis_df' in st.session_state and not st.session_state.analysis_df.empty:
        status_message.info("マスタデータとの比較を実行中...")
        try:
            new_cols, type_mismatch = mapper.compare_with_master(st.session_state.analysis_df)
            status_message.success("マスタデータとの比較が完了しました。")
            
            st.write("### マスタ未登録の新しい列")
            if not new_cols.empty:
                st.dataframe(new_cols)
                if st.button("未登録列をマスタに追加"):
                    try:
                        master_manager.update_master(new_cols)
                        st.success("未登録列をマスタに追加しました。")
                    except Exception as e:
                        st.error(f"マスタへの追加中にエラーが発生しました: {e}")
            else:
                st.info("マスタ未登録の新しい列はありませんでした。")
            
            st.write("### データ型不一致の列")
            if not type_mismatch.empty:
                st.dataframe(type_mismatch)
                st.warning("データ型不一致の列があります。必要に応じてマスタを更新してください。")
            else:
                st.info("データ型不一致の列はありませんでした。")

        except Exception as e:
            status_message.error(f"マスタデータとの比較中にエラーが発生しました: {e}")
    else:
        status_message.warning("先にファイル分析を実行してください。")
        st.warning("先にファイル分析を実行してください。")

st.markdown("---")
st.write("アプリケーションの状態やログはここに表示されます。")
