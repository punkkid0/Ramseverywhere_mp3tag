from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.cleaners import DEFAULT_SITE_NAMES, build_site_patterns
from core.paths import app_root, bundled_config_path, is_frozen

DEFAULT_CONFIG_NAME = "config.yaml"
# Empty by default — users set any comment via CLI --comment, GUI, or config.yaml
DEFAULT_COMMENT = ""


@dataclass
class AppConfig:
    site_names: list[str] = field(default_factory=lambda: list(DEFAULT_SITE_NAMES))
    watermark_patterns: list[str] = field(default_factory=list)
    ffmpeg_path: str = "ffmpeg"
    ffmpeg_timeout: int = 60
    backup_suffix: str = ".bak"
    default_comment: str = DEFAULT_COMMENT
    cover_size: int = 1000
    cover_quality: int = 90
    defaults: dict[str, str] = field(default_factory=lambda: {"genre": "", "comment": ""})

    def __post_init__(self) -> None:
        if not self.watermark_patterns:
            self.watermark_patterns = build_site_patterns(self.site_names)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        ffmpeg = data.get("ffmpeg", {})
        backup = data.get("backup", {})
        defaults = data.get("defaults", {})
        site_names = data.get("site_names")
        patterns = data.get("watermark_patterns")
        tags = data.get("tags", {})
        cover = data.get("cover", {})

        # Prefer tags.comment, then defaults.comment; empty string is allowed (user chooses).
        raw_comment = tags.get("comment", defaults.get("comment", DEFAULT_COMMENT))
        if raw_comment is None:
            raw_comment = DEFAULT_COMMENT
        user_comment = str(raw_comment)

        config = cls(
            site_names=list(site_names) if site_names else list(DEFAULT_SITE_NAMES),
            watermark_patterns=list(patterns) if patterns else [],
            ffmpeg_path=str(ffmpeg.get("path", "ffmpeg")),
            ffmpeg_timeout=int(ffmpeg.get("timeout_seconds", 60)),
            backup_suffix=str(backup.get("suffix", ".bak")),
            default_comment=user_comment,
            cover_size=int(cover.get("size", 1000)),
            cover_quality=int(cover.get("quality", 90)),
            defaults={
                "genre": str(defaults.get("genre", "")),
                "comment": user_comment,
            },
        )
        if not config.watermark_patterns:
            config.watermark_patterns = build_site_patterns(config.site_names)
        return config

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> "AppConfig":
        if config_path is not None:
            path = Path(config_path)
            if not path.exists():
                return cls()
            return cls.from_dict(_read_yaml(path))

        search_roots = [Path.cwd(), _package_root()]
        if is_frozen():
            search_roots.insert(0, app_root())

        seen: set[Path] = set()
        for root in search_roots:
            root = root.resolve()
            if root in seen:
                continue
            seen.add(root)
            candidate = root / DEFAULT_CONFIG_NAME
            if candidate.exists():
                return cls.from_dict(_read_yaml(candidate))

        bundled = bundled_config_path()
        if bundled.exists():
            return cls.from_dict(_read_yaml(bundled))

        return cls()


def _package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}