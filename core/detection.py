import re
from pathlib import Path

_SINGLE_MARKER = re.compile(r"\(single\)", re.IGNORECASE)


def is_single_album_name(album: str) -> bool:
    return bool(album and _SINGLE_MARKER.search(album))


def detect_mode(
    existing_album: str,
    mode_override: str = "auto",
) -> str:
    """
    Decide whether a track is a single or part of an album.

    Trusts existing album tags unless the worker overrides mode.
    """
    override = mode_override.strip().lower()
    if override in {"single", "album"}:
        return override

    album = existing_album.strip()
    if not album or is_single_album_name(album):
        return "single"
    return "album"


def parse_track_from_filename(filename: str) -> str:
    """Read a track number from common filename patterns."""
    stem = Path(filename).stem

    match = re.match(r"^(\d{1,2})[\s._\-]+", stem)
    if match:
        return str(int(match.group(1)))

    match = re.search(r"(?:track|trk)[\s._\-]*(\d{1,2})", stem, re.IGNORECASE)
    if match:
        return str(int(match.group(1)))

    return ""


def resolve_track(
    mode: str,
    existing_track: str,
    filename: str,
    manual_track: str = "",
) -> str:
    """Resolve the final track number."""
    if manual_track.strip():
        return manual_track.strip()

    if mode == "single":
        return "1"

    if existing_track.strip():
        track = existing_track.strip()
        if "/" in track:
            track = track.split("/", 1)[0].strip()
        return track

    return parse_track_from_filename(filename)


def single_album_name(clean_title: str) -> str:
    """Album field for a single release."""
    return f"{clean_title} (single)"