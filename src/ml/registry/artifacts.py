import json
from pathlib import Path
from typing import Any

import pandas as pd


def write_ml_outputs(scores: pd.DataFrame, metadata: dict[str, Any], data_dir: Path) -> dict[str, str]:
    scores_path = data_dir / "gold" / "ml_category_scores.parquet"
    metadata_path = data_dir / "gold" / "ml_model_metadata.json"
    scores_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(scores_path, index=False)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"scores": str(scores_path), "metadata": str(metadata_path)}

