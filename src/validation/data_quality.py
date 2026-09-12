from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class QualityCheckResult:
    name: str
    passed: bool
    details: str


def require_columns(frame: pd.DataFrame, columns: list[str], dataset: str) -> QualityCheckResult:
    missing = [column for column in columns if column not in frame.columns]
    return QualityCheckResult(
        name=f"{dataset}_required_columns",
        passed=not missing,
        details="missing=" + ",".join(missing) if missing else "all required columns present",
    )


def require_non_null(frame: pd.DataFrame, columns: list[str], dataset: str) -> QualityCheckResult:
    null_counts = frame[columns].isna().sum().to_dict() if not frame.empty else {}
    invalid = {column: count for column, count in null_counts.items() if count > 0}
    return QualityCheckResult(
        name=f"{dataset}_non_null",
        passed=not invalid,
        details=str(invalid) if invalid else "no nulls in required columns",
    )


def require_unique(frame: pd.DataFrame, column: str, dataset: str) -> QualityCheckResult:
    duplicate_count = int(frame[column].duplicated().sum()) if column in frame.columns else -1
    return QualityCheckResult(
        name=f"{dataset}_{column}_unique",
        passed=duplicate_count == 0,
        details=f"duplicate_count={duplicate_count}",
    )


def raise_on_failed_checks(checks: list[QualityCheckResult]) -> None:
    failed = [check for check in checks if not check.passed]
    if failed:
        message = "; ".join(f"{check.name}: {check.details}" for check in failed)
        raise ValueError(f"Data quality checks failed: {message}")

