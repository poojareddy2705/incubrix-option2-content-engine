from pathlib import Path
import csv

import pytest

from src.config_loader import EngineConfig, deep_merge
from src.dedupe import detect_exact_duplicates, detect_semantic_duplicates
from src.main import load_input_file, run_engine
from src.models import ContentAsset, WORKBOOK_COLUMNS
from src.scoring import compute_quality_score
from src.utm import build_utm_link
from src.validators import check_banned_phrases, validate_asset


def asset(**kwargs):
    base = dict(
        asset_id="LI_001",
        platform="linkedin",
        format="text_post",
        content_pillar="Repurposing Education",
        hook="Turn one long-form recording into multiple useful posts.",
        caption="A practical workflow starts with the transcript, selects distinct ideas, and adapts each one for the platform.",
        cta="See the workflow and decide which step to test next.",
        utm_link="https://example.com/?utm_source=linkedin",
        claim_status="verified",
    )
    base.update(kwargs)
    return ContentAsset(**base)


def test_deep_merge_nested():
    out = deep_merge({"a": {"b": 1, "c": 2}}, {"a": {"b": 9}})
    assert out == {"a": {"b": 9, "c": 2}}


def test_config_loads():
    cfg = EngineConfig(config_dir=Path("config"))
    assert cfg.output_count >= 20
    assert cfg.mode == "mock"


def test_utm_generation():
    url = build_utm_link("https://example.com/start", "linkedin", "creator_os_launch", "LI_001")
    assert "utm_source=linkedin" in url
    assert "utm_medium=organic_social" in url
    assert "utm_campaign=creator_os_launch" in url
    assert "utm_content=LI_001" in url


def test_exact_duplicate_detection():
    a = asset(asset_id="A")
    b = asset(asset_id="B")
    unique, dupes = detect_exact_duplicates([a, b])
    assert len(unique) == 1
    assert len(dupes) == 1
    assert dupes[0].matched_asset_id == "A"


def test_semantic_duplicate_detection():
    a = asset(asset_id="A", hook="Turn one podcast into a week of content")
    b = asset(asset_id="B", hook="Turn one podcast into a full week of content")
    unique, dupes = detect_semantic_duplicates([a, b], threshold=0.70)
    assert len(dupes) >= 1


def test_banned_phrase_validation():
    found = check_banned_phrases("This is a game-changing workflow", ["game-changing"])
    assert found == ["game-changing"]


def test_missing_hook_fails_validation():
    a = asset(hook="")
    result = validate_asset(a, banned_phrases=[])
    assert not result.passed
    assert any("hook" in issue.lower() for issue in result.issues)


def test_missing_cta_fails_validation():
    a = asset(cta="")
    result = validate_asset(a, banned_phrases=[])
    assert not result.passed
    assert any("cta" in issue.lower() for issue in result.issues)


def test_quality_score_is_bounded():
    a = asset()
    q, brand, issues = compute_quality_score(a, [], [])
    assert 0 <= q <= 100
    assert 0 <= brand <= 100


def test_workbook_export_value_normalization():
    a = asset(platform="youtube_shorts", format="short_script")
    a.rights_checked = "No"
    a.ai_label_needed = "Yes"
    row = a.to_workbook_dict()
    assert list(row.keys()) == WORKBOOK_COLUMNS
    assert row["platform"] == "YouTube Shorts"
    assert row["format"] == "short video"
    assert row["rights_checked"] == "No"
    assert row["ai_label_needed"] == "Yes"


def test_empty_input_fails(tmp_path):
    f = tmp_path / "empty.txt"
    f.write_text("")
    with pytest.raises(ValueError):
        load_input_file(f)


def test_mock_mode_deterministic(tmp_path):
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    code1 = run_engine(["--input", "examples/sample_input.txt", "--output-dir", str(out1), "--seed", "42"])
    code2 = run_engine(["--input", "examples/sample_input.txt", "--output-dir", str(out2), "--seed", "42"])
    assert code1 == 0 and code2 == 0
    csv1 = sorted(out1.glob("run_*/accepted_assets.csv"))[0]
    csv2 = sorted(out2.glob("run_*/accepted_assets.csv"))[0]
    with csv1.open(encoding="utf-8") as f1, csv2.open(encoding="utf-8") as f2:
        rows1 = list(csv.DictReader(f1))
        rows2 = list(csv.DictReader(f2))
    assert [(r["asset_id"], r["hook"]) for r in rows1] == [(r["asset_id"], r["hook"]) for r in rows2]
    assert len(rows1) >= 20
    assert list(rows1[0].keys()) == WORKBOOK_COLUMNS
