"""
models.py — Core data models for the IncuBrix Content Engine.
All fields use type hints. Dataclasses are preferred for clarity and interview-readability.
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
import uuid

# Official workbook columns (do NOT rename)
WORKBOOK_COLUMNS = [
    "asset_id", "platform", "format", "content_pillar", "hook", "caption",
    "cta", "utm_link", "final_file_url", "source_file_url", "source_input",
    "tools_used", "rights_checked", "ai_label_needed", "scheduled_date",
    "test_published_url", "impressions_or_views", "engagement_rate", "clicks",
    "status", "notes", "duplicate_check", "completeness_check"
]

CONTENT_PILLARS = [
    "Creator Pain and Workflow Friction",
    "Repurposing Education",
    "Product-in-Action",
    "Practical AI and Human Judgment",
]

PLATFORMS = ["linkedin", "instagram", "youtube_shorts"]

FUNNEL_STAGES = ["awareness", "consideration", "conversion"]

CLAIM_STATUSES = ["verified", "needs_verification", "rejected"]


# Official workbook-facing value normalization. Internal engine labels remain
# developer-friendly; exports use assessment-compatible human-readable values.
WORKBOOK_PLATFORM_VALUES = {
    "linkedin": "LinkedIn",
    "instagram": "Instagram",
    "youtube_shorts": "YouTube Shorts",
}

WORKBOOK_FORMAT_VALUES = {
    "text_post": "text post",
    "educational_post": "text post",
    "demo_post": "text post",
    "carousel": "carousel",
    "carousel_concept": "carousel",
    "graphic_concept": "graphic",
    "reel_script": "short video",
    "short_script": "short video",
    "long_video": "long video",
    "thread": "thread",
}

@dataclass
class ContentAsset:
    """Represents a single generated social media content asset."""
    # Required workbook fields
    asset_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    platform: str = ""
    format: str = ""
    content_pillar: str = ""
    hook: str = ""
    caption: str = ""
    cta: str = ""
    utm_link: str = ""
    final_file_url: str = ""
    source_file_url: str = ""
    source_input: str = ""
    tools_used: str = ""
    rights_checked: str = ""
    ai_label_needed: str = ""
    scheduled_date: str = ""
    test_published_url: str = ""
    impressions_or_views: str = ""
    engagement_rate: str = ""
    clicks: str = ""
    status: str = "Pending"
    notes: str = ""
    duplicate_check: str = ""
    completeness_check: str = ""

    # Internal QA fields
    hashtags: str = ""
    target_metric: str = ""
    claim_status: str = "needs_verification"
    quality_score: float = 0.0
    brand_score: float = 0.0
    semantic_similarity: float = 0.0
    rejection_reason: str = ""
    experiment_id: str = ""
    funnel_stage: str = ""
    scheduled_time: str = ""
    source_excerpt: str = ""

    def to_workbook_dict(self) -> dict:
        """Return the official workbook columns using workbook-compatible values."""
        row = {col: getattr(self, col, "") for col in WORKBOOK_COLUMNS}
        row["platform"] = WORKBOOK_PLATFORM_VALUES.get(self.platform, self.platform)
        row["format"] = WORKBOOK_FORMAT_VALUES.get(self.format, self.format)
        # The official workbook uses Yes/No dropdowns for these two fields.
        row["rights_checked"] = "Yes" if str(self.rights_checked).lower().startswith("yes") else "No"
        row["ai_label_needed"] = "Yes" if str(self.ai_label_needed).lower().startswith("yes") else "No"
        return row

    def to_full_dict(self) -> dict:
        """Return all fields including internal QA fields."""
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class RunMetadata:
    """Metadata recorded for each engine run."""
    run_id: str = field(default_factory=lambda: f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    input_filename: str = ""
    input_char_count: int = 0
    input_word_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    provider: str = "mock"
    mode: str = "mock"
    seed: int = 42
    campaign: str = ""
    candidates_generated: int = 0
    assets_accepted: int = 0
    assets_rejected: int = 0
    duplicates_removed: int = 0
    runtime_seconds: float = 0.0
    estimated_cost: str = "not_applicable"
    errors: List[str] = field(default_factory=list)
    output_paths: dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


@dataclass
class DuplicateRecord:
    """Record of a duplicate detection event."""
    asset_id: str = ""
    matched_asset_id: str = ""
    similarity_score: float = 0.0
    detection_method: str = ""
    action_taken: str = ""


@dataclass
class ValidationResult:
    """Result of brand/quality validation for an asset."""
    asset_id: str = ""
    passed: bool = True
    brand_score: float = 100.0
    quality_score: float = 100.0
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    claim_flags: List[str] = field(default_factory=list)
