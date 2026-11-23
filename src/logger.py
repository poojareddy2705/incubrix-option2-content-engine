"""
logger.py — Structured logging for the IncuBrix Content Engine.
Writes both human-readable logs and structured JSON run metadata.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(run_dir: Path, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging to both console and file.
    Returns the root logger for the engine.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "run.log"
    error_path = run_dir / "error.log"

    # Root logger
    logger = logging.getLogger("content_engine")
    logger.setLevel(level)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (all levels)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Error-only file handler
    error_handler = logging.FileHandler(error_path, encoding="utf-8")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    return logger


def save_run_summary(run_dir: Path, metadata: dict) -> Path:
    """Save run metadata as a JSON summary file."""
    path = run_dir / "run_summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    return path


def save_qa_summary(run_dir: Path, qa_data: dict) -> Path:
    """Save QA summary as a JSON file."""
    path = run_dir / "qa_summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(qa_data, f, indent=2, default=str)
    return path
