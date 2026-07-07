from dataclasses import dataclass, field


@dataclass
class SongRow:
    filename: str
    title: str = ""
    year: str = ""
    artist: str = ""
    album: str = ""
    track: str = ""
    genre: str = ""
    comment: str = ""
    cover: str = ""
    status: str = "pending"
    message: str = ""
    is_new: bool = False

    def to_tags(self) -> dict[str, str]:
        return {
            "artist": self.artist,
            "album": self.album,
            "track": self.track,
            "genre": self.genre,
            "comment": self.comment,
            "cover": self.cover,
        }

    def has_tags_to_apply(self) -> bool:
        return any(self.to_tags().values())


@dataclass
class AppState:
    folder: str = ""
    csv_path: str = ""
    songs: list[SongRow] = field(default_factory=list)
    dry_run: bool = False