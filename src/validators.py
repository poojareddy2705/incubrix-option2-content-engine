"""
validators.py — Brand, claim, and completeness validation for the IncuBrix Content Engine.

Checks:
  - Banned hype phrases
  - Unsupported product claims
  - Missing required fields (hook, caption, CTA)
  - Platform rule compliance
  - Content pillar assignment
  - Completeness check (official workbook field)
"""
import re
import logging
from typing import List, Tuple, Optional
from src.models import ContentAsset, ValidationResult, CONTENT_PILLARS, WORKBOOK_COLUMNS

logger = logging.getLogger("content_engine.validators")

# Unsupported claim patterns that should be flagged
UNSUPPORTED_CLAIM_PATTERNS = [
    r"proven to increase",
    r"customers report",
    r"users (say|report|claim)",
    r"our data shows",
    r"studies show",
    r"clinically proven",
    r"\d+%\s+of (users|creators|customers)",
    r"saves you \d+",
    r"guaranteed (to|results)",
    r"(always|never) fails",
    r"\d+x (faster|better|more)",
]

# Platform-appropriate format map
VALID_FORMATS = {
    "linkedin": ["text_post", "carousel", "educational_post", "demo_post"],
    "instagram": ["reel_script", "carousel_concept", "graphic_concept"],
    "youtube_shorts": ["short_script"],
}

REQUIRED_CONTENT_FIELDS = ["hook", "caption", "cta", "content_pillar", "platform", "format"]

# Official workbook fields that must be present (not necessarily filled)
REQUIRED_WORKBOOK_FIELDS = WORKBOOK_COLUMNS


def check_banned_phrases(text: str, banned_phrases: List[str]) -> List[str]:
    """Return list of banned phrases found in text."""
    found = []
    text_lower = text.lower()
    for phrase in banned_phrases:
        if phrase.lower() in text_lower:
            found.append(phrase)
    return found


def check_unsupported_claims(text: str) -> List[str]:
    """Return list of unsupported claim patterns found in text."""
    found = []
    text_lower = text.lower()
    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(pattern)
    return found


def check_missing_fields(asset: ContentAsset) -> List[str]:
    """Return list of required content fields that are empty or missing."""
    missing = []
    for field in REQUIRED_CONTENT_FIELDS:
        value = getattr(asset, field, "")
        if not value or not str(value).strip():
            missing.append(field)
    return missing


def check_platform_format(asset: ContentAsset) -> List[str]:
    """Check that the asset format is valid for its platform."""
    issues = []
    valid = VALID_FORMATS.get(asset.platform, [])
    if valid and asset.format not in valid:
        issues.append(
            f"Format '{asset.format}' is not valid for platform '{asset.platform}'. "
            f"Valid formats: {valid}"
        )
    return issues


def check_content_pillar(asset: ContentAsset) -> List[str]:
    """Check that content_pillar is one of the four defined pillars."""
    issues = []
    if asset.content_pillar not in CONTENT_PILLARS:
        issues.append(
            f"content_pillar '{asset.content_pillar}' is not a recognized pillar. "
            f"Valid pillars: {CONTENT_PILLARS}"
        )
    return issues


def check_utm_requirement(asset: ContentAsset) -> List[str]:
    """Check UTM link presence for platforms where it is required."""
    issues = []
    if asset.platform == "linkedin" and not asset.utm_link:
        issues.append("LinkedIn assets require a UTM link in utm_link field.")
    return issues


def check_instagram_cta(asset: ContentAsset) -> List[str]:
    """Warn if Instagram CTA assumes a direct post link."""
    issues = []
    if asset.platform == "instagram":
        cta_lower = asset.cta.lower()
        if "click the link" in cta_lower and "below" in cta_lower:
            issues.append(
                "Instagram CTA assumes a direct post link. "
                "Use bio/profile link reference instead."
            )
    return issues


def check_youtube_duration(asset: ContentAsset) -> List[str]:
    """Warn if YouTube Shorts script seems too long."""
    issues = []
    if asset.platform == "youtube_shorts":
        # Rough heuristic: 150 words ≈ 60 seconds of speech
        caption_words = len(asset.caption.split())
        if caption_words > 180:
            issues.append(
                f"YouTube Shorts caption/script is {caption_words} words, "
                f"which may exceed 60 seconds. Target ≤150 words for the script."
            )
    return issues


def determine_completeness_check(asset: ContentAsset) -> str:
    """
    Determine the completeness_check field value.
    PASS only if all required workbook fields have values.
    """
    missing = []
    for col in REQUIRED_CONTENT_FIELDS:
        val = getattr(asset, col, "")
        if not val or not str(val).strip():
            missing.append(col)
    return "PASS" if not missing else f"FAIL: missing {', '.join(missing)}"


def determine_rights_checked(asset: ContentAsset) -> str:
    """
    Determine rights_checked value based on content type.
    - Generated copy: Yes (rights owned by user/platform)
    - Media-requiring assets: Flag for human verification
    """
    formats_needing_media = ["graphic_concept", "carousel_concept", "reel_script", "short_script"]
    if asset.format in formats_needing_media:
        # Keep the workbook field binary; detailed caveat belongs in notes.
        asset.notes = (asset.notes + " | RIGHTS: media/footage rights require human verification").strip(" | ")
        return "No"
    return "Yes"


def determine_ai_label_needed(asset: ContentAsset) -> str:
    """
    Determine if an AI label/disclosure is needed.
    Conservative approach: Yes for all AI-generated assets.
    """
    return "Yes"


def validate_asset(
    asset: ContentAsset,
    banned_phrases: Optional[List[str]] = None,
) -> ValidationResult:
    """
    Run all validation checks on a single asset.
    Returns a ValidationResult with all issues documented.
    """
    banned_phrases = banned_phrases or []
    issues = []
    warnings = []
    claim_flags = []

    # Check 1: Missing required fields
    missing = check_missing_fields(asset)
    if missing:
        issues.extend([f"Missing required field: {f}" for f in missing])

    # Check 2: Banned phrases
    combined_text = f"{asset.hook} {asset.caption} {asset.cta}"
    banned_found = check_banned_phrases(combined_text, banned_phrases)
    if banned_found:
        issues.extend([f"Banned phrase: '{p}'" for p in banned_found])

    # Check 3: Unsupported claim patterns
    claim_issues = check_unsupported_claims(combined_text)
    if claim_issues:
        claim_flags.extend(claim_issues)
        warnings.extend([f"Potential unsupported claim: '{p}'" for p in claim_issues])
        asset.claim_status = "needs_verification"

    # Check 4: Platform format validity
    format_issues = check_platform_format(asset)
    issues.extend(format_issues)

    # Check 5: Content pillar validity
    pillar_issues = check_content_pillar(asset)
    issues.extend(pillar_issues)

    # Check 6: UTM requirement
    utm_issues = check_utm_requirement(asset)
    issues.extend(utm_issues)

    # Check 7: Platform-specific CTA checks
    if asset.platform == "instagram":
        issues.extend(check_instagram_cta(asset))
    if asset.platform == "youtube_shorts":
        warnings.extend(check_youtube_duration(asset))

    # Set completeness, rights, and AI label
    asset.completeness_check = determine_completeness_check(asset)
    asset.rights_checked = determine_rights_checked(asset)
    asset.ai_label_needed = determine_ai_label_needed(asset)

    passed = len(issues) == 0

    return ValidationResult(
        asset_id=asset.asset_id,
        passed=passed,
        issues=issues,
        warnings=warnings,
        claim_flags=claim_flags,
    )


def validate_all_assets(
    assets: List[ContentAsset],
    banned_phrases: Optional[List[str]] = None,
) -> Tuple[List[ContentAsset], List[ContentAsset], List[ValidationResult]]:
    """
    Validate all assets. Returns (passed, failed, all_results).
    Assets that fail validation have rejection_reason set.
    """
    passed = []
    failed = []
    results = []

    for asset in assets:
        result = validate_asset(asset, banned_phrases)
        results.append(result)

        if result.passed:
            passed.append(asset)
        else:
            asset.rejection_reason = " | ".join(result.issues)
            asset.status = "Rejected"
            failed.append(asset)
            logger.debug(f"Asset {asset.asset_id} failed validation: {result.issues}")

    logger.info(
        f"Validation complete: {len(passed)} passed, {len(failed)} failed"
    )
    return passed, failed, results
