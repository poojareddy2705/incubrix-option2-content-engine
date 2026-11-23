"""
main.py — CLI entry point for the IncuBrix Social Media Content Engine.

Usage:
    python -m src.main --input examples/sample_input.txt
    python -m src.main --input examples/sample_input.txt --refresh
    python -m src.main --input examples/sample_input.txt --dry-run
    python -m src.main --input examples/sample_input.txt --campaign my_campaign --seed 123

Implements four assessment run scenarios:
    RUN 1 — Normal run: new input → ≥20 accepted assets
    RUN 2 — Same input repeat: duplicate prevention activates
    RUN 3 — New input refresh: new assets without duplicating old
    RUN 4 — Failure/recovery: handles missing files and bad config gracefully
"""
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

# Ensure project root is on Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import EngineConfig
from src.generator import get_provider
from src.validators import validate_all_assets
from src.dedupe import run_full_dedupe
from src.scoring import compute_quality_score
from src.utm import build_utm_link, utm_note_for_platform, utm_required_for_platform
from src.scheduler import assign_schedule
from src.exporter import export_all
from src.logger import setup_logging, save_run_summary, save_qa_summary
from src.models import ContentAsset, RunMetadata, DuplicateRecord


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="python -m src.main",
        description=(
            "IncuBrix Social Media Content Engine — "
            "generates platform-ready content from one long-form input."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main --input examples/sample_input.txt
  python -m src.main --input examples/sample_input.txt --refresh
  python -m src.main --input examples/sample_input.txt --dry-run --seed 99
  python -m src.main --input examples/new_input.txt --campaign new_launch
        """,
    )
    parser.add_argument(
        "--input", required=True,
        help="Path to long-form input file (article, transcript, etc.)"
    )
    parser.add_argument(
        "--campaign", default=None,
        help="Campaign name for UTM tracking (overrides config)"
    )
    parser.add_argument(
        "--base-url", dest="base_url", default=None,
        help="Base URL for UTM links (overrides config)"
    )
    parser.add_argument(
        "--output-dir", dest="output_dir", default=None,
        help="Output directory for run evidence (overrides config)"
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for deterministic generation (overrides config)"
    )
    parser.add_argument(
        "--config", default="config",
        help="Path to config directory (default: config)"
    )
    parser.add_argument(
        "--refresh", action="store_true",
        help="Refresh mode: load prior accepted assets and avoid re-generating duplicates"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Dry run: generate and QA assets but do not write any output files"
    )
    parser.add_argument(
        "--provider", default=None,
        choices=["mock", "openai", "anthropic", "google"],
        help="Generation provider (overrides config and env)"
    )
    return parser.parse_args(argv)


def load_input_file(input_path: Path) -> str:
    """
    Load and validate the input file.
    Raises FileNotFoundError or ValueError with clear messages.
    """
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}\n"
            f"Please check the path and try again.\n"
            f"Example: python -m src.main --input examples/sample_input.txt"
        )
    if not input_path.is_file():
        raise ValueError(f"Input path is not a file: {input_path}")

    text = input_path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(
            f"Input file is empty: {input_path}\n"
            f"The input file must contain text content to generate assets from."
        )
    if len(text) < 50:
        raise ValueError(
            f"Input file is too short ({len(text)} characters): {input_path}\n"
            f"Please provide a longer input (at least 50 characters)."
        )
    return text


def load_prior_accepted_assets(run_evidence_dir: Path) -> List[ContentAsset]:
    """
    Load previously accepted assets from run-evidence directory for refresh mode.
    Scans all prior run directories for accepted_assets.csv files.
    """
    import csv
    prior_assets = []
    if not run_evidence_dir.exists():
        return prior_assets

    for run_dir in sorted(run_evidence_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        accepted_csv = run_dir / "accepted_assets.csv"
        if not accepted_csv.exists():
            continue
        try:
            with open(accepted_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    asset = ContentAsset(
                        asset_id=row.get("asset_id", ""),
                        platform=row.get("platform", ""),
                        format=row.get("format", ""),
                        content_pillar=row.get("content_pillar", ""),
                        hook=row.get("hook", ""),
                        caption=row.get("caption", ""),
                        cta=row.get("cta", ""),
                    )
                    prior_assets.append(asset)
        except Exception as e:
            pass  # Skip unreadable files silently

    return prior_assets


def apply_quality_scores(
    assets: List[ContentAsset],
    config: EngineConfig,
) -> List[ContentAsset]:
    """Apply quality and brand scores to all assets."""
    banned_phrases = config.banned_phrases
    unsupported_patterns = config.brand_rules.get("unsupported_claim_patterns", [])

    for asset in assets:
        quality_score, brand_score, issues = compute_quality_score(
            asset, banned_phrases, unsupported_patterns
        )
        asset.quality_score = quality_score
        asset.brand_score = brand_score

    return assets


def apply_utm_links(
    assets: List[ContentAsset],
    config: EngineConfig,
) -> List[ContentAsset]:
    """Generate and assign UTM links to assets."""
    for asset in assets:
        try:
            utm = build_utm_link(
                base_url=config.base_url,
                platform=asset.platform,
                campaign=config.campaign,
                asset_id=asset.asset_id,
            )
            asset.utm_link = utm
            # For non-LinkedIn platforms, add note about UTM usage
            if not utm_required_for_platform(asset.platform):
                utm_note = utm_note_for_platform(asset.platform)
                asset.notes = (asset.notes + f" | UTM: {utm_note}").strip(" | ")
        except ValueError as e:
            asset.utm_link = ""
            asset.notes = (asset.notes + f" | UTM error: {e}").strip(" | ")

    return assets


def accept_reject_assets(
    assets: List[ContentAsset],
    config: EngineConfig,
) -> tuple[List[ContentAsset], List[ContentAsset]]:
    """
    Apply quality threshold to separate accepted from rejected assets.
    Sets status field on each asset.
    """
    accepted = []
    rejected = []

    threshold = config.quality_threshold
    brand_threshold = config.brand_threshold

    for asset in assets:
        reasons = []
        if asset.quality_score < threshold:
            reasons.append(
                f"Quality score {asset.quality_score:.1f} below threshold {threshold}"
            )
        if asset.brand_score < brand_threshold:
            reasons.append(
                f"Brand score {asset.brand_score:.1f} below threshold {brand_threshold}"
            )

        if reasons:
            asset.rejection_reason = (
                (asset.rejection_reason + " | " if asset.rejection_reason else "")
                + " | ".join(reasons)
            )
            asset.status = "Rejected"
            rejected.append(asset)
        else:
            asset.status = "Ready"
            asset.duplicate_check = "PASS"
            accepted.append(asset)

    return accepted, rejected


def build_qa_summary(
    candidates: List[ContentAsset],
    accepted: List[ContentAsset],
    rejected: List[ContentAsset],
    duplicates: List[DuplicateRecord],
    validation_issues: List,
) -> dict:
    """Build a QA summary dict for the qa_summary.json file."""
    platform_counts = {}
    pillar_counts = {}
    experiment_counts = {}

    for asset in accepted:
        platform_counts[asset.platform] = platform_counts.get(asset.platform, 0) + 1
        pillar_counts[asset.content_pillar] = pillar_counts.get(asset.content_pillar, 0) + 1
        exp = asset.experiment_id.split(":")[0] if ":" in asset.experiment_id else asset.experiment_id
        if exp:
            experiment_counts[exp] = experiment_counts.get(exp, 0) + 1

    avg_quality = (
        sum(a.quality_score for a in accepted) / len(accepted) if accepted else 0
    )
    avg_brand = (
        sum(a.brand_score for a in accepted) / len(accepted) if accepted else 0
    )

    return {
        "candidates_generated": len(candidates),
        "accepted": len(accepted),
        "rejected": len(rejected),
        "duplicates_removed": len(duplicates),
        "acceptance_rate": f"{len(accepted)/len(candidates)*100:.1f}%" if candidates else "0%",
        "average_quality_score": round(avg_quality, 2),
        "average_brand_score": round(avg_brand, 2),
        "platform_distribution": platform_counts,
        "pillar_distribution": pillar_counts,
        "experiment_distribution": experiment_counts,
        "validation_issues_total": sum(len(r.issues) for r in validation_issues),
        "claim_flags_total": sum(len(r.claim_flags) for r in validation_issues),
    }


def run_engine(argv: Optional[List[str]] = None) -> int:
    """
    Main engine run function. Returns exit code (0=success, 1=error).
    """
    start_time = time.time()

    # --- Parse arguments ---
    try:
        args = parse_args(argv)
    except SystemExit as e:
        return int(e.code) if e.code else 0

    # --- Load config ---
    try:
        cli_overrides = {}
        if args.campaign:
            cli_overrides["campaign"] = args.campaign
        if args.base_url:
            cli_overrides["base_url"] = args.base_url
        if args.output_dir:
            cli_overrides["output_dir"] = args.output_dir
        if args.seed is not None:
            cli_overrides["seed"] = args.seed
        if args.provider:
            cli_overrides["provider"] = args.provider

        config = EngineConfig(
            config_dir=Path(args.config),
            cli_overrides=cli_overrides,
        )
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}", file=sys.stderr)
        print("Check config/engine.yaml, config/brand_rules.yaml, config/platform_rules.yaml", file=sys.stderr)
        return 1

    # --- Set up run directory and logging ---
    from src.models import RunMetadata
    metadata = RunMetadata(
        input_filename=args.input,
        provider=config.provider,
        mode=config.mode,
        seed=config.seed,
        campaign=config.campaign,
    )

    run_dir = Path(config.output_dir) / metadata.run_id
    if args.dry_run:
        # Use a temp directory for dry runs but don't create actual run dir
        import tempfile
        run_dir = Path(tempfile.mkdtemp(prefix="incubrix_dryrun_"))

    logger = setup_logging(run_dir)
    logger.info("=" * 60)
    logger.info("IncuBrix Social Media Content Engine")
    logger.info(f"Run ID: {metadata.run_id}")
    logger.info(f"Mode: {config.mode} | Provider: {config.provider}")
    logger.info(f"Refresh: {args.refresh} | Dry-run: {args.dry_run}")
    logger.info("=" * 60)

    # --- Load input file ---
    try:
        input_path = Path(args.input)
        input_text = load_input_file(input_path)
        metadata.input_filename = str(input_path)
        metadata.input_char_count = len(input_text)
        metadata.input_word_count = len(input_text.split())
        logger.info(
            f"Input loaded: {input_path.name} "
            f"({metadata.input_word_count} words, {metadata.input_char_count} chars)"
        )
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Input error: {e}")
        print(f"\n[ERROR] {e}", file=sys.stderr)
        return 1

    # --- Load prior assets for refresh mode ---
    prior_assets = []
    if args.refresh:
        run_evidence_dir = Path(config.output_dir)
        prior_assets = load_prior_accepted_assets(run_evidence_dir)
        logger.info(
            f"[REFRESH] Loaded {len(prior_assets)} prior accepted assets for duplicate checking"
        )

    # --- Generate candidates ---
    try:
        provider = get_provider(config)
        logger.info(
            f"Generating {config.candidate_count} candidate assets "
            f"(provider: {type(provider).__name__})"
        )
        candidates = provider.generate(
            input_text=input_text,
            campaign=config.campaign,
            base_url=config.base_url,
            candidate_count=config.candidate_count,
        )
        metadata.candidates_generated = len(candidates)
        logger.info(f"Generated {len(candidates)} candidate assets")
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        print(f"\n[ERROR] Content generation failed: {e}", file=sys.stderr)
        metadata.errors.append(f"Generation error: {e}")
        return 1

    # --- Apply UTM links ---
    candidates = apply_utm_links(candidates, config)

    # --- Validate assets (brand/claim/completeness checks) ---
    logger.info("Running brand and claim validation...")
    validated_pass, validated_fail, validation_results = validate_all_assets(
        candidates, banned_phrases=config.banned_phrases
    )
    logger.info(
        f"Validation: {len(validated_pass)} passed, {len(validated_fail)} failed"
    )

    # --- Apply quality scores ---
    logger.info("Computing quality scores...")
    validated_pass = apply_quality_scores(validated_pass, config)

    # --- Run deduplication ---
    logger.info("Running deduplication...")
    unique_assets, duplicates = run_full_dedupe(
        candidates=validated_pass,
        threshold=config.semantic_threshold,
        existing_assets=prior_assets if args.refresh else None,
    )
    metadata.duplicates_removed = len(duplicates)
    logger.info(
        f"After dedupe: {len(unique_assets)} unique assets, {len(duplicates)} duplicates removed"
    )

    # --- Re-score after dedupe (originality score updates) ---
    unique_assets = apply_quality_scores(unique_assets, config)

    # --- Accept / reject based on quality threshold ---
    logger.info(f"Applying quality threshold (>= {config.quality_threshold})...")
    accepted, score_rejected = accept_reject_assets(unique_assets, config)
    all_rejected = validated_fail + score_rejected

    metadata.assets_accepted = len(accepted)
    metadata.assets_rejected = len(all_rejected)

    logger.info(f"Accepted: {len(accepted)} | Rejected: {len(all_rejected)}")

    if len(accepted) < config.output_count:
        logger.warning(
            f"WARNING: Only {len(accepted)} assets accepted, "
            f"target was {config.output_count}. "
            f"Consider lowering quality_threshold or increasing candidate_count."
        )

    # --- Assign schedule ---
    logger.info("Assigning publication schedule...")
    schedule_config = config.get("schedule", default={})
    start_date = schedule_config.get("start_date", "2026-12-01") if schedule_config else "2026-12-01"
    accepted = assign_schedule(accepted, start_date=start_date)

    # --- Build QA summary ---
    qa_summary = build_qa_summary(
        candidates, accepted, all_rejected, duplicates, validation_results
    )

    # --- Record runtime ---
    runtime = time.time() - start_time
    metadata.runtime_seconds = round(runtime, 2)
    metadata.estimated_cost = "not_applicable" if config.mode == "mock" else "unknown"

    # --- Export outputs ---
    if not args.dry_run:
        logger.info("Exporting outputs...")
        root_dir = Path(".")
        output_paths = export_all(
            accepted=accepted,
            rejected=all_rejected,
            duplicates=duplicates,
            output_dir=run_dir,
            root_dir=root_dir,
        )
        metadata.output_paths = output_paths

        # Save run summary and QA summary
        summary_data = metadata.__dict__.copy()
        summary_data["errors"] = metadata.errors
        save_run_summary(run_dir, summary_data)
        save_qa_summary(run_dir, qa_summary)

        logger.info("=" * 60)
        logger.info("Run complete.")
        logger.info(f"Run ID:    {metadata.run_id}")
        logger.info(f"Accepted:  {len(accepted)} assets")
        logger.info(f"Rejected:  {len(all_rejected)} assets")
        logger.info(f"Dupes:     {len(duplicates)} removed")
        logger.info(f"Runtime:   {runtime:.2f}s")
        logger.info(f"Output:    {run_dir}")
        logger.info("=" * 60)

        print("\n" + "=" * 60)
        print("IncuBrix Content Engine — Run Complete")
        print("=" * 60)
        print(f"  Run ID:         {metadata.run_id}")
        print(f"  Mode:           {config.mode} ({config.provider})")
        print(f"  Input:          {args.input}")
        print(f"  Candidates:     {metadata.candidates_generated}")
        print(f"  Accepted:       {len(accepted)} assets ✓")
        print(f"  Rejected:       {len(all_rejected)} assets")
        print(f"  Duplicates:     {len(duplicates)} removed")
        print(f"  Runtime:        {runtime:.2f}s")
        print(f"  Avg quality:    {qa_summary['average_quality_score']}")
        print(f"  Cost estimate:  {metadata.estimated_cost}")
        print(f"\n  Output directory: {run_dir}")
        print(f"  Calendar CSV:     calendar.csv (project root)")
        print(f"  Run evidence:     {config.output_dir}/")
        print("=" * 60 + "\n")

    else:
        # Dry run: print summary only
        print("\n[DRY RUN] No files written.")
        print(f"  Candidates:  {metadata.candidates_generated}")
        print(f"  Would accept: {len(accepted)}")
        print(f"  Would reject: {len(all_rejected)}")
        print(f"  Duplicates:  {len(duplicates)}")
        print(f"  Runtime:     {runtime:.2f}s")

    return 0


def main() -> None:
    """Entry point for python -m src.main"""
    sys.exit(run_engine())


if __name__ == "__main__":
    main()
