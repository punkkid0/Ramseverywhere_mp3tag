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
    folder: str = ""
    songs: list[SongItem] = field(default_factory=list)
    last_result_summary: str = ""