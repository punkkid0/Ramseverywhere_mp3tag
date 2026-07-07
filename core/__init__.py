from core.auto_tag import TagJobOptions, build_auto_tags, process_files
from core.cleaners import clean_title
from core.config import AppConfig
from core.formatters import format_artist
from core.csv_store import CSV_COLUMNS, normalize_cell, process_csv, sync_csv_with_folder
from core.exceptions import (
    CsvError,
    Mp3TagError,
    RemuxError,
    TagLoadError,
    TagWriteError,
    UnsupportedFormatError,
)
from core.remux import ffmpeg_available, remux_with_ffmpeg
from core.report import FileReport, ProcessResult
from core.tagger import TagOutcome, edit_tags, read_tags_from_file, safe_edit_tags

__all__ = [
    "AppConfig",
    "TagJobOptions",
    "build_auto_tags",
    "format_artist",
    "process_files",
    "CSV_COLUMNS",
    "CsvError",
    "FileReport",
    "Mp3TagError",
    "ProcessResult",
    "RemuxError",
    "TagLoadError",
    "TagOutcome",
    "TagWriteError",
    "UnsupportedFormatError",
    "clean_title",
    "edit_tags",
    "ffmpeg_available",
    "normalize_cell",
    "process_csv",
    "read_tags_from_file",
    "remux_with_ffmpeg",
    "safe_edit_tags",
    "sync_csv_with_folder",
]