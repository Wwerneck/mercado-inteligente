from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def read_parquet_dataset(path: Path) -> pd.DataFrame:
    files = sorted(path.rglob("*.parquet"))
    if not files:
        return pd.DataFrame()
    tables = [pq.read_table(file) for file in files]
    return pa.concat_tables(tables, promote_options="default").to_pandas()


def write_parquet(frame: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, path)
    return path

