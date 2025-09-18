#!/usr/bin/env python3
"""
T002: バックアップ機能の実装
"""

import os
import shutil
import sqlite3
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import asdict
from t002_data_structures import BackupInfo, ModificationBatch

class BackupManager:
    """バックアップ管理クラス"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.backup_index_file = self.backup_dir / "backup_index.json"
        self.backups: List[BackupInfo] = []
        self.load_backup_index()
    
    def load_backup_index(self) -> None:
        """バックアップインデックスを読み込み"""
        if self.backup_index_file.exists():
            try:
                with open(self.backup_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.backups = [
                        BackupInfo(
                            backup_id=item["backup_id"],
                            original_db_path=item["original_db_path"],
                            backup_path=item["backup_path"],
                            batch_id=item["batch_id"],
                            created_at=datetime.fromisoformat(item["created_at"]),
                            size_bytes=item["size_bytes"],
                            checksum=item["checksum"],
                            description=item["description"]
                        )
                        for item in data
                    ]
            except Exception as e:
                print(f"バックアップインデックス読み込みエラー: {e}")
                self.backups = []
    
    def save_backup_index(self) -> None:
        """バックアップインデックスを保存"""
        try:
            data = [
                {
                    "backup_id": backup.backup_id,
                    "original_db_path": backup.original_db_path,
                    "backup_path": backup.backup_path,
                    "batch_id": backup.batch_id,
                    "created_at": backup.created_at.isoformat(),
                    "size_bytes": backup.size_bytes,
                    "checksum": backup.checksum,
                    "description": backup.description
                }
                for backup in self.backups
            ]
            
            with open(self.backup_index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"バックアップインデックス保存エラー: {e}")
    
    def calculate_file_checksum(self, file_path: str) -> str:
        """ファイルのチェックサムを計算"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            print(f"チェックサム計算エラー: {e}")
            return ""
    
    def create_backup(self, db_path: str, batch: ModificationBatch, 
                     description: str = "") -> Optional[BackupInfo]:
        """データベースのバックアップを作成"""
        try:
            # バックアップファイル名を生成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{batch.batch_id}_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # ファイルをコピー
            shutil.copy2(db_path, backup_path)
            
            # バックアップ情報を作成
            file_size = os.path.getsize(backup_path)
            checksum = self.calculate_file_checksum(str(backup_path))
            
            backup_info = BackupInfo(
                backup_id=f"backup_{timestamp}",
                original_db_path=db_path,
                backup_path=str(backup_path),
                batch_id=batch.batch_id,
                created_at=datetime.now(),
                size_bytes=file_size,
                checksum=checksum,
                description=description or f"Backup for batch: {batch.name}"
            )
            
            self.backups.append(backup_info)
            self.save_backup_index()
            
            print(f"バックアップ作成完了: {backup_path}")
            return backup_info
            
        except Exception as e:
            print(f"バックアップ作成エラー: {e}")
            return None
    
    def restore_backup(self, backup_id: str, target_path: str) -> bool:
        """バックアップからリストア"""
        backup = self.get_backup_by_id(backup_id)
        if not backup:
            print(f"バックアップが見つかりません: {backup_id}")
            return False
        
        try:
            # バックアップファイルの整合性チェック
            if not self.verify_backup_integrity(backup):
                print(f"バックアップファイルの整合性チェックに失敗: {backup_id}")
                return False
            
            # リストア実行
            shutil.copy2(backup.backup_path, target_path)
            print(f"リストア完了: {backup.backup_path} -> {target_path}")
            return True
            
        except Exception as e:
            print(f"リストアエラー: {e}")
            return False
    
    def verify_backup_integrity(self, backup: BackupInfo) -> bool:
        """バックアップファイルの整合性を検証"""
        try:
            # ファイル存在チェック
            if not os.path.exists(backup.backup_path):
                print(f"バックアップファイルが存在しません: {backup.backup_path}")
                return False
            
            # サイズチェック
            current_size = os.path.getsize(backup.backup_path)
            if current_size != backup.size_bytes:
                print(f"ファイルサイズが一致しません: {current_size} != {backup.size_bytes}")
                return False
            
            # チェックサムチェック
            current_checksum = self.calculate_file_checksum(backup.backup_path)
            if current_checksum != backup.checksum:
                print(f"チェックサムが一致しません: {current_checksum} != {backup.checksum}")
                return False
            
            # SQLiteファイルとして開けるかチェック
            conn = sqlite3.connect(backup.backup_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()
            
            if not tables:
                print("有効なSQLiteファイルではありません")
                return False
            
            return True
            
        except Exception as e:
            print(f"整合性チェックエラー: {e}")
            return False
    
    def get_backup_by_id(self, backup_id: str) -> Optional[BackupInfo]:
        """IDでバックアップを取得"""
        for backup in self.backups:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def get_backups_by_batch(self, batch_id: str) -> List[BackupInfo]:
        """バッチIDでバックアップを取得"""
        return [backup for backup in self.backups if backup.batch_id == batch_id]
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """バックアップ一覧を取得"""
        return [
            {
                "backup_id": backup.backup_id,
                "batch_id": backup.batch_id,
                "created_at": backup.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "size_mb": round(backup.size_bytes / 1024 / 1024, 2),
                "description": backup.description,
                "integrity": self.verify_backup_integrity(backup)
            }
            for backup in sorted(self.backups, key=lambda x: x.created_at, reverse=True)
        ]
    
    def cleanup_old_backups(self, keep_days: int = 30) -> int:
        """古いバックアップを削除"""
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_date = cutoff_date.replace(day=cutoff_date.day - keep_days)
        
        deleted_count = 0
        backups_to_remove = []
        
        for backup in self.backups:
            if backup.created_at < cutoff_date:
                try:
                    if os.path.exists(backup.backup_path):
                        os.remove(backup.backup_path)
                    backups_to_remove.append(backup)
                    deleted_count += 1
                    print(f"古いバックアップを削除: {backup.backup_id}")
                except Exception as e:
                    print(f"バックアップ削除エラー ({backup.backup_id}): {e}")
        
        # インデックスから削除
        for backup in backups_to_remove:
            self.backups.remove(backup)
        
        if backups_to_remove:
            self.save_backup_index()
        
        return deleted_count
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """バックアップ統計情報を取得"""
        if not self.backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "oldest_backup": None,
                "newest_backup": None,
                "integrity_ok": 0,
                "integrity_failed": 0
            }
        
        total_size = sum(backup.size_bytes for backup in self.backups)
        sorted_backups = sorted(self.backups, key=lambda x: x.created_at)
        
        integrity_ok = 0
        integrity_failed = 0
        
        for backup in self.backups:
            if self.verify_backup_integrity(backup):
                integrity_ok += 1
            else:
                integrity_failed += 1
        
        return {
            "total_backups": len(self.backups),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "oldest_backup": sorted_backups[0].created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "newest_backup": sorted_backups[-1].created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "integrity_ok": integrity_ok,
            "integrity_failed": integrity_failed
        }

def main():
    """テスト実行"""
    from t002_data_structures import ModificationBatch
    
    backup_manager = BackupManager()
    
    print("=== バックアップシステムテスト ===")
    
    # テスト用バッチ
    test_batch = ModificationBatch(
        batch_id="test_batch_001",
        name="テストバッチ",
        description="バックアップテスト用"
    )
    
    # 既存のDBファイルがある場合のテスト
    db_path = "output/master.db"
    if os.path.exists(db_path):
        backup_info = backup_manager.create_backup(db_path, test_batch, "テスト用バックアップ")
        if backup_info:
            print(f"バックアップ作成成功: {backup_info.backup_id}")
            
            # 整合性チェック
            if backup_manager.verify_backup_integrity(backup_info):
                print("整合性チェック: OK")
            else:
                print("整合性チェック: NG")
    
    # バックアップ一覧表示
    backups = backup_manager.list_backups()
    print(f"\nバックアップ一覧: {len(backups)}件")
    for backup in backups:
        print(f"  - {backup['backup_id']}: {backup['size_mb']}MB ({backup['created_at']})")
    
    # 統計情報表示
    stats = backup_manager.get_backup_statistics()
    print(f"\n統計情報:")
    print(f"  総バックアップ数: {stats['total_backups']}")
    print(f"  総サイズ: {stats['total_size_mb']}MB")
    print(f"  整合性OK: {stats['integrity_ok']}")
    print(f"  整合性NG: {stats['integrity_failed']}")

if __name__ == "__main__":
    main()