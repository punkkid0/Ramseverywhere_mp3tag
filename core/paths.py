import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def app_root() -> Path:
    """Project root when running from source, bundle root when frozen."""
    if is_frozen():
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def bundled_config_path() -> Path:
    return app_root() / "config.yaml"


def icon_path() -> Path | None:
    for candidate in (
        app_root() / "assets" / "app_icon.ico",
        Path(__file__).resolve().parent.parent / "assets" / "app_icon.ico",
    ):
        if candidate.exists():
            return candidate
    return None