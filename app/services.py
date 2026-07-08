from pathlib import Path

from app.models import SongItem
from core.auto_tag import (
    TagJobOptions,
    collect_mp3_files,
    preview_tags,
    process_files,
)
from core.config import AppConfig
from core.report import ProcessResult
from core.tagger import resolve_cover_path


def list_mp3_items(folder: str) -> list[SongItem]:
    files = collect_mp3_files(folder=folder)
    return [SongItem(path=path) for path in files]


def build_previews(
    songs: list[SongItem],
    options: TagJobOptions,
    config: AppConfig,
) -> list[SongItem]:
    for song in songs:
        song.preview = preview_tags(song.path, options, config)
        song.status = "preview"
        song.message = f"Mode: {song.preview.mode}"
    return songs


def validate_cover(songs: list[SongItem], cover: str) -> str | None:
    if not cover.strip() or not songs:
        return None
    resolved = resolve_cover_path(songs[0].path, cover.strip())
    if not resolved:
        return (
            f"Cover image not found: {cover}\n"
            "Put it in the music folder or use a full path."
        )
    return None


def apply_to_songs(
    songs: list[SongItem],
    options: TagJobOptions,
    config: AppConfig,
    dry_run: bool = False,
    on_progress=None,
    should_cancel=None,
) -> ProcessResult:
    selected = [song for song in songs if song.selected]

    if not options.artist.strip():
        raise ValueError("Artist is required.")

    if not selected:
        raise ValueError("Select at least one song.")

    total = len(selected)
    merged = ProcessResult(dry_run=dry_run)

    for index, song in enumerate(selected):
        if should_cancel and should_cancel():
            break
        if on_progress:
            on_progress(index + 1, total, song.filename)

        file_result = process_files([song.path], options, config=config, dry_run=dry_run)
        merged.updated.extend(file_result.updated)
        merged.skipped.extend(file_result.skipped)
        merged.failed.extend(file_result.failed)
        merged.remuxed.extend(file_result.remuxed)
        merged.details.extend(file_result.details)

        if file_result.details:
            detail = file_result.details[0]
            song.status = detail.status
            song.message = detail.message
        if not dry_run and song.status in {"updated", "preview"}:
            song.preview = preview_tags(song.path, options, config)

    return merged