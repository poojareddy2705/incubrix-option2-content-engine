"""
utm.py — UTM tracking link generator for the IncuBrix Content Engine.

UTM structure:
  utm_source=<platform>
  utm_medium=organic_social
  utm_campaign=<campaign_name>
  utm_content=<asset_id>

LinkedIn requires UTM. Instagram and YouTube Shorts do not assume clickable post links.
"""
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs, urljoin
from typing import Optional


PLATFORM_UTM_SOURCE = {
    "linkedin": "linkedin",
    "instagram": "instagram",
    "youtube_shorts": "youtube",
}

# Platforms where a UTM link in the post is meaningful
UTM_REQUIRED_PLATFORMS = {"linkedin"}

# Platforms where UTM links are optional/not in-post
UTM_OPTIONAL_PLATFORMS = {"instagram", "youtube_shorts"}


def build_utm_link(
    base_url: str,
    platform: str,
    campaign: str,
    asset_id: str,
    medium: str = "organic_social",
) -> str:
    """
    Build a UTM-tagged URL.

    Args:
        base_url: The landing page URL (from config, never hardcoded production URL).
        platform: Content platform (linkedin, instagram, youtube_shorts).
        campaign: Campaign slug (e.g. 'creator_os_launch').
        asset_id: Unique asset identifier.
        medium: UTM medium (default: organic_social).

    Returns:
        Full URL with UTM parameters appended.

    Raises:
        ValueError: If base_url is empty or invalid.
    """
    if not base_url or not base_url.strip():
        raise ValueError("base_url must not be empty. Set it in config/engine.yaml or --base-url.")

    parsed = urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"base_url '{base_url}' is not a valid URL. Must include scheme and domain.")

    utm_source = PLATFORM_UTM_SOURCE.get(platform, platform)

    params = {
        "utm_source": utm_source,
        "utm_medium": medium,
        "utm_campaign": campaign,
        "utm_content": asset_id,
    }

    # Preserve existing query params if any
    existing_params = parse_qs(parsed.query)
    merged = {k: v[0] for k, v in existing_params.items()}
    merged.update(params)

    new_query = urlencode(merged)
    new_url = urlunparse(parsed._replace(query=new_query))
    return new_url


def utm_required_for_platform(platform: str) -> bool:
    """Return True if UTM is required for this platform's posts."""
    return platform in UTM_REQUIRED_PLATFORMS


def utm_note_for_platform(platform: str) -> str:
    """Return a human-readable note about UTM usage for the platform."""
    notes = {
        "linkedin": "UTM link included in post CTA.",
        "instagram": "UTM link tracked via bio/link-in-bio. Not embedded in post.",
        "youtube_shorts": "UTM link tracked via description. Click-through not assumed.",
    }
    return notes.get(platform, "UTM link generated for tracking purposes.")
