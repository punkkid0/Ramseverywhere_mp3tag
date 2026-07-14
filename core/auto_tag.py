from dataclasses import dataclass, field
from pathlib import Path

from core.cleaners import clean_title
from core.config import AppConfig
from core.detection import (
    detect_mode,
    resolve_track,
    single_album_name,
)
from core.formatters import format_artist
from core.report import FileReport, ProcessResult
from core.tagger import read_tags_from_file, safe_edit_tags


@dataclass
class TagJobOptions:
    """Worker inputs for one batch or a single file."""

    artist: str = ""
    genre: str = ""
    year: str = ""
    album: str = ""
    track: str = ""
    mode: str = "auto"
    cover: str = ""
    comment: str = ""


@dataclass
class TagPreview:
    filename: str
    before: dict[str, str]
    after: dict[str, str]
    mode: str


def build_auto_tags(
    file_path: Path,
    existing: dict[str, str],
    options: TagJobOptions,
    config: AppConfig,
) -> dict[str, str]:
    """Compute final tags for one MP3 using worker rules."""
    raw_title = existing.get("title", "").strip() or file_path.stem
    clean = clean_title(
        raw_title,
        patterns=config.watermark_patterns,
        site_names=config.site_names,
    )

    artist_source = options.artist.strip() or existing.get("artist", "").strip()
    artist = format_artist(artist_source) if artist_source else ""

    year = options.year.strip() or existing.get("year", "").strip()

    mode = detect_mode(existing.get("album", ""), options.mode)

    if mode == "single":
        album = single_album_name(clean)
        album_artist = ""
    else:
        album = options.album.strip() or existing.get("album", "").strip()
        album_artist = artist

    track = resolve_track(
        mode,
        existing.get("track", ""),
        file_path.name,
        options.track,
    )

    genre = options.genre.strip() or existing.get("genre", "").strip()
    # Priority: CLI/GUI --comment → config.yaml tags.comment → keep file's existing comment
    # Empty at every level is fine — user decides the text (or no comment at all).
    comment = (
        options.comment.strip()
        or (config.default_comment or "").strip()
        or config.defaults.get("comment", "").strip()
        or existing.get("comment", "").strip()
    )

    tags = {
        "title": clean,
        "artist": artist,
        "year": year,
        "album": album,
        "track": track,
        "genre": genre,
        "comment": comment,
        "album_artist": album_artist,
    }

    if options.cover.strip():
        tags["cover"] = options.cover.strip()

    return tags


def preview_tags(
    file_path: Path,
    options: TagJobOptions,
    config: AppConfig | None = None,
) -> TagPreview:
    active_config = config or AppConfig()
    existing = read_tags_from_file(file_path)
    existing["has_cover"] = "yes" if _file_has_cover(file_path) else "no"
    after = build_auto_tags(file_path, existing, options, active_config)
    mode = detect_mode(existing.get("album", ""), options.mode)
    return TagPreview(
        filename=file_path.name,
        before=existing,
        after=after,
        mode=mode,
    )


def _file_has_cover(file_path: Path) -> bool:
    try:
        from mutagen.id3 import ID3

        tags = ID3(str(file_path))
        return any(key.startswith("APIC") for key in tags.keys())
    except Exception:
        return False


def process_files(
    files: list[Path],
    options: TagJobOptions,
    config: AppConfig | None = None,
    dry_run: bool = False,
) -> ProcessResult:
    active_config = config or AppConfig()
    result = ProcessResult(dry_run=dry_run)

    for file_path in files:
        if file_path.suffix.lower() != ".mp3":
            result.skipped.append(file_path.name)
            result.add_detail(file_path.name, "skipped", "Not an MP3 file")
            continue

        if not file_path.exists():
            result.failed.append(file_path.name)
            result.add_detail(file_path.name, "failed", "File not found")
            continue

        existing = read_tags_from_file(file_path)
        tags = build_auto_tags(file_path, existing, options, active_config)

        if not tags.get("artist", "").strip():
            result.skipped.append(file_path.name)
            result.add_detail(
                file_path.name,
                "skipped",
                "No artist on file — add a tag to the MP3 or pass --artist",
            )
            continue

        if dry_run:
            result.updated.append(file_path.name)
            result.add_detail(file_path.name, "preview", f"Mode: {detect_mode(existing.get('album', ''), options.mode)}")
            continue

        outcome = safe_edit_tags(
            file_path,
            tags,
            dry_run=False,
            config=active_config,
            preserve_cover=not bool(options.cover.strip()),
        )

        if outcome.success:
            result.updated.append(file_path.name)
            if outcome.remuxed:
                result.remuxed.append(file_path.name)
            result.add_detail(
                file_path.name,
                "updated",
                "Remuxed before tagging" if outcome.remuxed else "Tags applied",
                remuxed=outcome.remuxed,
            )
        else:
            result.failed.append(file_path.name)
            result.add_detail(file_path.name, "failed", outcome.error or "Tag update failed")

    return result


def collect_mp3_files(
    folder: str | None = None,
    file_path: str | None = None,
) -> list[Path]:
    """Collect MP3 paths from a folder or a single file.

    If --file points to a folder, all MP3s inside are included automatically.
    """
    if file_path:
        path = Path(file_path)
        if path.is_dir():
            return _mp3s_in_folder(path)
        if path.suffix.lower() == ".mp3":
            return [path]
        raise ValueError(
            f"--file must be an .mp3 file or a folder. Got: {file_path}"
        )

    if not folder:
        return []

    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise ValueError(f"--folder not found: {folder}")

    return _mp3s_in_folder(folder_path)


def _mp3s_in_folder(folder_path: Path) -> list[Path]:
    return sorted(
        path
        for path in folder_path.iterdir()
        if path.is_file() and path.suffix.lower() == ".mp3"
    )