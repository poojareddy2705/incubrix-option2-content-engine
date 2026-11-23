"""
scoring.py — Quality scoring engine for the IncuBrix Content Engine.

Scoring dimensions (total 100 points):
  - Hook quality       : 20 pts — Is the hook strong, specific, non-generic?
  - Platform fit       : 15 pts — Does the asset match platform format/style?
  - Usefulness         : 15 pts — Does it provide genuine insight or value?
  - Specificity        : 10 pts — Is it concrete, not vague?
  - Brand voice        : 15 pts — Does it match tone, avoid banned phrases?
  - CTA fit            : 10 pts — Is the CTA logical and platform-appropriate?
  - Claim safety       : 10 pts — Does it avoid unsupported claims?
  - Originality        :  3 pts — Is it not a duplicate of existing content?
  - Completeness       :  2 pts — Are all required fields filled?

Threshold: quality_score >= 75 to be accepted.
"""
import re
from typing import List, Optional
from src.models import ContentAsset


# Weak/generic hook indicators
GENERIC_HOOK_PATTERNS = [
    r"^are you (struggling|tired|fed up)",
    r"^have you ever wondered",
    r"^this post is about",
    r"^today (i want to|we will|i will)",
    r"^let me tell you",
    r"^hey everyone",
    r"^hi there",
    r"^introduction to",
    r"^welcome to",
    r"^in this post",
    r"^in this video",
    r"^ever wondered",
]

# Strong hook indicators
STRONG_HOOK_PATTERNS = [
    r"\?$",                      # Question hook
    r"^\d+",                     # Number-led hook
    r"^if you",                  # Conditional hook
    r"^most (creators|people|podcasters)",  # Contrast hook
    r"^the (problem|reason|truth|mistake)",  # Problem hook
    r"^stop ",                   # Imperative hook
    r"^what (nobody|no one)",    # Exclusive insight hook
    r"^your ",                   # Direct address
    r"^here'?s (what|why|how)",  # Reveal hook
]

# Platform format expectations
PLATFORM_FORMAT_RULES = {
    "linkedin": {
        "formats": ["text_post", "carousel", "educational_post", "demo_post"],
        "max_caption_chars": 3000,
        "min_caption_chars": 100,
    },
    "instagram": {
        "formats": ["reel_script", "carousel_concept", "graphic_concept"],
        "max_caption_chars": 2200,
        "min_caption_chars": 30,
    },
    "youtube_shorts": {
        "formats": ["short_script"],
        "max_caption_chars": 5000,
        "min_caption_chars": 50,
        "max_duration_note": "60 seconds",
    },
}


def score_hook(hook: str) -> float:
    """
    Score hook quality out of 20.
    Checks for: presence, length, strength indicators, avoidance of generic patterns.
    """
    if not hook or not hook.strip():
        return 0.0

    score = 10.0  # Base score for having a hook
    hook_lower = hook.lower().strip()

    # Penalize generic patterns
    for pattern in GENERIC_HOOK_PATTERNS:
        if re.search(pattern, hook_lower):
            score -= 4.0
            break

    # Reward strong patterns
    for pattern in STRONG_HOOK_PATTERNS:
        if re.search(pattern, hook_lower):
            score += 5.0
            break

    # Reward specificity (numbers, named concepts)
    if re.search(r"\d+", hook):
        score += 2.0

    # Penalize very long hooks (>20 words is too long for a hook)
    word_count = len(hook.split())
    if word_count > 20:
        score -= 2.0
    elif 5 <= word_count <= 15:
        score += 3.0

    return max(0.0, min(20.0, score))


def score_platform_fit(asset: ContentAsset) -> float:
    """Score platform fit out of 15."""
    platform_rules = PLATFORM_FORMAT_RULES.get(asset.platform, {})
    if not platform_rules:
        return 5.0  # Unknown platform, partial credit

    score = 15.0
    supported_formats = platform_rules.get("formats", [])

    # Check format is valid for platform
    if asset.format and asset.format not in supported_formats:
        score -= 8.0

    # Check caption length
    caption_len = len(asset.caption)
    max_chars = platform_rules.get("max_caption_chars", 5000)
    min_chars = platform_rules.get("min_caption_chars", 0)

    if caption_len > max_chars:
        score -= 5.0
    elif caption_len < min_chars:
        score -= 3.0

    # YouTube Shorts: check for 60-second mention or short script style
    if asset.platform == "youtube_shorts":
        if "60" not in asset.notes and "seconds" not in asset.caption.lower():
            score -= 2.0

    return max(0.0, min(15.0, score))


def score_usefulness(caption: str) -> float:
    """Score usefulness/insight out of 15."""
    if not caption or not caption.strip():
        return 0.0

    score = 7.0  # Base

    # Reward educational patterns
    educational_patterns = [
        r"how to", r"why ", r"what (most|many)", r"the reason",
        r"tip:", r"step \d", r"here'?s (how|what|why)", r"lesson",
        r"mistake", r"workflow", r"process", r"strategy",
    ]
    for pattern in educational_patterns:
        if re.search(pattern, caption.lower()):
            score += 2.0
            break

    # Reward specificity (concrete examples)
    if re.search(r"\d+", caption):
        score += 2.0

    # Reward adequate length
    words = len(caption.split())
    if words >= 50:
        score += 4.0
    elif words >= 25:
        score += 2.0

    return max(0.0, min(15.0, score))


def score_specificity(hook: str, caption: str) -> float:
    """Score specificity out of 10."""
    combined = f"{hook} {caption}".lower()
    score = 5.0

    # Reward concrete references
    concrete_patterns = [
        r"\d+", r"transcript", r"clip", r"reel", r"carousel",
        r"workflow", r"edit", r"hook", r"caption", r"platform",
        r"linkedin", r"instagram", r"youtube", r"podcast",
        r"audio", r"video", r"publish", r"schedule",
    ]
    hits = sum(1 for p in concrete_patterns if re.search(p, combined))
    score += min(5.0, hits * 1.0)

    return max(0.0, min(10.0, score))


def score_brand_voice(
    caption: str,
    hook: str,
    banned_phrases: List[str],
    unsupported_patterns: Optional[List[str]] = None,
) -> tuple[float, List[str]]:
    """
    Score brand voice compliance out of 15.
    Returns (score, list_of_issues).
    """
    issues = []
    score = 15.0
    combined = f"{hook} {caption}".lower()

    for phrase in banned_phrases:
        if phrase.lower() in combined:
            issues.append(f"Banned phrase detected: '{phrase}'")
            score -= 5.0

    if unsupported_patterns:
        for pattern in unsupported_patterns:
            if re.search(pattern.lower(), combined):
                issues.append(f"Potential unsupported claim pattern: '{pattern}'")
                score -= 3.0

    return max(0.0, min(15.0, score)), issues


def score_cta(cta: str, platform: str) -> float:
    """Score CTA quality and platform fit out of 10."""
    if not cta or not cta.strip():
        return 0.0

    score = 5.0  # Base for having a CTA

    cta_lower = cta.lower()

    # Platform-appropriate CTA checks
    if platform == "linkedin":
        if any(w in cta_lower for w in ["link", "comment", "share", "dm", "follow"]):
            score += 3.0
        if any(w in cta_lower for w in ["utm", "http", "/"]):  # Has a link reference
            score += 2.0

    elif platform == "instagram":
        if any(w in cta_lower for w in ["bio", "profile", "save", "share", "comment", "follow"]):
            score += 3.0
        # Penalize if assumes direct post link
        if "click the link" in cta_lower and "below" in cta_lower:
            score -= 2.0

    elif platform == "youtube_shorts":
        if any(w in cta_lower for w in ["subscribe", "like", "comment", "follow", "watch"]):
            score += 3.0

    return max(0.0, min(10.0, score))


def score_claim_safety(claim_status: str) -> float:
    """Score claim safety out of 10."""
    return {
        "verified": 10.0,
        "needs_verification": 5.0,
        "rejected": 0.0,
    }.get(claim_status, 5.0)


def score_originality(semantic_similarity: float) -> float:
    """Score originality out of 3 based on semantic similarity to existing assets."""
    if semantic_similarity >= 0.95:
        return 0.0
    elif semantic_similarity >= 0.82:
        return 1.0
    elif semantic_similarity >= 0.60:
        return 2.0
    else:
        return 3.0


def score_completeness(asset: ContentAsset) -> float:
    """Score completeness out of 2."""
    required = ["hook", "caption", "cta", "content_pillar", "platform", "format"]
    missing = [f for f in required if not getattr(asset, f, "").strip()]
    return 2.0 if not missing else 0.0


def compute_quality_score(
    asset: ContentAsset,
    banned_phrases: Optional[List[str]] = None,
    unsupported_patterns: Optional[List[str]] = None,
) -> tuple[float, float, List[str]]:
    """
    Compute overall quality score and brand score for an asset.

    Returns:
        (quality_score, brand_score, list_of_issues)
    """
    banned_phrases = banned_phrases or []
    unsupported_patterns = unsupported_patterns or []

    hook_score = score_hook(asset.hook)
    platform_score = score_platform_fit(asset)
    useful_score = score_usefulness(asset.caption)
    specific_score = score_specificity(asset.hook, asset.caption)
    brand_score_raw, brand_issues = score_brand_voice(
        asset.caption, asset.hook, banned_phrases, unsupported_patterns
    )
    cta_score = score_cta(asset.cta, asset.platform)
    claim_score = score_claim_safety(asset.claim_status)
    orig_score = score_originality(asset.semantic_similarity)
    complete_score = score_completeness(asset)

    quality_score = (
        hook_score + platform_score + useful_score + specific_score +
        brand_score_raw + cta_score + claim_score + orig_score + complete_score
    )

    # Brand score is a 0-100 normalized version of brand compliance
    brand_score = (brand_score_raw / 15.0) * 100.0

    return round(quality_score, 2), round(brand_score, 2), brand_issues
