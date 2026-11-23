"""
scheduler.py — Schedule distribution for the IncuBrix Content Engine.

Distributes accepted assets across a weekly calendar:
  LinkedIn:       3 posts/week — Monday, Wednesday, Friday @ 09:00
  Instagram:      3 posts/week — Tuesday, Thursday, Saturday @ 11:00
  YouTube Shorts: 2 posts/week — Wednesday, Sunday @ 14:00

Generates a week-by-week schedule starting from a configured start date.
No two assets on the same platform are assigned the same date+time.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from src.models import ContentAsset

logger = logging.getLogger("content_engine.scheduler")

# Weekly schedule: platform -> list of (weekday_name, time_str)
# weekday: 0=Monday, 1=Tuesday, ..., 6=Sunday
PLATFORM_SCHEDULE = {
    "linkedin": [
        (0, "09:00"),  # Monday
        (2, "09:00"),  # Wednesday
        (4, "09:00"),  # Friday
    ],
    "instagram": [
        (1, "11:00"),  # Tuesday
        (3, "11:00"),  # Thursday
        (5, "11:00"),  # Saturday
    ],
    "youtube_shorts": [
        (2, "14:00"),  # Wednesday
        (6, "14:00"),  # Sunday
    ],
}

WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _next_weekday(start_date: datetime, target_weekday: int) -> datetime:
    """Return the next occurrence of target_weekday (0=Mon) from start_date (inclusive)."""
    days_ahead = target_weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def build_schedule_slots(
    start_date: datetime,
    num_weeks: int = 4,
) -> Dict[str, List[str]]:
    """
    Build available schedule slots per platform for num_weeks.
    Returns dict: platform -> [sorted list of datetime strings]
    """
    slots: Dict[str, List[str]] = {platform: [] for platform in PLATFORM_SCHEDULE}

    for platform, schedule in PLATFORM_SCHEDULE.items():
        for week in range(num_weeks):
            week_start = start_date + timedelta(weeks=week)
            for weekday, time_str in schedule:
                slot_date = _next_weekday(week_start, weekday)
                # Avoid adding same slot twice (can happen when week_start is mid-week)
                slot_str = f"{slot_date.strftime('%Y-%m-%d')} {time_str}"
                if slot_str not in slots[platform]:
                    slots[platform].append(slot_str)

        slots[platform].sort()

    return slots


def assign_schedule(
    assets: List[ContentAsset],
    start_date: str = "2026-12-01",
    num_weeks: int = 4,
) -> List[ContentAsset]:
    """
    Assign scheduled_date and scheduled_time to accepted assets.
    Assets are distributed across available slots for their platform.
    Returns assets with scheduled_date populated.
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        logger.warning(f"Invalid start_date '{start_date}', using 2026-12-01")
        start_dt = datetime(2026, 12, 1)

    # Expand the schedule horizon when accepted output exceeds the nominal
    # four-week capacity for any platform. This prevents Ready assets from
    # being exported without a date while preserving the configured cadence.
    from math import ceil
    counts = {}
    for asset in assets:
        counts[asset.platform] = counts.get(asset.platform, 0) + 1
    required_weeks = num_weeks
    for platform, count in counts.items():
        weekly_slots = len(PLATFORM_SCHEDULE.get(platform, []))
        if weekly_slots:
            required_weeks = max(required_weeks, ceil(count / weekly_slots))

    slots = build_schedule_slots(start_dt, num_weeks=required_weeks)
    slot_indices = {platform: 0 for platform in PLATFORM_SCHEDULE}

    for asset in assets:
        platform = asset.platform
        platform_slots = slots.get(platform, [])
        idx = slot_indices.get(platform, 0)

        if idx < len(platform_slots):
            slot_str = platform_slots[idx]
            parts = slot_str.split(" ")
            asset.scheduled_date = parts[0]
            asset.scheduled_time = parts[1] if len(parts) > 1 else "09:00"
            slot_indices[platform] = idx + 1
        else:
            logger.warning(
                f"No more schedule slots for platform '{platform}' — "
                f"asset {asset.asset_id} will not have a scheduled date."
            )
            asset.scheduled_date = ""
            asset.scheduled_time = ""

    logger.info(f"Schedule assigned to {len(assets)} assets")
    return assets
