"""
dedupe.py — Duplicate detection for the IncuBrix Content Engine.

Implements three layers:
  A. Exact duplicate detection (hash comparison)
  B. Normalized text duplicate detection (lowercase, strip whitespace)
  C. Semantic near-duplicate detection via TF-IDF + cosine similarity

No paid embedding API required. scikit-learn TF-IDF is sufficient and reproducible.
"""
import hashlib
import re
import logging
from typing import List, Tuple, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import ContentAsset, DuplicateRecord

logger = logging.getLogger("content_engine.dedupe")


def _normalize_text(text: str) -> str:
    """Normalize text for comparison: lowercase, collapse whitespace, remove punctuation."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _content_fingerprint(asset: ContentAsset) -> str:
    """Create a stable fingerprint of the asset's main content."""
    combined = f"{asset.hook} {asset.caption} {asset.cta}"
    return combined.strip()


def _exact_hash(text: str) -> str:
    """SHA-256 hash of normalized text."""
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_exact_duplicates(
    candidates: List[ContentAsset],
) -> Tuple[List[ContentAsset], List[DuplicateRecord]]:
    """
    Remove exact and normalized-exact duplicates.
    Returns (deduplicated_list, duplicate_records).
    """
    seen_hashes = {}
    unique_assets = []
    duplicate_records = []

    for asset in candidates:
        fingerprint = _content_fingerprint(asset)
        h = _exact_hash(fingerprint)

        if h in seen_hashes:
            record = DuplicateRecord(
                asset_id=asset.asset_id,
                matched_asset_id=seen_hashes[h],
                similarity_score=1.0,
                detection_method="exact_hash",
                action_taken="rejected",
            )
            duplicate_records.append(record)
            logger.debug(f"Exact duplicate: {asset.asset_id} matches {seen_hashes[h]}")
        else:
            seen_hashes[h] = asset.asset_id
            unique_assets.append(asset)

    return unique_assets, duplicate_records


def detect_semantic_duplicates(
    candidates: List[ContentAsset],
    threshold: float = 0.82,
    existing_assets: Optional[List[ContentAsset]] = None,
) -> Tuple[List[ContentAsset], List[DuplicateRecord]]:
    """
    Detect semantic near-duplicates using TF-IDF cosine similarity.

    Args:
        candidates: New assets to check.
        threshold: Cosine similarity threshold above which assets are considered duplicates.
        existing_assets: Previously accepted assets (for refresh mode).

    Returns:
        (unique_assets, duplicate_records)
    """
    if len(candidates) <= 1 and not existing_assets:
        return candidates, []

    all_assets = list(existing_assets or []) + list(candidates)
    texts = [_normalize_text(_content_fingerprint(a)) for a in all_assets]

    # Need at least 2 documents for TF-IDF
    if len(texts) < 2:
        return candidates, []

    try:
        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            max_features=5000,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
    except Exception as e:
        logger.warning(f"TF-IDF vectorization failed: {e}. Skipping semantic dedupe.")
        return candidates, []

    n_existing = len(existing_assets) if existing_assets else 0
    unique_assets = []
    duplicate_records = []
    accepted_indices = set(range(n_existing))  # Existing assets are reference

    for i, asset in enumerate(candidates):
        idx = n_existing + i
        similarities = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()

        # Find max similarity to any already-accepted asset
        max_sim = 0.0
        matched_id = ""
        for j in accepted_indices:
            if similarities[j] > max_sim:
                max_sim = similarities[j]
                matched_id = all_assets[j].asset_id

        # Update asset's semantic similarity field
        asset.semantic_similarity = round(float(max_sim), 4)

        # Cross-run refresh comparison uses a slightly stricter duplicate
        # threshold than within-run QA. The same input still scores 1.0 and is
        # removed, while genuinely new source material may reuse a topic without
        # being rejected merely because the editorial template is similar.
        comparison_threshold = threshold
        if n_existing and matched_id in {a.asset_id for a in all_assets[:n_existing]}:
            comparison_threshold = max(threshold, 0.94)

        if max_sim >= comparison_threshold:
            record = DuplicateRecord(
                asset_id=asset.asset_id,
                matched_asset_id=matched_id,
                similarity_score=round(float(max_sim), 4),
                detection_method="tfidf_cosine",
                action_taken="rejected",
            )
            duplicate_records.append(record)
            logger.debug(
                f"Semantic duplicate: {asset.asset_id} sim={max_sim:.3f} matches {matched_id}"
            )
        else:
            unique_assets.append(asset)
            accepted_indices.add(idx)

    return unique_assets, duplicate_records


def run_full_dedupe(
    candidates: List[ContentAsset],
    threshold: float = 0.82,
    existing_assets: Optional[List[ContentAsset]] = None,
) -> Tuple[List[ContentAsset], List[DuplicateRecord]]:
    """
    Run all three deduplication layers in sequence.
    Returns (deduplicated_assets, all_duplicate_records).
    """
    logger.info(f"Running deduplication on {len(candidates)} candidates...")

    # Layer A+B: exact/normalized duplicates
    after_exact, exact_dupes = detect_exact_duplicates(candidates)
    logger.info(f"After exact dedupe: {len(after_exact)} remain, {len(exact_dupes)} removed")

    # Layer C: semantic near-duplicate detection
    after_semantic, semantic_dupes = detect_semantic_duplicates(
        after_exact, threshold=threshold, existing_assets=existing_assets
    )
    logger.info(
        f"After semantic dedupe: {len(after_semantic)} remain, {len(semantic_dupes)} removed"
    )

    all_dupes = exact_dupes + semantic_dupes
    return after_semantic, all_dupes
