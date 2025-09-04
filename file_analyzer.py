import os
import csv
import chardet
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import re

def detect_encoding(file_path):
    for enc in ['cp932', 'shift_jis']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                f.read(10)
            return enc, 1.0
        except UnicodeDecodeError:
            pass
    
    with open(file_path, 'rb') as f:
        raw_data = f.read(1024 * 10)
        result = chardet.detect(raw_data)
    return result['encoding'], result['confidence']

def detect_delimiter_and_types_revised(file_path, encoding):
    delimiter = 'N/A'
    data_types = ['N/A']
    fallback_delimiters = [',', '\t', ';', '|', ' ']
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            sample = f.read(1024 * 5)
            if sample:
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    delimiter = dialect.delimiter
                except csv.Error:
                    pass
        df = None
        current_delimiter = delimiter if delimiter != 'N/A' else None
        for delim in ([current_delimiter] if current_delimiter else []) + fallback_delimiters:
            try:
                df = pd.read_csv(file_path, sep=delim, encoding=encoding, nrows=10, engine='python', on_bad_lines='skip', header=None)
                if len(df.columns) > 1:
                    delimiter = delim
                    break
                else:
                    df = None
            except Exception:
                df = None
        if df is not None:
            inferred_types = [pd.api.types.infer_dtype(df[col], skipna=True) for col in df.columns]
            data_types = inferred_types
        return delimiter, data_types
    except UnicodeDecodeError:
        return 'N/A', ['N/A']
    except Exception:
        return 'N/A', ['N/A']

def analyze_irregular_file_robust(file_path, encoding, expected_columns, file_name):
    """不規則なファイルを頑健に解析する関数"""
    try:
        print(f"\n🔍 分析開始: {file_name}")
        print("="*60)
        
        # 1. まずファイルの最初の数行を手動で読んで構造を確認
        with open(file_path, 'r', encoding=encoding) as f:
            first_line = f.readline().strip()
            second_line = f.readline().strip()
            third_line = f.readline().strip()
        
        print(f"📄 ファイル構造サンプル:")
        print(f"   ヘッダー行: {first_line[:80]}{'...' if len(first_line) > 80 else ''}")
        print(f"   データ行1: {second_line[:80]}{'...' if len(second_line) > 80 else ''}")
        print(f"   データ行2: {third_line[:80]}{'...' if len(third_line) > 80 else ''}")
        
        # 2. ヘッダー行の解析（期待列数を基準に最適な区切り文字を選択）
        print(f"\n🎯 ヘッダー解析 (期待列数: {expected_columns})")
        header_columns = None
        header_delimiter = None
        best_match_diff = float('inf')
        
        for delim in ['\t', ' ', r'\s+', ',', ';']:
            try:
                if delim == r'\s+':
                    # 正規表現の場合は手動で分割
                    parts = re.split(r'\s+', first_line)
                    parts = [p.strip() for p in parts if p.strip()]
                else:
                    parts = first_line.split(delim)
                    parts = [p.strip() for p in parts if p.strip()]
                
                column_count = len(parts)
                delim_name = {'\\t': 'タブ', ' ': 'スペース', r'\\s+': '正規表現', ',': 'カンマ', ';': 'セミコロン'}.get(delim, delim)
                
                print(f"   {delim_name:8}: {column_count:3}列", end="")
                
                # 期待列数がある場合は、それに最も近い結果を選ぶ
                if expected_columns != 'N/A':
                    diff = abs(column_count - expected_columns)
                    if diff < best_match_diff and column_count > 10:
                        best_match_diff = diff
                        header_columns = column_count
                        header_delimiter = delim
                        print(f" ← BEST MATCH (差分: {diff})")
                    else:
                        print(f" (差分: {diff})")
                else:
                    # 期待列数がない場合は従来通り
                    if column_count > 10:
                        header_columns = column_count
                        header_delimiter = delim
                        print(f" ← SELECTED")
                        break
                    else:
                        print("")
                        
            except Exception as e:
                print(f"   {delim:8}: ERROR - {e}")
                continue
        
        # 3. データ行の解析（期待列数に合わせて最適な方法を選択）
        print(f"\n📊 データ行解析")
        data_columns = None
        data_delimiter = None
        data_types = ['N/A']
        best_data_diff = float('inf')
        
        # 複数の方法でデータ行を読み込む
        methods = [
            # 方法1: pandas with quoting=csv.QUOTE_NONE (正規表現区切り)
            ('正規表現区切り', lambda: pd.read_csv(file_path, sep=r'\s+', encoding=encoding, 
                               engine='python', skiprows=1, nrows=5, header=None,
                               quoting=csv.QUOTE_NONE, on_bad_lines='skip')),
            # 方法2: pandas with tab separator
            ('タブ区切り', lambda: pd.read_csv(file_path, sep='\t', encoding=encoding, 
                               engine='python', skiprows=1, nrows=5, header=None,
                               quoting=csv.QUOTE_NONE, on_bad_lines='skip')),
            # 方法3: 手動分割
            ('手動解析', lambda: manual_parse_data_lines(file_path, encoding)),
            # 方法4: pandas with comma separator  
            ('カンマ区切り', lambda: pd.read_csv(file_path, sep=',', encoding=encoding, 
                               engine='python', skiprows=1, nrows=5, header=None,
                               quoting=csv.QUOTE_NONE, on_bad_lines='skip')),
        ]
        
        df = None
        method_used = "None"
        
        for method_name, method_func in methods:
            try:
                test_df = method_func()
                if test_df is not None and len(test_df.columns) > 5:
                    test_columns = len(test_df.columns)
                    
                    # 期待列数に最も近い結果を選ぶ
                    if expected_columns != 'N/A':
                        diff = abs(test_columns - expected_columns)
                        print(f"   {method_name:12}: {test_columns:3}列", end="")
                        if diff < best_data_diff:
                            best_data_diff = diff
                            df = test_df
                            data_columns = test_columns
                            method_used = method_name
                            print(f" ← BEST MATCH (差分: {diff})")
                        else:
                            print(f" (差分: {diff})")
                    else:
                        # 期待列数がない場合は最初に成功した方法を使用
                        print(f"   {method_name:12}: {test_columns:3}列", end="")
                        if df is None:
                            df = test_df
                            data_columns = test_columns
                            method_used = method_name
                            print(f" ← SELECTED")
                        else:
                            print("")
                else:
                    print(f"   {method_name:12}: FAILED (列数不足)")
                            
            except Exception as e:
                print(f"   {method_name:12}: ERROR - {str(e)[:30]}...")
                continue
        
        # データ型推定
        if df is not None:
            data_types = [pd.api.types.infer_dtype(df[col], skipna=True) for col in df.columns]
            print(f"\n📋 データ型推定完了: {len(data_types)}種類の型を検出")
        
        # 4. 結果の決定（期待列数を最優先）
        print(f"\n📈 解析結果サマリー")
        if expected_columns != 'N/A':
            # 期待列数がある場合は、それを正解とする
            actual_columns = expected_columns
            print(f"   期待列数: {expected_columns}")
            print(f"   ヘッダー検出列数: {header_columns}")  
            print(f"   データ検出列数: {data_columns}")
            print(f"   → 採用列数: {actual_columns} (期待値を採用)")
            
            # 不規則性の判定
            if header_columns and abs(header_columns - expected_columns) > 5:
                is_irregular = 'Yes (Header Column Mismatch)'
                print(f"   🚨 不規則判定: ヘッダー列数不一致")
            elif data_columns and abs(data_columns - expected_columns) > 5:
                is_irregular = 'Yes (Data Column Mismatch)'  
                print(f"   🚨 不規則判定: データ列数不一致")
            else:
                is_irregular = 'Yes (Known Irregular - Resolved)'
                print(f"   ✅ 不規則判定: 既知の不規則ファイル（解決済み）")
        else:
            # 期待列数がない場合
            actual_columns = data_columns if data_columns else header_columns
            is_irregular = 'Yes (Unknown Structure)'
            print(f"   ⚠️  不規則判定: 構造不明")
        
        delimiter_desc = f"Header: {header_delimiter} ({header_columns if header_columns else 'N/A'} cols), Data: {method_used} ({data_columns if data_columns else 'N/A'} cols)"
        
        return delimiter_desc, data_types, actual_columns, is_irregular
        
    except Exception as e:
        print(f"全体的な解析エラー: {e}")
        return 'Analysis Failed', ['N/A'], 0, 'Yes (Analysis Error)'

def manual_parse_data_lines(file_path, encoding):
    """手動でデータ行を解析"""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            lines = f.readlines()[1:6]  # ヘッダーをスキップして5行取得
        
        parsed_data = []
        for line in lines:
            # 複数の空白文字で分割
            parts = re.split(r'\s+', line.strip())
            parts = [p for p in parts if p]  # 空文字列を除去
            parsed_data.append(parts)
        
        if parsed_data:
            # 最大列数を取得
            max_cols = max(len(row) for row in parsed_data)
            # DataFrameに変換（欠損値はNaNで埋める）
            df_data = []
            for row in parsed_data:
                padded_row = row + [None] * (max_cols - len(row))
                df_data.append(padded_row)
            
            df = pd.DataFrame(df_data)
            return df
        
    except Exception as e:
        print(f"手動解析エラー: {e}")
        return None

def analyze_files(file_paths):
    results = []
    known_irregular = {
        'ZS58MONTH.csv': {'columns': 38},
        'ZS61KDAY.csv': {'columns': 68},
    }
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        is_irregular = 'No'
        expected_columns = 'N/A'
        
        encoding, confidence = detect_encoding(file_path)

        if file_name in known_irregular:
            expected_columns = known_irregular[file_name]['columns']
            
            # 新しい頑健な解析関数を使用
            delimiter_final, data_types, actual_columns, is_irregular = analyze_irregular_file_robust(
                file_path, encoding, expected_columns, file_name
            )
                        
        else:
            delimiter_final, data_types = detect_delimiter_and_types_revised(file_path, encoding)
            actual_columns = len(data_types)
            if delimiter_final not in [',', '\t', 'N/A']:
                is_irregular = 'Yes (Unusual Delimiter)'

        if expected_columns != 'N/A' and actual_columns != expected_columns:
            if is_irregular == 'No':  # まだ不規則と判定されていない場合のみ
                is_irregular = 'Yes (Column Mismatch)'

        types_str = ", ".join(f"{t}" for t in data_types)  # 全ての型を表示
            
        results.append({
            'File Path': file_path,
            'Irregular': is_irregular,
            'Expected Columns': expected_columns,
            'Actual Columns': actual_columns,
            'Delimiter': delimiter_final,
            'Encoding': encoding,
            'Data Types': types_str
        })
    return results

def select_files():
    file_paths = filedialog.askopenfilenames(
        title="ファイルを選択してください",
        filetypes=[("CSV files", "*.csv")]
    )
    if file_paths:
        run_analysis(file_paths)

def run_analysis(file_paths):
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "分析中...\n")
    root.update()  # UIの更新
    
    # ターミナル出力をGUIにもリダイレクトするためのクラス
    class TextRedirector:
        def __init__(self, widget):
            self.widget = widget
        
        def write(self, text):
            self.widget.insert(tk.END, text)
            self.widget.see(tk.END)  # 自動スクロール
            root.update()  # リアルタイム表示
        
        def flush(self):
            pass
    
    # 標準出力をGUIにリダイレクト
    import sys
    old_stdout = sys.stdout
    sys.stdout = TextRedirector(result_text)
    
    try:
        print("="*80)
        print("CSV FILE ANALYSIS REPORT - SQLite格納前チェック")
        print("="*80)
        
        results = analyze_files(file_paths)
        
        print("\n" + "="*80)
        print("SUMMARY REPORT")
        print("="*80)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n[ファイル {i}] {os.path.basename(result['File Path'])}")
                print("-" * 50)
                
                # SQLite格納に重要な情報を強調表示
                if result['Irregular'] != 'No':
                    print(f"⚠️  IRREGULAR FILE: {result['Irregular']}")
                else:
                    print("✅ REGULAR FILE")
                    
                print(f"📊 列数: 期待={result['Expected Columns']}, 実際={result['Actual Columns']}")
                print(f"🔤 エンコーディング: {result['Encoding']}")
                print(f"📝 区切り文字: {result['Delimiter']}")
                
                # SQLite格納時の注意事項
                if result['Irregular'] != 'No':
                    print("🚨 SQLite格納時の注意:")
                    if 'Column Mismatch' in result['Irregular']:
                        print("   - 列数不一致のため、スキーマ定義要確認")
                    if 'Header/Data Mismatch' in result['Irregular']:
                        print("   - ヘッダーとデータで構造が異なります")
                    if 'regex' in result['Delimiter']:
                        print("   - 正規表現区切り文字使用、パース処理要注意")
                    print("   - 手動でのスキーマ定義を推奨")
                else:
                    print("✅ SQLite格納: 標準的な処理で問題なし")
                
                # データ型サマリー（重要な型のみ抜粋）
                types_list = result['Data Types'].split(', ')
                type_counts = {}
                for t in types_list:
                    type_counts[t] = type_counts.get(t, 0) + 1
                
                print("📋 データ型サマリー:")
                for dtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   {dtype}: {count}列")
                
        print("\n" + "="*80)
        print("ANALYSIS COMPLETED")
        print("="*80)
        messagebox.showinfo("完了", "詳細な分析結果をご確認ください。\nターミナル出力に重要な情報が含まれています。")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        messagebox.showerror("エラー", f"分析中にエラーが発生しました: {e}")
    finally:
        # 標準出力を元に戻す
        sys.stdout = old_stdout

# メインウィンドウの設定
root = tk.Tk()
root.title("ファイルアナライザー")
root.geometry("800x600")

# ウィジェットの作成
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

select_button = tk.Button(frame, text="ファイルを選択して分析開始", command=select_files, font=("Arial", 12))
select_button.pack(pady=10)

result_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=90, height=30, font=("Courier New", 10))
result_text.pack(fill=tk.BOTH, expand=True)

# GUIのメインループ開始
root.mainloop()