import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def bronze_partition_path(base_dir: Path, entity: str, ingested_at: datetime) -> Path:
    return (
        base_dir
        / "bronze"
        / entity
        / f"year={ingested_at:%Y}"
        / f"month={ingested_at:%m}"
        / f"day={ingested_at:%d}"
    )


def build_bronze_records(
    payloads: list[dict[str, Any]],
    source: str,
    endpoint: str,
    ingested_at: datetime | None = None,
) -> list[dict[str, Any]]:
    current_time = ingested_at or datetime.now(UTC)
    return [
        {
            "ingested_at": current_time.isoformat(),
            "source": source,
            "endpoint": endpoint,
            "record_id": payload.get("id") or payload.get("domain_id") or payload.get("category_id"),
            "payload": payload,
        }
        for payload in payloads
    ]


def write_bronze_dataset(
    records: list[dict[str, Any]],
    base_dir: Path,
    entity: str,
    ingested_at: datetime | None = None,
) -> dict[str, Any]:
    current_time = ingested_at or datetime.now(UTC)
    output_dir = bronze_partition_path(base_dir, entity, current_time)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = current_time.strftime("%Y%m%dT%H%M%SZ")
    jsonl_path = output_dir / f"{entity}_{timestamp}.jsonl"
    parquet_path = output_dir / f"{entity}_{timestamp}.parquet"

    with jsonl_path.open("w", encoding="utf-8") as fp:
        for record in records:
            fp.write(json.dumps(record, ensure_ascii=False) + "\n")

    frame = pd.DataFrame(records)
    if not frame.empty:
        frame["payload"] = frame["payload"].apply(lambda value: json.dumps(value, ensure_ascii=False))
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, parquet_path)

    return {
        "entity": entity,
        "rows": len(records),
        "jsonl_path": str(jsonl_path),
        "parquet_path": str(parquet_path),
    }
