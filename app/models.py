from dataclasses import dataclass, field
from pathlib import Path

from core.auto_tag import TagPreview
from core.detection import detect_mode


@dataclass
class SongItem:
    path: Path
    existing: dict[str, str] = field(default_factory=dict)
    preview: TagPreview | None = None
    status: str = "ready"
    message: str = ""
    selected: bool = True
    has_cover: bool = False
    cover_bytes: bytes | None = None

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def display(self) -> dict[str, str]:
        if self.preview:
            return self.preview.after
        return self.existing

    @property
    def mode(self) -> str:
        if self.preview:
            return self.preview.mode
        return detect_mode(self.existing.get("album", ""))

    def field(self, name: str) -> str:
        return self.display.get(name, "")


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