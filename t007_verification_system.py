#!/usr/bin/env python3
"""
T007: 修正結果の検証機能
"""

import sqlite3
import json
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from t002_data_structures import ModificationBatch, FieldType

@dataclass
class DataIntegrityCheck:
    """データ整合性チェック結果"""
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error

@dataclass
class FieldStatistics:
    """フィールド統計情報"""
    field_name: str
    table_name: str
    total_rows: int
    null_count: int
    unique_count: int
    data_type: str
    sample_values: List[str] = field(default_factory=list)
    min_length: int = 0
    max_length: int = 0
    avg_length: float = 0.0

@dataclass
class VerificationReport:
    """検証レポート"""
    batch_id: str
    verification_time: datetime
    overall_status: str  # passed, warning, failed
    integrity_checks: List[DataIntegrityCheck] = field(default_factory=list)
    statistics_before: Dict[str, FieldStatistics] = field(default_factory=dict)
    statistics_after: Dict[str, FieldStatistics] = field(default_factory=dict)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

class VerificationSystem:
    """修正結果検証システム"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.verification_history: List[VerificationReport] = []
    
    def verify_modification_batch(self, batch: ModificationBatch, 
                                backup_path: str = None) -> VerificationReport:
        """修正バッチの結果を検証"""
        print(f"=== 修正結果検証開始: {batch.name} ===")
        
        report = VerificationReport(
            batch_id=batch.batch_id,
            verification_time=datetime.now(),
            overall_status="passed"
        )
        
        try:
            # 1. データ整合性チェック
            integrity_checks = self._perform_integrity_checks(batch)
            report.integrity_checks = integrity_checks
            
            # 2. 統計情報比較
            if backup_path:
                stats_before = self._collect_field_statistics(backup_path, batch)
                stats_after = self._collect_field_statistics(self.db_path, batch)
                report.statistics_before = stats_before
                report.statistics_after = stats_after
            
            # 3. 異常値検出
            anomalies = self._detect_anomalies(batch)
            report.anomalies = anomalies
            
            # 4. パフォーマンス測定
            performance = self._measure_performance(batch)
            report.performance_metrics = performance
            
            # 5. 全体ステータス判定
            report.overall_status = self._determine_overall_status(report)
            
            # 6. レポート保存
            self._save_verification_report(report)
            
            print(f"検証完了: {report.overall_status}")
            return report
            
        except Exception as e:
            print(f"検証エラー: {e}")
            report.overall_status = "failed"
            report.integrity_checks.append(
                DataIntegrityCheck(
                    check_name="verification_system_error",
                    passed=False,
                    message=f"検証システムエラー: {str(e)}",
                    severity="error"
                )
            )
            return report
    
    def _perform_integrity_checks(self, batch: ModificationBatch) -> List[DataIntegrityCheck]:
        """データ整合性チェックを実行"""
        checks = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # チェック1: テーブル存在確認
            checks.append(self._check_table_existence(cursor, batch))
            
            # チェック2: カラム型整合性
            checks.append(self._check_column_type_consistency(cursor, batch))
            
            # チェック3: データ値妥当性
            checks.append(self._check_data_value_validity(cursor, batch))
            
            # チェック4: 外部キー整合性
            checks.append(self._check_foreign_key_integrity(cursor, batch))
            
            # チェック5: NULL値制約
            checks.append(self._check_null_constraints(cursor, batch))
            
        finally:
            conn.close()
        
        return checks
    
    def _check_table_existence(self, cursor: sqlite3.Cursor, 
                             batch: ModificationBatch) -> DataIntegrityCheck:
        """テーブル存在確認"""
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            required_tables = {
                mod.file_name.replace('.txt', '').replace('.csv', '') 
                for mod in batch.modifications
            }
            
            missing_tables = required_tables - existing_tables
            
            if missing_tables:
                return DataIntegrityCheck(
                    check_name="table_existence",
                    passed=False,
                    message=f"不足テーブル: {', '.join(missing_tables)}",
                    details={"missing_tables": list(missing_tables)},
                    severity="error"
                )
            else:
                return DataIntegrityCheck(
                    check_name="table_existence",
                    passed=True,
                    message="すべてのテーブルが存在します",
                    details={"checked_tables": list(required_tables)}
                )
        
        except Exception as e:
            return DataIntegrityCheck(
                check_name="table_existence",
                passed=False,
                message=f"テーブル存在確認エラー: {str(e)}",
                severity="error"
            )
    
    def _check_column_type_consistency(self, cursor: sqlite3.Cursor, 
                                     batch: ModificationBatch) -> DataIntegrityCheck:
        """カラム型整合性チェック"""
        try:
            inconsistencies = []
            
            for modification in batch.modifications:
                table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
                
                try:
                    # 実際のテーブル構造を確認
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = {row[1]: row[2] for row in cursor.fetchall()}
                    
                    if modification.column_name in columns:
                        actual_type = columns[modification.column_name]
                        expected_type = modification.target_type.value
                        
                        # SQLiteの型マッピング確認
                        if not self._types_compatible(actual_type, expected_type):
                            inconsistencies.append({
                                "table": table_name,
                                "column": modification.column_name,
                                "expected": expected_type,
                                "actual": actual_type
                            })
                    else:
                        inconsistencies.append({
                            "table": table_name,
                            "column": modification.column_name,
                            "error": "カラムが存在しません"
                        })
                
                except Exception as e:
                    inconsistencies.append({
                        "table": table_name,
                        "error": str(e)
                    })
            
            if inconsistencies:
                return DataIntegrityCheck(
                    check_name="column_type_consistency",
                    passed=False,
                    message=f"型不整合: {len(inconsistencies)}件",
                    details={"inconsistencies": inconsistencies},
                    severity="warning"
                )
            else:
                return DataIntegrityCheck(
                    check_name="column_type_consistency",
                    passed=True,
                    message="カラム型は整合しています"
                )
        
        except Exception as e:
            return DataIntegrityCheck(
                check_name="column_type_consistency",
                passed=False,
                message=f"型整合性チェックエラー: {str(e)}",
                severity="error"
            )
    
    def _check_data_value_validity(self, cursor: sqlite3.Cursor, 
                                 batch: ModificationBatch) -> DataIntegrityCheck:
        """データ値妥当性チェック"""
        try:
            invalid_values = []
            
            for modification in batch.modifications:
                table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
                
                try:
                    # 型に応じた妥当性チェック
                    if modification.target_type == FieldType.INTEGER:
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE {modification.column_name} IS NOT NULL 
                            AND {modification.column_name} NOT GLOB '*[0-9]*'
                        """)
                        invalid_count = cursor.fetchone()[0]
                        
                        if invalid_count > 0:
                            invalid_values.append({
                                "table": table_name,
                                "column": modification.column_name,
                                "type": "INTEGER",
                                "invalid_count": invalid_count
                            })
                    
                    elif modification.target_type == FieldType.REAL:
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE {modification.column_name} IS NOT NULL 
                            AND {modification.column_name} NOT GLOB '*[0-9.]*'
                        """)
                        invalid_count = cursor.fetchone()[0]
                        
                        if invalid_count > 0:
                            invalid_values.append({
                                "table": table_name,
                                "column": modification.column_name,
                                "type": "REAL",
                                "invalid_count": invalid_count
                            })
                    
                    elif modification.target_type == FieldType.DATETIME:
                        # 日付形式の妥当性チェック
                        cursor.execute(f"""
                            SELECT COUNT(*) FROM {table_name} 
                            WHERE {modification.column_name} IS NOT NULL 
                            AND LENGTH({modification.column_name}) < 10
                        """)
                        invalid_count = cursor.fetchone()[0]
                        
                        if invalid_count > 0:
                            invalid_values.append({
                                "table": table_name,
                                "column": modification.column_name,
                                "type": "DATETIME",
                                "invalid_count": invalid_count
                            })
                
                except Exception as e:
                    invalid_values.append({
                        "table": table_name,
                        "column": modification.column_name,
                        "error": str(e)
                    })
            
            if invalid_values:
                return DataIntegrityCheck(
                    check_name="data_value_validity",
                    passed=False,
                    message=f"無効な値: {len(invalid_values)}件",
                    details={"invalid_values": invalid_values},
                    severity="warning"
                )
            else:
                return DataIntegrityCheck(
                    check_name="data_value_validity",
                    passed=True,
                    message="データ値は妥当です"
                )
        
        except Exception as e:
            return DataIntegrityCheck(
                check_name="data_value_validity",
                passed=False,
                message=f"データ値妥当性チェックエラー: {str(e)}",
                severity="error"
            )
    
    def _check_foreign_key_integrity(self, cursor: sqlite3.Cursor, 
                                   batch: ModificationBatch) -> DataIntegrityCheck:
        """外部キー整合性チェック"""
        try:
            # 外部キー制約の確認
            cursor.execute("PRAGMA foreign_key_check")
            fk_violations = cursor.fetchall()
            
            if fk_violations:
                return DataIntegrityCheck(
                    check_name="foreign_key_integrity",
                    passed=False,
                    message=f"外部キー制約違反: {len(fk_violations)}件",
                    details={"violations": fk_violations},
                    severity="error"
                )
            else:
                return DataIntegrityCheck(
                    check_name="foreign_key_integrity",
                    passed=True,
                    message="外部キー制約は正常です"
                )
        
        except Exception as e:
            return DataIntegrityCheck(
                check_name="foreign_key_integrity",
                passed=False,
                message=f"外部キー整合性チェックエラー: {str(e)}",
                severity="error"
            )
    
    def _check_null_constraints(self, cursor: sqlite3.Cursor, 
                              batch: ModificationBatch) -> DataIntegrityCheck:
        """NULL値制約チェック"""
        try:
            null_violations = []
            
            for modification in batch.modifications:
                table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
                
                try:
                    # NULL値の統計を取得
                    cursor.execute(f"""
                        SELECT COUNT(*) as total, 
                               COUNT({modification.column_name}) as non_null
                        FROM {table_name}
                    """)
                    total, non_null = cursor.fetchone()
                    null_count = total - non_null
                    null_ratio = null_count / total if total > 0 else 0
                    
                    # NULL値が多すぎる場合は警告
                    if null_ratio > 0.5:  # 50%以上がNULL
                        null_violations.append({
                            "table": table_name,
                            "column": modification.column_name,
                            "null_count": null_count,
                            "total_count": total,
                            "null_ratio": null_ratio
                        })
                
                except Exception as e:
                    null_violations.append({
                        "table": table_name,
                        "column": modification.column_name,
                        "error": str(e)
                    })
            
            if null_violations:
                return DataIntegrityCheck(
                    check_name="null_constraints",
                    passed=False,
                    message=f"NULL値が多いフィールド: {len(null_violations)}件",
                    details={"null_violations": null_violations},
                    severity="warning"
                )
            else:
                return DataIntegrityCheck(
                    check_name="null_constraints",
                    passed=True,
                    message="NULL値制約は正常です"
                )
        
        except Exception as e:
            return DataIntegrityCheck(
                check_name="null_constraints",
                passed=False,
                message=f"NULL値制約チェックエラー: {str(e)}",
                severity="error"
            )
    
    def _types_compatible(self, actual_type: str, expected_type: str) -> bool:
        """SQLite型の互換性チェック"""
        # SQLiteの型アフィニティを考慮
        type_mapping = {
            "TEXT": ["TEXT", "VARCHAR", "CHAR"],
            "INTEGER": ["INTEGER", "INT", "BIGINT"],
            "REAL": ["REAL", "FLOAT", "DOUBLE", "NUMERIC"],
            "DATETIME": ["DATETIME", "TIMESTAMP", "DATE"]
        }
        
        for canonical_type, variants in type_mapping.items():
            if expected_type == canonical_type:
                return actual_type.upper() in [v.upper() for v in variants]
        
        return actual_type.upper() == expected_type.upper()
    
    def _collect_field_statistics(self, db_path: str, 
                                batch: ModificationBatch) -> Dict[str, FieldStatistics]:
        """フィールド統計情報を収集"""
        statistics = {}
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            for modification in batch.modifications:
                table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
                field_key = f"{table_name}.{modification.column_name}"
                
                try:
                    # 基本統計
                    cursor.execute(f"""
                        SELECT COUNT(*) as total,
                               COUNT({modification.column_name}) as non_null,
                               COUNT(DISTINCT {modification.column_name}) as unique_count
                        FROM {table_name}
                    """)
                    total, non_null, unique_count = cursor.fetchone()
                    null_count = total - non_null
                    
                    # サンプル値
                    cursor.execute(f"""
                        SELECT {modification.column_name} 
                        FROM {table_name} 
                        WHERE {modification.column_name} IS NOT NULL 
                        LIMIT 10
                    """)
                    sample_values = [str(row[0]) for row in cursor.fetchall()]
                    
                    # 長さ統計（文字列の場合）
                    min_length = max_length = avg_length = 0
                    if sample_values:
                        lengths = [len(str(val)) for val in sample_values]
                        min_length = min(lengths)
                        max_length = max(lengths)
                        avg_length = statistics.mean(lengths) if lengths else 0
                    
                    field_stats = FieldStatistics(
                        field_name=modification.column_name,
                        table_name=table_name,
                        total_rows=total,
                        null_count=null_count,
                        unique_count=unique_count,
                        data_type=modification.target_type.value,
                        sample_values=sample_values,
                        min_length=min_length,
                        max_length=max_length,
                        avg_length=avg_length
                    )
                    
                    statistics[field_key] = field_stats
                
                except Exception as e:
                    print(f"統計収集エラー ({field_key}): {e}")
                    continue
        
        finally:
            conn.close()
        
        return statistics
    
    def _detect_anomalies(self, batch: ModificationBatch) -> List[Dict[str, Any]]:
        """異常値を検出"""
        anomalies = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for modification in batch.modifications:
                table_name = modification.file_name.replace('.txt', '').replace('.csv', '')
                
                try:
                    # 数値型の場合の異常値検出
                    if modification.target_type in [FieldType.INTEGER, FieldType.REAL]:
                        cursor.execute(f"""
                            SELECT {modification.column_name}
                            FROM {table_name}
                            WHERE {modification.column_name} IS NOT NULL
                            AND CAST({modification.column_name} AS REAL) IS NOT NULL
                        """)
                        values = [float(row[0]) for row in cursor.fetchall() if row[0] is not None]
                        
                        if len(values) > 10:  # 十分なデータがある場合
                            mean_val = statistics.mean(values)
                            stdev_val = statistics.stdev(values) if len(values) > 1 else 0
                            
                            # 3σ外れ値を検出
                            if stdev_val > 0:
                                outliers = [v for v in values if abs(v - mean_val) > 3 * stdev_val]
                                
                                if outliers:
                                    anomalies.append({
                                        "type": "statistical_outlier",
                                        "table": table_name,
                                        "column": modification.column_name,
                                        "outlier_count": len(outliers),
                                        "total_values": len(values),
                                        "sample_outliers": outliers[:5]
                                    })
                    
                    # 文字列長の異常値検出
                    elif modification.target_type == FieldType.TEXT:
                        cursor.execute(f"""
                            SELECT LENGTH({modification.column_name}) as len
                            FROM {table_name}
                            WHERE {modification.column_name} IS NOT NULL
                        """)
                        lengths = [row[0] for row in cursor.fetchall()]
                        
                        if lengths:
                            avg_length = statistics.mean(lengths)
                            
                            # 平均の10倍以上の長さを異常値とする
                            long_values = [l for l in lengths if l > avg_length * 10]
                            
                            if long_values:
                                anomalies.append({
                                    "type": "unusual_length",
                                    "table": table_name,
                                    "column": modification.column_name,
                                    "unusual_count": len(long_values),
                                    "avg_length": avg_length,
                                    "max_length": max(long_values)
                                })
                
                except Exception as e:
                    anomalies.append({
                        "type": "detection_error",
                        "table": table_name,
                        "column": modification.column_name,
                        "error": str(e)
                    })
        
        finally:
            conn.close()
        
        return anomalies
    
    def _measure_performance(self, batch: ModificationBatch) -> Dict[str, Any]:
        """パフォーマンス測定"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # データベースサイズ
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            
            # テーブル数
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            # インデックス数
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index'")
            index_count = cursor.fetchone()[0]
            
            return {
                "database_size_bytes": db_size,
                "database_size_mb": round(db_size / 1024 / 1024, 2),
                "table_count": table_count,
                "index_count": index_count,
                "modifications_count": len(batch.modifications)
            }
        
        finally:
            conn.close()
    
    def _determine_overall_status(self, report: VerificationReport) -> str:
        """全体ステータスを判定"""
        error_count = sum(1 for check in report.integrity_checks if not check.passed and check.severity == "error")
        warning_count = sum(1 for check in report.integrity_checks if not check.passed and check.severity == "warning")
        
        if error_count > 0:
            return "failed"
        elif warning_count > 0:
            return "warning"
        else:
            return "passed"
    
    def _save_verification_report(self, report: VerificationReport) -> None:
        """検証レポートを保存"""
        try:
            reports_dir = Path("verification_reports")
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"verification_{report.batch_id}_{report.verification_time.strftime('%Y%m%d_%H%M%S')}.json"
            
            # レポートをJSON形式で保存
            report_data = {
                "batch_id": report.batch_id,
                "verification_time": report.verification_time.isoformat(),
                "overall_status": report.overall_status,
                "integrity_checks": [
                    {
                        "check_name": check.check_name,
                        "passed": check.passed,
                        "message": check.message,
                        "details": check.details,
                        "severity": check.severity
                    }
                    for check in report.integrity_checks
                ],
                "anomalies": report.anomalies,
                "performance_metrics": report.performance_metrics
            }
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            print(f"検証レポート保存: {report_file}")
            
        except Exception as e:
            print(f"レポート保存エラー: {e}")

def main():
    """テスト実行"""
    print("=== 検証システムテスト ===")
    
    if not Path("output/master.db").exists():
        print("テスト用データベースが見つかりません")
        return
    
    from t002_data_structures import ModificationBatch, FieldModification, FieldType, ModificationAction, ConfidenceLevel
    
    # テスト用バッチ
    test_batch = ModificationBatch(
        batch_id="test_verification_001",
        name="検証テストバッチ",
        description="検証システムのテスト",
        modifications=[
            FieldModification(
                file_name="test.txt",
                column_name="test_field",
                current_type=FieldType.TEXT,
                target_type=FieldType.INTEGER,
                action=ModificationAction.TYPE_CHANGE,
                confidence=ConfidenceLevel.HIGH,
                reason="テスト用修正"
            )
        ]
    )
    
    verification_system = VerificationSystem("output/master.db")
    report = verification_system.verify_modification_batch(test_batch)
    
    print(f"検証結果: {report.overall_status}")
    print(f"整合性チェック: {len(report.integrity_checks)}件")
    print(f"異常値: {len(report.anomalies)}件")

if __name__ == "__main__":
    main()