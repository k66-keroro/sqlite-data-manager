#!/usr/bin/env python3
"""
T002: データ型修正支援ツール基盤 - データ構造設計
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum
import json

class FieldType(Enum):
    """サポートするフィールド型"""
    TEXT = "TEXT"
    INTEGER = "INTEGER"
    REAL = "REAL"
    DATETIME = "DATETIME"
    BLOB = "BLOB"

class ModificationAction(Enum):
    """修正アクション"""
    TYPE_CHANGE = "type_change"
    ZERO_PADDING_REMOVE = "zero_padding_remove"
    TRAILING_MINUS_FIX = "trailing_minus_fix"
    DATE_FORMAT_FIX = "date_format_fix"
    DECIMAL_COMMA_FIX = "decimal_comma_fix"

class ConfidenceLevel(Enum):
    """信頼度レベル"""
    HIGH = "high"      # 90%以上
    MEDIUM = "medium"  # 70-89%
    LOW = "low"        # 50-69%
    VERY_LOW = "very_low"  # 50%未満

@dataclass
class FieldModification:
    """フィールド修正情報"""
    file_name: str
    column_name: str
    current_type: FieldType
    target_type: FieldType
    action: ModificationAction
    confidence: ConfidenceLevel
    reason: str
    sample_data: List[str] = field(default_factory=list)
    estimated_affected_rows: int = 0
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ModificationBatch:
    """修正バッチ"""
    batch_id: str
    name: str
    description: str
    modifications: List[FieldModification] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, in_progress, completed, failed, rolled_back
    backup_path: Optional[str] = None
    execution_log: List[str] = field(default_factory=list)

@dataclass
class ModificationRule:
    """修正ルール"""
    rule_id: str
    name: str
    description: str
    pattern: str  # 正規表現パターン
    action: ModificationAction
    target_type: FieldType
    confidence_threshold: float = 0.7
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0

@dataclass
class BackupInfo:
    """バックアップ情報"""
    backup_id: str
    original_db_path: str
    backup_path: str
    batch_id: str
    created_at: datetime
    size_bytes: int
    checksum: str
    description: str

class ModificationTemplate:
    """修正ルールテンプレート"""
    
    @staticmethod
    def get_default_rules() -> List[ModificationRule]:
        """デフォルトの修正ルールを取得"""
        return [
            ModificationRule(
                rule_id="zero_padding_removal",
                name="0パディング除去",
                description="先頭の0を除去して数値型に変換",
                pattern=r"^0+(\d+)$",
                action=ModificationAction.ZERO_PADDING_REMOVE,
                target_type=FieldType.INTEGER,
                confidence_threshold=0.8
            ),
            ModificationRule(
                rule_id="trailing_minus_fix",
                name="後ろマイナス修正",
                description="末尾のマイナスを先頭に移動",
                pattern=r"^(\d+)-$",
                action=ModificationAction.TRAILING_MINUS_FIX,
                target_type=FieldType.INTEGER,
                confidence_threshold=0.9
            ),
            ModificationRule(
                rule_id="decimal_comma_fix",
                name="小数点カンマ修正",
                description="カンマを小数点に変換",
                pattern=r"^(\d+),(\d+)$",
                action=ModificationAction.DECIMAL_COMMA_FIX,
                target_type=FieldType.REAL,
                confidence_threshold=0.8
            ),
            ModificationRule(
                rule_id="date_yyyymmdd",
                name="YYYYMMDD日付変換",
                description="8桁数値を日付型に変換",
                pattern=r"^\d{8}$",
                action=ModificationAction.DATE_FORMAT_FIX,
                target_type=FieldType.DATETIME,
                confidence_threshold=0.7
            ),
            ModificationRule(
                rule_id="numeric_text_to_real",
                name="数値テキストをREAL型に",
                description="数値のみのテキストをREAL型に変換",
                pattern=r"^\d+\.?\d*$",
                action=ModificationAction.TYPE_CHANGE,
                target_type=FieldType.REAL,
                confidence_threshold=0.8
            ),
            ModificationRule(
                rule_id="integer_text_to_int",
                name="整数テキストをINTEGER型に",
                description="整数のみのテキストをINTEGER型に変換",
                pattern=r"^\d+$",
                action=ModificationAction.TYPE_CHANGE,
                target_type=FieldType.INTEGER,
                confidence_threshold=0.9
            )
        ]

class DataStructureManager:
    """データ構造管理クラス"""
    
    def __init__(self):
        self.modifications: List[FieldModification] = []
        self.batches: List[ModificationBatch] = []
        self.rules: List[ModificationRule] = ModificationTemplate.get_default_rules()
        self.backups: List[BackupInfo] = []
    
    def add_modification(self, modification: FieldModification) -> None:
        """修正情報を追加"""
        self.modifications.append(modification)
    
    def create_batch(self, name: str, description: str, 
                    modifications: List[FieldModification]) -> ModificationBatch:
        """修正バッチを作成"""
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch = ModificationBatch(
            batch_id=batch_id,
            name=name,
            description=description,
            modifications=modifications
        )
        self.batches.append(batch)
        return batch
    
    def get_modifications_by_confidence(self, min_confidence: ConfidenceLevel) -> List[FieldModification]:
        """信頼度でフィルタした修正情報を取得"""
        confidence_order = {
            ConfidenceLevel.VERY_LOW: 0,
            ConfidenceLevel.LOW: 1,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.HIGH: 3
        }
        min_level = confidence_order[min_confidence]
        
        return [
            mod for mod in self.modifications 
            if confidence_order[mod.confidence] >= min_level
        ]
    
    def export_to_json(self, file_path: str) -> None:
        """JSON形式でエクスポート"""
        data = {
            "modifications": [self._modification_to_dict(mod) for mod in self.modifications],
            "batches": [self._batch_to_dict(batch) for batch in self.batches],
            "rules": [self._rule_to_dict(rule) for rule in self.rules],
            "backups": [self._backup_to_dict(backup) for backup in self.backups]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    
    def _modification_to_dict(self, mod: FieldModification) -> Dict:
        """FieldModificationを辞書に変換"""
        return {
            "file_name": mod.file_name,
            "column_name": mod.column_name,
            "current_type": mod.current_type.value,
            "target_type": mod.target_type.value,
            "action": mod.action.value,
            "confidence": mod.confidence.value,
            "reason": mod.reason,
            "sample_data": mod.sample_data,
            "estimated_affected_rows": mod.estimated_affected_rows,
            "validation_rules": mod.validation_rules,
            "created_at": mod.created_at.isoformat()
        }
    
    def _batch_to_dict(self, batch: ModificationBatch) -> Dict:
        """ModificationBatchを辞書に変換"""
        return {
            "batch_id": batch.batch_id,
            "name": batch.name,
            "description": batch.description,
            "modifications": [self._modification_to_dict(mod) for mod in batch.modifications],
            "created_at": batch.created_at.isoformat(),
            "status": batch.status,
            "backup_path": batch.backup_path,
            "execution_log": batch.execution_log
        }
    
    def _rule_to_dict(self, rule: ModificationRule) -> Dict:
        """ModificationRuleを辞書に変換"""
        return {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "description": rule.description,
            "pattern": rule.pattern,
            "action": rule.action.value,
            "target_type": rule.target_type.value,
            "confidence_threshold": rule.confidence_threshold,
            "enabled": rule.enabled,
            "created_at": rule.created_at.isoformat(),
            "usage_count": rule.usage_count
        }
    
    def _backup_to_dict(self, backup: BackupInfo) -> Dict:
        """BackupInfoを辞書に変換"""
        return {
            "backup_id": backup.backup_id,
            "original_db_path": backup.original_db_path,
            "backup_path": backup.backup_path,
            "batch_id": backup.batch_id,
            "created_at": backup.created_at.isoformat(),
            "size_bytes": backup.size_bytes,
            "checksum": backup.checksum,
            "description": backup.description
        }

if __name__ == "__main__":
    # テスト用のサンプル
    manager = DataStructureManager()
    
    # サンプル修正情報を作成
    sample_mod = FieldModification(
        file_name="test.txt",
        column_name="test_field",
        current_type=FieldType.TEXT,
        target_type=FieldType.INTEGER,
        action=ModificationAction.ZERO_PADDING_REMOVE,
        confidence=ConfidenceLevel.HIGH,
        reason="0パディングされた数値データ",
        sample_data=["0001", "0002", "0003"],
        estimated_affected_rows=100
    )
    
    manager.add_modification(sample_mod)
    
    # バッチを作成
    batch = manager.create_batch(
        name="テストバッチ",
        description="テスト用の修正バッチ",
        modifications=[sample_mod]
    )
    
    print(f"データ構造設計完了:")
    print(f"- 修正情報: {len(manager.modifications)}件")
    print(f"- バッチ: {len(manager.batches)}件")
    print(f"- ルール: {len(manager.rules)}件")
    print(f"- バックアップ: {len(manager.backups)}件")