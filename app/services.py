from pathlib import Path

import pandas as pd

from app.models import SongRow
from core.config import AppConfig
from core.csv_store import CSV_COLUMNS, normalize_cell, sync_csv_with_folder
from core.report import ProcessResult
from core.tagger import safe_edit_tags


def default_csv_path(folder: str) -> str:
    return str(Path(folder) / "tags.csv")


def songs_from_dataframe(df: pd.DataFrame, new_files: set[str] | None = None) -> list[SongRow]:
    new_files = new_files or set()
    songs: list[SongRow] = []

    for _, row in df.iterrows():
        filename = normalize_cell(row.get("filename", ""))
        if not filename:
            continue
        songs.append(
            SongRow(
                filename=filename,
                title=normalize_cell(row.get("title", "")),
                year=normalize_cell(row.get("year", "")),
                artist=normalize_cell(row.get("artist", "")),
                album=normalize_cell(row.get("album", "")),
                track=normalize_cell(row.get("track", "")),
                genre=normalize_cell(row.get("genre", "")),
                comment=normalize_cell(row.get("comment", "")),
                cover=normalize_cell(row.get("cover", "")),
                is_new=filename in new_files,
            )
        )
    return songs


def dataframe_from_songs(songs: list[SongRow]) -> pd.DataFrame:
    rows = []
    for song in songs:
        rows.append(
            {
                "filename": song.filename,
                "title": song.title,
                "year": song.year,
                "artist": song.artist,
                "album": song.album,
                "track": song.track,
                "genre": song.genre,
                "comment": song.comment,
                "cover": song.cover,
            }
        )
    return pd.DataFrame(rows, columns=CSV_COLUMNS)


def load_library(folder: str, csv_path: str) -> list[SongRow]:
    path = Path(csv_path)
    if not path.exists():
        return []
    df = pd.read_csv(path)
    return songs_from_dataframe(df)


def save_library(songs: list[SongRow], csv_path: str) -> None:
    dataframe_from_songs(songs).to_csv(csv_path, index=False)


def sync_library(
    folder: str, csv_path: str, config: AppConfig
) -> tuple[list[SongRow], list[str]]:
    df, new_files = sync_csv_with_folder(folder, csv_path, config=config)
    songs = songs_from_dataframe(df, new_files=set(new_files))
    return songs, new_files


def apply_songs(
    folder: str,
    songs: list[SongRow],
    indices: list[int],
    config: AppConfig,
    dry_run: bool = False,
    on_progress=None,
    should_cancel=None,
) -> ProcessResult:
    folder_path = Path(folder)
    result = ProcessResult(dry_run=dry_run)

    for position, index in enumerate(indices):
        if should_cancel and should_cancel():
            break

        song = songs[index]
        file_path = folder_path / song.filename

        if on_progress:
            on_progress(position + 1, len(indices), song.filename)

        if not file_path.exists():
            song.status = "failed"
            song.message = "File not found"
            result.failed.append(song.filename)
            result.add_detail(song.filename, "failed", song.message)
            continue

        if not song.has_tags_to_apply():
            song.status = "skipped"
            song.message = "No tags to update"
            result.skipped.append(song.filename)
            result.add_detail(song.filename, "skipped", song.message)
            continue

        outcome = safe_edit_tags(
            file_path,
            song.to_tags(),
            dry_run=dry_run,
            config=config,
        )

        if outcome.success:
            song.status = "updated"
            song.message = "Remuxed before tagging" if outcome.remuxed else "Tags applied"
            song.is_new = False
            result.updated.append(song.filename)
            if outcome.remuxed:
                result.remuxed.append(song.filename)
            result.add_detail(
                song.filename,
                "updated",
                song.message,
                remuxed=outcome.remuxed,
            )
        else:
            song.status = "failed"
            song.message = outcome.error or "Tag update failed"
            result.failed.append(song.filename)
            result.add_detail(song.filename, "failed", song.message)

    return result