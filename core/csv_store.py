import logging
import os
from pathlib import Path

import pandas as pd

from core.config import AppConfig
from core.exceptions import CsvError
from core.report import ProcessResult
from core.tagger import read_tags_from_file, safe_edit_tags

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    "filename",
    "title",
    "year",
    "artist",
    "album",
    "track",
    "genre",
    "comment",
    "cover",
]

TAG_FIELDS = ["artist", "album", "track", "genre", "comment", "cover"]
PREFILL_FIELDS = ["title", "year", "artist", "album", "track", "genre", "comment"]


def normalize_cell(value) -> str:
    """Convert a CSV cell to a clean string, treating NaN and 'nan' as empty."""
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def _read_or_create_csv(csv_file: str) -> pd.DataFrame:
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        if "filename" not in df.columns:
            raise CsvError("CSV missing required 'filename' column.")
        for column in CSV_COLUMNS:
            if column not in df.columns:
                df[column] = ""
        return df

    return pd.DataFrame(columns=CSV_COLUMNS)


def _prefill_row(folder_path: Path, filename: str, config: AppConfig) -> dict[str, str]:
    """Build a CSV row from existing MP3 metadata and config defaults."""
    row = {column: "" for column in CSV_COLUMNS}
    row["filename"] = filename

    existing = read_tags_from_file(folder_path / filename)
    for field in PREFILL_FIELDS:
        row[field] = existing.get(field, "")

    if not row["genre"] and config.defaults.get("genre"):
        row["genre"] = config.defaults["genre"]
    if not row["comment"] and config.defaults.get("comment"):
        row["comment"] = config.defaults["comment"]

    return row


def sync_csv_with_folder(
    folder: str,
    csv_file: str,
    config: AppConfig | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """Ensure all MP3 files in a folder are listed in the CSV."""
    active_config = config or AppConfig()
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise CsvError(f"Folder not found: {folder}")

    music_files = sorted(
        f.name for f in folder_path.iterdir() if f.suffix.lower() == ".mp3"
    )
    df = _read_or_create_csv(csv_file)
    existing_rows = df["filename"].astype(str).tolist()
    new_files = [name for name in music_files if name not in existing_rows]

    if not new_files:
        logger.info("CSV already up to date — no new files found.")
        return df, []

    new_entries = pd.DataFrame(
        [_prefill_row(folder_path, filename, active_config) for filename in new_files]
    )
    df = pd.concat([df, new_entries], ignore_index=True)
    df.to_csv(csv_file, index=False)
    logger.info("Added %d new file(s) to %s", len(new_files), csv_file)
    return df, new_files


def row_to_tags(row) -> dict[str, str]:
    """Extract writable tag fields from a CSV row."""
    return {field: normalize_cell(row.get(field, "")) for field in TAG_FIELDS}


def process_csv(
    folder: str,
    csv_file: str,
    dry_run: bool = False,
    config: AppConfig | None = None,
) -> ProcessResult:
    """Read a CSV and apply tags to each listed MP3 file."""
    active_config = config or AppConfig()
    folder_path = Path(folder)
    df = pd.read_csv(csv_file)
    result = ProcessResult(dry_run=dry_run)

    if "filename" not in df.columns:
        raise CsvError("CSV missing required 'filename' column.")

    for _, row in df.iterrows():
        filename = normalize_cell(row.get("filename", ""))
        if not filename:
            result.skipped.append("(empty filename)")
            result.add_detail("(empty filename)", "skipped", "Missing filename")
            continue

        file_path = folder_path / filename
        if not file_path.exists():
            logger.warning("File not found: %s", filename)
            result.failed.append(filename)
            result.add_detail(filename, "failed", "File not found")
            continue

        tags = row_to_tags(row)
        if not any(tags.values()):
            logger.info("Skipping %s (no tags to update)", filename)
            result.skipped.append(filename)
            result.add_detail(filename, "skipped", "No tags to update")
            continue

        outcome = safe_edit_tags(
            file_path,
            tags,
            dry_run=dry_run,
            config=active_config,
        )
        if outcome.success:
            result.updated.append(filename)
            if outcome.remuxed:
                result.remuxed.append(filename)
            result.add_detail(
                filename,
                "updated",
                "Remuxed before tagging" if outcome.remuxed else "Tags applied",
                remuxed=outcome.remuxed,
            )
        else:
            result.failed.append(filename)
            result.add_detail(
                filename,
                "failed",
                outcome.error or "Tag update failed",
            )

    return result