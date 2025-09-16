#!/usr/bin/env python3
"""
T003 - ルール統合システム
pattern_rules.py と loader.py の統合機能
GUI操作からデータベース反映までの一貫性確保
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import sqlite3
from config import DB_FILE
import pattern_rules

class RuleIntegrationManager:
    """パターンルール管理とloader.py統合の管理クラス"""
    
    def __init__(self, pattern_rules_manager: pattern_rules.TypeCorrectionRules = None):
        self.pattern_rules = pattern_rules_manager or pattern_rules.TypeCorrectionRules()
        self.loader_updates_file = "t002_loader_updates.json"
        
    def generate_loader_updates_from_rules(self) -> Dict[str, Any]:
        """pattern_rules.pyのルールからt002_loader_updates.json形式を生成"""
        
        loader_updates = {
            "datetime_override_fields": [],
            "storage_code_fields": [],
            "total_overrides": 0
        }
        
        # 1. 未登録ファイルルールから強制TEXT化を生成
        unregistered_files = self.pattern_rules._rules_data.get('unregistered_files', {})
        
        # 2. ビジネスロジックルールから型修正を生成
        business_rules = self.pattern_rules._rules_data.get('business_logic_rules', {})
        
        # コードフィールド（保管場所など）を強制TEXT化
        code_fields = business_rules.get('code_fields', [])
        if '保管場所' in code_fields:
            # データベースから保管場所フィールドを持つファイルを取得
            storage_files = self._get_files_with_field('保管場所')
            for file_name in storage_files:
                loader_updates["storage_code_fields"].append({
                    "file": file_name,
                    "field": "保管場所", 
                    "action": "force_text"
                })
        
        # 3. 日付パターンから問題のあるDATETIMEフィールドを強制TEXT化
        datetime_patterns = self.pattern_rules._rules_data.get('datetime_patterns', [])
        
        # 既知の問題DATETIMEフィールドを追加
        problematic_datetime_fields = [
            {"file": "GetSekkeiWBSJisseki.txt", "field": "COMP_SCH_DT"},
            {"file": "zs45.txt", "field": "TecComp"}, 
            {"file": "ZS61KDAY.csv", "field": "工場出庫可能日"},
            {"file": "ZS61KDAY.csv", "field": "工場回答日"}
        ]
        
        for field_info in problematic_datetime_fields:
            loader_updates["datetime_override_fields"].append({
                **field_info,
                "action": "force_text"
            })
            
        # 4. 総数を計算
        loader_updates["total_overrides"] = (
            len(loader_updates["datetime_override_fields"]) + 
            len(loader_updates["storage_code_fields"])
        )
        
        return loader_updates
    
    def _get_files_with_field(self, field_name: str) -> List[str]:
        """指定されたフィールド名を持つファイル一覧を取得"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # column_masterから該当フィールドを持つファイルを検索
            cursor.execute(
                "SELECT DISTINCT file_name FROM column_master WHERE column_name = ?", 
                (field_name,)
            )
            
            files = [row[0] for row in cursor.fetchall()]
            conn.close()
            return files
            
        except Exception as e:
            print(f"エラー: フィールド {field_name} を持つファイル検索中: {e}")
            return []
    
    def update_loader_updates_file(self) -> bool:
        """ルールに基づいてt002_loader_updates.jsonを更新"""
        try:
            loader_updates = self.generate_loader_updates_from_rules()
            
            with open(self.loader_updates_file, 'w', encoding='utf-8') as f:
                json.dump(loader_updates, f, indent=2, ensure_ascii=False)
            
            print(f"✅ {self.loader_updates_file} を更新しました")
            print(f"   - DATETIME修正: {len(loader_updates['datetime_override_fields'])}件")
            print(f"   - 保管場所修正: {len(loader_updates['storage_code_fields'])}件") 
            print(f"   - 総修正数: {loader_updates['total_overrides']}件")
            
            return True
            
        except Exception as e:
            print(f"❌ エラー: loader更新ファイル生成中: {e}")
            return False
    
    def sync_gui_to_loader(self) -> bool:
        """GUIの変更をloader.pyに即座に反映"""
        success = self.update_loader_updates_file()
        
        if success:
            print("🔄 GUI設定がloader.pyに反映されました")
            print("💡 変更を適用するには 'python loader.py' を再実行してください")
        
        return success
    
    def get_current_rule_status(self) -> Dict[str, Any]:
        """現在のルール適用状況を取得"""
        
        # パターンルールの状況
        pattern_status = {
            "unregistered_files": len(self.pattern_rules._rules_data.get('unregistered_files', {})),
            "datetime_patterns": len(self.pattern_rules._rules_data.get('datetime_patterns', [])),
            "code_fields": len(self.pattern_rules._rules_data.get('business_logic_rules', {}).get('code_fields', [])),
            "amount_fields": len(self.pattern_rules._rules_data.get('business_logic_rules', {}).get('amount_fields', [])),
            "quantity_fields": len(self.pattern_rules._rules_data.get('business_logic_rules', {}).get('quantity_fields', []))
        }
        
        # loader更新ファイルの状況
        loader_status = {"exists": False, "total_overrides": 0}
        if Path(self.loader_updates_file).exists():
            try:
                with open(self.loader_updates_file, 'r', encoding='utf-8') as f:
                    loader_data = json.load(f)
                    loader_status = {
                        "exists": True,
                        "total_overrides": loader_data.get("total_overrides", 0),
                        "datetime_overrides": len(loader_data.get("datetime_override_fields", [])),
                        "storage_overrides": len(loader_data.get("storage_code_fields", []))
                    }
            except Exception as e:
                print(f"警告: loader更新ファイル読み込みエラー: {e}")
        
        return {
            "pattern_rules": pattern_status,
            "loader_updates": loader_status,
            "sync_required": not loader_status["exists"] or loader_status["total_overrides"] == 0
        }

def main():
    """メイン実行関数"""
    print("=== T003 ルール統合システム ===")
    
    # ルール統合管理器を初期化
    manager = RuleIntegrationManager()
    
    # 現在の状況を確認
    print("\n📊 現在のルール状況:")
    status = manager.get_current_rule_status()
    
    print(f"Pattern Rules:")
    for key, value in status["pattern_rules"].items():
        print(f"  - {key}: {value}件")
    
    print(f"Loader Updates:")
    for key, value in status["loader_updates"].items():
        print(f"  - {key}: {value}")
    
    # 同期が必要な場合は実行
    if status["sync_required"]:
        print("\n🔄 同期が必要です。loader更新ファイルを生成中...")
        manager.sync_gui_to_loader()
    else:
        print("\n✅ ルールは既に同期されています")
    
    print("\n💡 使用方法:")
    print("1. StreamlitでGUI操作を行う")
    print("2. RuleIntegrationManager.sync_gui_to_loader() を呼び出す")  
    print("3. python loader.py を実行してデータベースに反映")

if __name__ == "__main__":
    main()
