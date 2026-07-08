from dataclasses import dataclass, field
from pathlib import Path

from core.auto_tag import TagPreview


@dataclass
class SongItem:
    path: Path
    preview: TagPreview | None = None
    status: str = "pending"
    message: str = ""
    selected: bool = True

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def mode(self) -> str:
        if self.preview:
            return self.preview.mode
        return ""

    @property
    def title_after(self) -> str:
        if self.preview:
            return self.preview.after.get("title", "")
        return ""

    @property
    def artist_after(self) -> str:
        if self.preview:
            return self.preview.after.get("artist", "")
        return ""


@dataclass
class AppState:
    source_path: str = ""
    source_type: str = ""  # "folder" or "file"
    songs: list[SongItem] = field(default_factory=list)
    last_result_summary: str = ""

    @property
    def folder(self) -> str:
        """Directory used for cover lookup and display."""
        if not self.source_path:
            return ""
        path = Path(self.source_path)
        if self.source_type == "file":
            return str(path.parent)
        return str(path)