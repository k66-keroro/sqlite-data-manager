import pandas as pd
from master_manager import load_master

def compare_with_master(analyzed: pd.DataFrame):
    master = load_master()

    merged = analyzed.merge(
        master,
        on=["file_name", "column_name"],
        how="left",
        suffixes=("", "_master")
    )

    # 新しい列（マスタ未登録）
    new_cols = merged[merged["data_type_master"].isna()][
        ["file_name", "column_name", "data_type"]
    ]

    # データ型不一致（登録済みだけど推定型と異なる）
    type_mismatch = merged[
        (~merged["data_type_master"].isna()) &
        (merged["data_type"] != merged["data_type_master"])
    ][["file_name", "column_name", "data_type", "data_type_master"]]

    return new_cols, type_mismatch
