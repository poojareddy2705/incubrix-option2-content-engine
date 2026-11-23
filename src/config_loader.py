"""
config_loader.py — Loads and merges config from YAML files and environment variables.
Priority: CLI args > environment variables > config YAML > defaults.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "engine": {
        "campaign": "creator_os_launch",
        "base_url": "https://example.com",
        "output_dir": "run-evidence",
        "candidate_count": 32,
        "output_count": 20,
        "seed": 42,
        "provider": "mock",
        "mode": "mock",
    },
    "dedupe": {
        "exact_threshold": 1.0,
        "semantic_threshold": 0.82,
        "method": "tfidf_cosine",
    },
    "quality": {
        "acceptance_threshold": 75,
        "brand_score_threshold": 70,
    },
    "content_pillars": [
        "Creator Pain and Workflow Friction",
        "Repurposing Education",
        "Product-in-Action",
        "Practical AI and Human Judgment",
    ],
}


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file, returning empty dict if file doesn't exist."""
    if not path.exists():
        logger.warning(f"Config file not found: {path}")
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}")


def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class EngineConfig:
    """Unified engine configuration from YAML + env + CLI overrides."""

    def __init__(self, config_dir: Optional[Path] = None, cli_overrides: Optional[Dict] = None):
        # Load .env file
        load_dotenv()

        self.config_dir = config_dir or Path("config")
        self.cli_overrides = cli_overrides or {}

        # Load YAML configs
        engine_yaml = load_yaml(self.config_dir / "engine.yaml")
        brand_yaml = load_yaml(self.config_dir / "brand_rules.yaml")
        platform_yaml = load_yaml(self.config_dir / "platform_rules.yaml")

        # Merge engine config
        self._config = deep_merge(DEFAULT_CONFIG, engine_yaml)

        # Store brand and platform rules
        self.brand_rules = brand_yaml
        self.platform_rules = platform_yaml

        # Apply environment variable overrides
        self._apply_env_overrides()

        # Apply CLI overrides
        self._apply_cli_overrides()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides to config."""
        env_map = {
            "CONTENT_ENGINE_PROVIDER": ("engine", "provider"),
            "CONTENT_ENGINE_BASE_URL": ("engine", "base_url"),
            "CONTENT_ENGINE_CAMPAIGN": ("engine", "campaign"),
            "CONTENT_ENGINE_SEED": ("engine", "seed"),
            "CONTENT_ENGINE_MODE": ("engine", "mode"),
        }
        for env_var, (section, key) in env_map.items():
            value = os.getenv(env_var)
            if value:
                if key == "seed":
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                self._config[section][key] = value

        # Detect provider from API keys if not explicitly set
        if self._config["engine"]["provider"] == "mock":
            if os.getenv("OPENAI_API_KEY"):
                self._config["engine"]["provider"] = "openai"
                self._config["engine"]["mode"] = "live"
            elif os.getenv("ANTHROPIC_API_KEY"):
                self._config["engine"]["provider"] = "anthropic"
                self._config["engine"]["mode"] = "live"
            elif os.getenv("GOOGLE_API_KEY"):
                self._config["engine"]["provider"] = "google"
                self._config["engine"]["mode"] = "live"

    def _apply_cli_overrides(self) -> None:
        """Apply CLI argument overrides."""
        cli_map = {
            "campaign": ("engine", "campaign"),
            "base_url": ("engine", "base_url"),
            "output_dir": ("engine", "output_dir"),
            "seed": ("engine", "seed"),
            "provider": ("engine", "provider"),
        }
        for cli_key, (section, config_key) in cli_map.items():
            value = self.cli_overrides.get(cli_key)
            if value is not None:
                self._config[section][config_key] = value

    @property
    def campaign(self) -> str:
        return self._config["engine"]["campaign"]

    @property
    def base_url(self) -> str:
        return self._config["engine"]["base_url"]

    @property
    def output_dir(self) -> str:
        return self._config["engine"]["output_dir"]

    @property
    def candidate_count(self) -> int:
        return int(self._config["engine"]["candidate_count"])

    @property
    def output_count(self) -> int:
        return int(self._config["engine"]["output_count"])

    @property
    def seed(self) -> int:
        return int(self._config["engine"]["seed"])

    @property
    def provider(self) -> str:
        return self._config["engine"]["provider"]

    @property
    def mode(self) -> str:
        return self._config["engine"]["mode"]

    @property
    def semantic_threshold(self) -> float:
        return float(self._config["dedupe"]["semantic_threshold"])

    @property
    def quality_threshold(self) -> float:
        return float(self._config["quality"]["acceptance_threshold"])

    @property
    def brand_threshold(self) -> float:
        return float(self._config["quality"]["brand_score_threshold"])

    @property
    def content_pillars(self) -> list:
        return self._config["content_pillars"]

    @property
    def banned_phrases(self) -> list:
        return self.brand_rules.get("banned_phrases", [])

    @property
    def verified_capabilities(self) -> list:
        return self.brand_rules.get("verified_capabilities", [])

    def get_platform_rules(self, platform: str) -> dict:
        """Return rules for a specific platform."""
        return self.platform_rules.get("platforms", {}).get(platform, {})

    def get(self, *keys, default=None):
        """Get a nested config value by keys."""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value
