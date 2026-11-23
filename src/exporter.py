"""
exporter.py — CSV export for the IncuBrix Content Engine.

Exports two files:
  1. accepted_assets.csv   — Official workbook schema (exact column names)
  2. rejected_assets.csv   — Rejected assets with rejection reason
  3. duplicate_report.csv  — Duplicate detection log
  4. calendar.csv          — Scheduler-ready version of accepted assets (same workbook schema)
  5. qa_debug.csv          — Internal QA fields (extra data for review)

IMPORTANT: The official workbook column names must not be changed.
"""
import csv
import logging
from pathlib import Path
from typing import List, Optional
from src.models import ContentAsset, DuplicateRecord, WORKBOOK_COLUMNS

logger = logging.getLogger("content_engine.exporter")

# Extra QA columns exported to qa_debug.csv only
QA_EXTRA_COLUMNS = [
    "hashtags",
    "target_metric",
    "claim_status",
    "quality_score",
    "brand_score",
    "semantic_similarity",
    "rejection_reason",
    "experiment_id",
    "funnel_stage",
    "scheduled_time",
    "source_excerpt",
]

DUPLICATE_COLUMNS = [
    "asset_id",
    "matched_asset_id",
    "similarity_score",
    "detection_method",
    "action_taken",
]


def _write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    """Write a list of dicts to a CSV file with the given field names."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
        logger.debug(f"Wrote {len(rows)} rows to {path}")
    except OSError as e:
        raise OSError(f"Failed to write CSV to {path}: {e}")


def export_accepted_assets(
    assets: List[ContentAsset],
    output_dir: Path,
) -> Path:
    """
    Export accepted assets to accepted_assets.csv using official workbook schema.
    Returns the path to the written file.
    """
    path = output_dir / "accepted_assets.csv"
    rows = [a.to_workbook_dict() for a in assets]
    _write_csv(path, rows, WORKBOOK_COLUMNS)
    logger.info(f"Exported {len(rows)} accepted assets to {path}")
    return path


def export_rejected_assets(
    assets: List[ContentAsset],
    output_dir: Path,
) -> Path:
    """Export rejected assets to rejected_assets.csv."""
    path = output_dir / "rejected_assets.csv"
    rejection_columns = WORKBOOK_COLUMNS + ["rejection_reason", "quality_score", "brand_score"]
    rows = []
    for a in assets:
        row = a.to_workbook_dict()
        row["rejection_reason"] = a.rejection_reason
        row["quality_score"] = a.quality_score
        row["brand_score"] = a.brand_score
        rows.append(row)
    _write_csv(path, rows, rejection_columns)
    logger.info(f"Exported {len(rows)} rejected assets to {path}")
    return path


def export_duplicate_report(
    duplicates: List[DuplicateRecord],
    output_dir: Path,
) -> Path:
    """Export duplicate detection log to duplicate_report.csv."""
    path = output_dir / "duplicate_report.csv"
    rows = [d.__dict__ for d in duplicates]
    _write_csv(path, rows, DUPLICATE_COLUMNS)
    logger.info(f"Exported {len(rows)} duplicate records to {path}")
    return path


def export_calendar(
    assets: List[ContentAsset],
    output_dir: Path,
    root_output_dir: Optional[Path] = None,
) -> Path:
    """
    Export calendar.csv using official workbook schema.
    Only assets with status=Ready are included.
    Calendar is written both to run dir and to project root.
    """
    ready_assets = [a for a in assets if a.status == "Ready"]
    rows = [a.to_workbook_dict() for a in ready_assets]

    # Write to run directory
    run_path = output_dir / "calendar.csv"
    _write_csv(run_path, rows, WORKBOOK_COLUMNS)

    # Write to project root (convenient for reviewer access)
    if root_output_dir:
        root_path = root_output_dir / "calendar.csv"
        _write_csv(root_path, rows, WORKBOOK_COLUMNS)
        logger.info(f"Calendar written to {root_path} (project root)")

    logger.info(f"Exported {len(rows)} Ready assets to calendar.csv")
    return run_path


def export_qa_debug(
    assets: List[ContentAsset],
    output_dir: Path,
) -> Path:
    """Export full asset data including internal QA fields to qa_debug.csv."""
    path = output_dir / "qa_debug.csv"
    all_columns = WORKBOOK_COLUMNS + QA_EXTRA_COLUMNS
    rows = []
    for a in assets:
        row = a.to_workbook_dict()
        for col in QA_EXTRA_COLUMNS:
            row[col] = getattr(a, col, "")
        rows.append(row)
    _write_csv(path, rows, all_columns)
    logger.info(f"Exported QA debug data ({len(rows)} assets) to {path}")
    return path


def export_all(
    accepted: List[ContentAsset],
    rejected: List[ContentAsset],
    duplicates: List[DuplicateRecord],
    output_dir: Path,
    root_dir: Optional[Path] = None,
) -> dict:
    """
    Run all exports. Returns a dict of output file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    try:
        paths["accepted_assets"] = str(export_accepted_assets(accepted, output_dir))
    except OSError as e:
        logger.error(f"Failed to export accepted_assets.csv: {e}")

    try:
        paths["rejected_assets"] = str(export_rejected_assets(rejected, output_dir))
    except OSError as e:
        logger.error(f"Failed to export rejected_assets.csv: {e}")

    try:
        paths["duplicate_report"] = str(export_duplicate_report(duplicates, output_dir))
    except OSError as e:
        logger.error(f"Failed to export duplicate_report.csv: {e}")

    try:
        paths["calendar"] = str(export_calendar(accepted, output_dir, root_output_dir=root_dir))
    except OSError as e:
        logger.error(f"Failed to export calendar.csv: {e}")

    all_assets = accepted + rejected
    try:
        paths["qa_debug"] = str(export_qa_debug(all_assets, output_dir))
    except OSError as e:
        logger.error(f"Failed to export qa_debug.csv: {e}")

    return paths
