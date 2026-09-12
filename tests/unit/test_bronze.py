from datetime import UTC, datetime

import pyarrow.parquet as pq

from src.storage.bronze import bronze_partition_path, build_bronze_records, write_bronze_dataset


def test_bronze_partition_path_uses_ingestion_date(tmp_path):
    ingested_at = datetime(2026, 9, 10, tzinfo=UTC)

    path = bronze_partition_path(tmp_path, "products", ingested_at)

    assert path == tmp_path / "bronze" / "products" / "year=2026" / "month=09" / "day=10"


def test_write_bronze_dataset_creates_jsonl_and_parquet(tmp_path):
    ingested_at = datetime(2026, 9, 10, 12, 0, tzinfo=UTC)
    records = build_bronze_records(
        [{"id": "MLB1", "title": "Produto real"}],
        source="mercado_livre",
        endpoint="/sites/MLB/search",
        ingested_at=ingested_at,
    )

    output = write_bronze_dataset(records, tmp_path, "products", ingested_at)

    assert output["rows"] == 1
    table = pq.read_table(output["parquet_path"])
    assert table.num_rows == 1
    assert "payload" in table.column_names


def test_build_bronze_records_uses_alternative_identifiers():
    records = build_bronze_records(
        [{"domain_id": "MLB-NOTEBOOKS", "category_id": "MLB1652"}],
        source="mercado_livre",
        endpoint="/sites/MLB/domain_discovery/search",
        ingested_at=datetime(2026, 9, 10, tzinfo=UTC),
    )

    assert records[0]["record_id"] == "MLB-NOTEBOOKS"
