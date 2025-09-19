import streamlit as st
import sys
import os
import sqlite3

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DATA_DIR, CANDIDATE_CSV, DB_FILE
from init_dev import init_db_dev
from init_prod import init_db_prod
from analyzer import analyze_files
from loader import load_data
import pattern_rules # パターンルール管理のためにインポート
import master_manager # 追加
import mapper # 追加
from t003_rule_integration import RuleIntegrationManager # T003統合機能
from t004_modification_engine import ModificationEngine # T004修正エンジン
from t005_sap_special_rules import SAPSpecialRulesEngine # T005 SAP特殊ルール
from t006_batch_modification import BatchModificationManager # T006バッチ修正
from t007_verification_system import VerificationSystem # T007検証システム

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

with st.sidebar.expander("日付フォーマット管理"):
    st.write("### 日付フォーマット管理")
    st.info("日付として妥当か検証するためのフォーマット文字列（例: `%Y-%m-%d`）を管理します。")

    # 新しいフォーマットを追加
    new_datetime_format = st.text_input("新しい日付フォーマットを追加", key="new_datetime_format_input")
    if st.button("フォーマット追加", key="add_datetime_format_button"):
        if new_datetime_format and new_datetime_format not in st.session_state.corrector._rules_data.get('datetime_formats', []):
            if 'datetime_formats' not in st.session_state.corrector._rules_data:
                st.session_state.corrector._rules_data['datetime_formats'] = []
            st.session_state.corrector._rules_data['datetime_formats'].append(new_datetime_format)
            st.session_state.corrector._save_rules_data()
            st.success(f"フォーマット '{new_datetime_format}' を追加しました。")
            st.rerun()
        elif new_datetime_format in st.session_state.corrector._rules_data.get('datetime_formats', []):
            st.warning(f"フォーマット '{new_datetime_format}' は既に存在します。")
        else:
            st.warning("追加するフォーマットを入力してください。")

    st.write("---")
    st.write("### 既存の日付フォーマット")

    # 既存のフォーマットを表示・削除
    if st.session_state.corrector._rules_data.get('datetime_formats'):
        for i, fmt in enumerate(st.session_state.corrector._rules_data['datetime_formats']):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{i+1}.** `{fmt}`")
            with col2:
                if st.button("削除", key=f"delete_datetime_format_{i}"):
                    st.session_state.corrector._rules_data['datetime_formats'].pop(i)
                    st.session_state.corrector._save_rules_data()
                    st.success(f"フォーマット '{fmt}' を削除しました。")
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


# ステップ1: スキーマ分析とマスタ更新
st.subheader("ステップ1: スキーマ分析とマスタ更新")
st.write(
    "サイドバーで編集した最新のパターンルールをすべてのファイルに適用し、データベースの型定義マスタ（`column_master`）を更新します。"
    "この操作は、データをロードする前に必ず実行してください。"
)
st.write(f"分析対象データディレクトリ: `{DATA_DIR}`")
if st.button("最新ルールを適用してマスタを更新"):
    status_message = st.empty()
    status_message.info("ルールを適用し、マスタを更新中...")
    try:
        # analyze_filesはルールを適用し、マスタDBを更新し、結果を返す
        analysis_df = analyze_files(DATA_DIR, CANDIDATE_CSV, DB_FILE)
        status_message.success("型マスタの更新が完了しました。")
        st.write("### 分析・更新結果レポート")
        st.dataframe(analysis_df) # DataFrameとして表示
        st.session_state.analysis_df = analysis_df # セッションステートに保存
    except Exception as e:
        status_message.error(f"マスタの更新中にエラーが発生しました: {e}")

# ステップ2: データをテーブルにロード
st.subheader("ステップ2: データをテーブルにロード")
st.write("分析・定義されたスキーマ（`column_master`）に基づき、ファイルを読み込んでデータベースにテーブルを作成します。")
if st.button("データをテーブルにロード"):
    status_message = st.empty()
    status_message.info("データロードを実行中...")
    try:
        load_data()
        status_message.success("データロードが完了しました。")
    except Exception as e:
        status_message.error(f"データロード中にエラーが発生しました: {e}")

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

# === T003-T007 統合機能 ===
st.header("🚀 高度なデータ処理機能")

# T003: 型統合レポート機能
st.subheader("📊 T003: 型統合レポート機能")
col1, col2 = st.columns(2)

with col1:
    if st.button("型統合レポート生成"):
        status_message = st.empty()
        status_message.info("型統合レポートを生成中...")
        try:
            from t003_integration_report import IntegrationReportGenerator
            report_generator = IntegrationReportGenerator(DB_FILE)
            
            if report_generator.connect():
                # 型統合レポート生成
                master_summary = report_generator.get_column_master_summary()
                actual_summary = report_generator.get_actual_table_schema_summary()
                
                report = {
                    "column_master_summary": master_summary.to_dict('records'),
                    "actual_table_summary": actual_summary,
                    "total_fields": len(master_summary),
                    "total_tables": len(actual_summary)
                }
                
                report_generator.close()
                status_message.success("型統合レポート生成完了！")
                
                st.write("### 型統合レポート")
                st.write("#### Column Master サマリー")
                st.dataframe(master_summary)
                
                st.write("#### 実テーブル型分布")
                st.json(actual_summary)
            else:
                status_message.error("データベース接続に失敗しました。")
            
            # レポートをセッションに保存
            st.session_state.integration_report = report
            
        except Exception as e:
            status_message.error(f"型統合レポート生成エラー: {e}")

with col2:
    if st.button("修正候補の自動提案"):
        status_message = st.empty()
        status_message.info("修正候補を生成中...")
        try:
            # 簡易的な修正候補生成
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # 型不一致の候補を検出
            cursor.execute("""
                SELECT file_name, column_name, data_type, initial_inferred_type
                FROM column_master 
                WHERE data_type != initial_inferred_type
                LIMIT 10
            """)
            
            suggestions = []
            for row in cursor.fetchall():
                suggestions.append({
                    'file_name': row[0],
                    'column_name': row[1], 
                    'current_type': row[2],
                    'suggested_type': row[3],
                    'reason': '初期推定型との不一致',
                    'confidence': 'MEDIUM'
                })
            
            conn.close()
            status_message.success("修正候補生成完了！")
            
            st.write("### 修正候補")
            if suggestions:
                for suggestion in suggestions:
                    st.write(f"- **{suggestion['file_name']}.{suggestion['column_name']}**: {suggestion['current_type']} → {suggestion['suggested_type']}")
                    st.write(f"  理由: {suggestion['reason']}")
                    st.write(f"  信頼度: {suggestion['confidence']}")
            else:
                st.info("修正候補はありません。")
                
        except Exception as e:
            status_message.error(f"修正候補生成エラー: {e}")

st.markdown("---")

# T004: 型修正エンジン
st.subheader("🔧 T004: 型修正エンジン")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("修正エンジン実行"):
        status_message = st.empty()
        status_message.info("型修正エンジンを実行中...")
        try:
            engine = ModificationEngine(DB_FILE)
            
            # 簡易的な修正候補を生成して実行
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # 推論値と異なる全フィールドを修正対象として取得
            cursor.execute("""
                SELECT file_name, column_name, data_type, initial_inferred_type
                FROM column_master 
                WHERE data_type != initial_inferred_type
                AND initial_inferred_type IS NOT NULL
                AND initial_inferred_type != ''
                -- コード系フィールドは除外
                AND column_name NOT LIKE '%コード%'
                AND column_name NOT LIKE '%保管場所%'
                AND column_name NOT LIKE '%プラント%'
                LIMIT 10
            """)
            
            modifications = []
            for row in cursor.fetchall():
                from t002_data_structures import FieldModification, FieldType, ModificationAction, ConfidenceLevel
                
                file_name = row[0]
                column_name = row[1]
                current_type_str = row[2]
                target_type_str = row[3]
                
                # 文字列型をFieldType enumに変換
                current_type = FieldType.TEXT if current_type_str == 'TEXT' else FieldType.INTEGER
                if target_type_str == 'INTEGER':
                    target_type = FieldType.INTEGER
                elif target_type_str == 'REAL':
                    target_type = FieldType.REAL
                elif target_type_str == 'DATETIME':
                    target_type = FieldType.DATETIME
                else:
                    target_type = FieldType.TEXT
                
                modification = FieldModification(
                    file_name=file_name,
                    column_name=column_name,
                    current_type=current_type,
                    target_type=target_type,
                    action=ModificationAction.TYPE_CHANGE,
                    confidence=ConfidenceLevel.HIGH,
                    reason=f"推論値への復元 ({current_type_str}→{target_type_str})"
                )
                modifications.append(modification)
            
            conn.close()
            
            if modifications:
                # バッチ作成と実行
                from t002_data_structures import ModificationBatch
                batch = ModificationBatch(
                    batch_id="gui_zs65_fix",
                    name="zs65数値型修正",
                    description="zs65テーブルの数値フィールド型修正",
                    modifications=modifications
                )
                
                result = engine.execute_batch(batch)
                status_message.success(f"修正完了: {result.get('success_count', 0)}件成功")
                
                st.write("### 修正結果")
                st.json(result)
            else:
                status_message.info("修正が必要な項目はありません。")
                
        except Exception as e:
            status_message.error(f"型修正エンジンエラー: {e}")

with col2:
    if st.button("バックアップ作成"):
        status_message = st.empty()
        status_message.info("バックアップを作成中...")
        try:
            from t002_backup_system import BackupManager
            backup_manager = BackupManager()
            
            # テスト用バッチ
            from t002_data_structures import ModificationBatch
            test_batch = ModificationBatch(
                batch_id="gui_backup",
                name="GUIバックアップ",
                description="GUI操作前のバックアップ"
            )
            
            backup_info = backup_manager.create_backup(DB_FILE, test_batch)
            status_message.success("バックアップ作成完了！")
            
            st.write("### バックアップ情報")
            st.write(f"- バックアップID: {backup_info.backup_id}")
            st.write(f"- 作成日時: {backup_info.created_at}")
            st.write(f"- ファイルパス: {backup_info.backup_path}")
            
        except Exception as e:
            status_message.error(f"バックアップ作成エラー: {e}")

with col3:
    if st.button("修正履歴表示"):
        try:
            engine = ModificationEngine(DB_FILE)
            history = engine.get_modification_history()
            
            st.write("### 修正履歴")
            if history:
                for record in history[-10:]:  # 最新10件
                    st.write(f"- {record['timestamp']}: {record['description']}")
            else:
                st.info("修正履歴はありません。")
                
        except Exception as e:
            st.error(f"修正履歴取得エラー: {e}")

st.markdown("---")

# T005: SAP特殊ルール
st.subheader("🏭 T005: SAP特殊ルール")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("後ろマイナス検出"):
        status_message = st.empty()
        status_message.info("後ろマイナスフィールドを検出中...")
        try:
            sap_engine = SAPSpecialRulesEngine(DB_FILE)
            trailing_minus_fields = sap_engine.detect_trailing_minus_fields()
            status_message.success(f"後ろマイナス検出完了: {len(trailing_minus_fields)}件")
            
            st.write("### 後ろマイナスフィールド")
            if trailing_minus_fields:
                for field in trailing_minus_fields:
                    st.write(f"- {field.file_name}.{field.column_name}")
            else:
                st.info("後ろマイナスフィールドは検出されませんでした。（特殊文字エラーの可能性があります）")
                
        except Exception as e:
            status_message.error(f"後ろマイナス検出エラー: {e}")

with col2:
    if st.button("コード系フィールド識別"):
        status_message = st.empty()
        status_message.info("コード系フィールドを識別中...")
        try:
            sap_engine = SAPSpecialRulesEngine(DB_FILE)
            code_fields = sap_engine.detect_code_fields()
            status_message.success(f"コード系フィールド識別完了: {len(code_fields)}件")
            
            st.write("### コード系フィールド")
            for field in code_fields:
                st.write(f"- {field.file_name}.{field.column_name}")
                
        except Exception as e:
            status_message.error(f"コード系フィールド識別エラー: {e}")

with col3:
    if st.button("小数点カンマ検出"):
        status_message = st.empty()
        status_message.info("小数点カンマフィールドを検出中...")
        try:
            sap_engine = SAPSpecialRulesEngine(DB_FILE)
            decimal_comma_fields = sap_engine.detect_decimal_comma_fields()
            status_message.success(f"小数点カンマ検出完了: {len(decimal_comma_fields)}件")
            
            st.write("### 小数点カンマフィールド")
            for field in decimal_comma_fields:
                st.write(f"- {field.file_name}.{field.column_name}")
                
        except Exception as e:
            status_message.error(f"小数点カンマ検出エラー: {e}")

st.markdown("---")

# T006: バッチ修正機能
st.subheader("📦 T006: バッチ修正機能")
col1, col2 = st.columns(2)

with col1:
    st.write("### CSV修正指示")
    st.write("**使い方**: 上記で生成したCSVをダウンロードし、必要に応じて編集してからアップロードしてください。")
    st.write("**注意**: 保管場所やコード系フィールドはTEXT型のままにしてください。")
    
    uploaded_file = st.file_uploader("修正指示CSVファイル", type=['csv'])
    
    if uploaded_file is not None and st.button("CSVから修正実行"):
        status_message = st.empty()
        status_message.info("CSV修正指示を実行中...")
        try:
            batch_manager = BatchModificationManager(DB_FILE)
            
            # アップロードされたファイルを一時保存
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_path = tmp_file.name
            
            # CSVから修正指示を読み込み
            modifications = batch_manager.load_modifications_from_csv(tmp_path)
            
            # バッチ実行
            result = batch_manager.execute_batch_with_progress(modifications)
            status_message.success(f"CSV修正完了: {result.get('success_count', 0)}件成功")
            
            st.write("### 修正結果")
            st.json(result)
            
            # 一時ファイル削除
            os.unlink(tmp_path)
            
        except Exception as e:
            status_message.error(f"CSV修正エラー: {e}")

with col2:
    if st.button("修正指示CSVエクスポート"):
        status_message = st.empty()
        status_message.info("修正指示CSVを生成中...")
        try:
            batch_manager = BatchModificationManager(DB_FILE)
            
            # 修正候補を生成
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # 推論値ベースの修正候補を取得（個別マッピング不要）
            cursor.execute("""
                SELECT file_name, column_name, data_type, initial_inferred_type
                FROM column_master 
                WHERE data_type != initial_inferred_type
                AND initial_inferred_type IS NOT NULL
                AND initial_inferred_type != ''
                -- コード系フィールドは除外（TEXTが正しい）
                AND column_name NOT LIKE '%コード%'
                AND column_name NOT LIKE '%保管場所%'
                AND column_name NOT LIKE '%プラント%'
                ORDER BY file_name, column_name
                LIMIT 50
            """)
            
            suggestions = []
            for row in cursor.fetchall():
                file_name = row[0]
                column_name = row[1]
                current_type = row[2]
                initial_type = row[3]
                
                # 推論値をそのまま使用（個別マッピング不要）
                suggestions.append({
                    'file_name': file_name,
                    'column_name': column_name,
                    'current_type': current_type,
                    'suggested_type': initial_type,  # 推論値を信頼
                    'reason': f'推論値への復元 (TEXT→{initial_type})',
                    'confidence': 'HIGH'
                })
            
            conn.close()
            
            if suggestions:
                # CSVエクスポート
                import pandas as pd
                df = pd.DataFrame(suggestions)
                csv_path = "modification_instructions.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                
                status_message.success("修正指示CSV生成完了！")
                
                # ダウンロードリンク提供
                with open(csv_path, 'rb') as f:
                    st.download_button(
                        label="修正指示CSVダウンロード",
                        data=f.read(),
                        file_name="modification_instructions.csv",
                        mime="text/csv"
                    )
            else:
                status_message.info("修正候補がありません。")
                
        except Exception as e:
            status_message.error(f"CSV生成エラー: {e}")

st.markdown("---")

# T007: 検証システム
st.subheader("✅ T007: 検証システム")
col1, col2 = st.columns(2)

with col1:
    if st.button("データ整合性検証"):
        status_message = st.empty()
        status_message.info("データ整合性を検証中...")
        try:
            verification_system = VerificationSystem(DB_FILE)
            
            # テスト用バッチ
            from t002_data_structures import ModificationBatch
            test_batch = ModificationBatch(
                batch_id="gui_verification",
                name="GUI検証",
                description="GUI操作の検証"
            )
            
            report = verification_system.verify_modification_batch(test_batch)
            status_message.success("データ整合性検証完了！")
            
            st.write("### 検証結果")
            st.write(f"- 全体ステータス: {report.overall_status}")
            st.write(f"- 検証項目数: {len(report.integrity_checks)}")
            
            for check in report.integrity_checks:
                status_icon = "✅" if check.passed else "❌"
                st.write(f"{status_icon} {check.check_name}: {check.message}")
                
        except Exception as e:
            status_message.error(f"検証エラー: {e}")

with col2:
    if st.button("実テーブル型比較"):
        status_message = st.empty()
        status_message.info("実テーブルとcolumn_masterを比較中...")
        try:
            # データ型比較ツールを実行
            import subprocess
            result = subprocess.run(['python', 'data_type_comparison_tool.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                status_message.success("実テーブル型比較完了！")
                st.write("### 比較結果")
                st.text(result.stdout)
            else:
                status_message.error("比較処理でエラーが発生しました。")
                st.text(result.stderr)
                
        except Exception as e:
            status_message.error(f"型比較エラー: {e}")

st.markdown("---")

# 重たい処理専用セクション
st.header("⚡ 重たい処理・業務処理")
st.subheader("🏭 ZP138引当・過不足算出")
st.write("90,000データの引当と過不足を算出する重たい処理です。")

col1, col2 = st.columns(2)

with col1:
    if st.button("ZP138処理実行", type="primary"):
        status_message = st.empty()
        status_message.info("ZP138引当・過不足算出を実行中... (数分かかる場合があります)")
        
        try:
            # zp138_test.pyの処理を実行
            import subprocess
            result = subprocess.run(['python', 'test/.obsidian/zp138_test.py'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                status_message.success("ZP138処理完了！")
                st.write("### 処理結果")
                st.text(result.stdout)
            else:
                status_message.error("ZP138処理でエラーが発生しました。")
                st.text(result.stderr)
                
        except Exception as e:
            status_message.error(f"ZP138処理エラー: {e}")

with col2:
    st.write("### 処理内容")
    st.write("- データ読み込み・加工")
    st.write("- 引当・過不足計算")
    st.write("- SQLite → Access エクスポート")
    st.write("- Excel資料生成")

st.markdown("---")
st.write("🎯 **Phase 1完了**: 全機能がGUIに統合されました！")
