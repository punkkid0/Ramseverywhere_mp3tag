import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from mutagen.id3 import (
    APIC,
    COMM,
    ID3,
    ID3NoHeaderError,
    TALB,
    TCON,
    TDRC,
    TIT2,
    TPE1,
    TPE2,
    TRCK,
)
from mutagen.mp3 import MP3

from core.cleaners import clean_title
from core.config import AppConfig
from core.cover_image import prepare_cover_bytes
from core.exceptions import (
    RemuxError,
    TagLoadError,
    TagWriteError,
    UnsupportedFormatError,
)
from core.remux import remux_with_ffmpeg

logger = logging.getLogger(__name__)

MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


@dataclass
class TagOutcome:
    success: bool
    remuxed: bool = False
    error: str | None = None


def cover_mime_type(cover_path: Path) -> str:
    mime = MIME_BY_SUFFIX.get(cover_path.suffix.lower())
    if mime:
        return mime
    raise TagWriteError(f"Unsupported cover image format: {cover_path.suffix}")


def resolve_cover_path(file_path: Path, cover: str) -> Path | None:
    if not cover:
        return None

    cover_path = Path(cover)
    if cover_path.is_absolute():
        return cover_path if cover_path.exists() else None

    search_roots = [file_path.parent, Path.cwd()]
    seen: set[Path] = set()
    for root in search_roots:
        root = root.resolve()
        if root in seen:
            continue
        seen.add(root)

        candidate = root / cover_path
        if candidate.exists():
            return candidate

        by_name = root / cover_path.name
        if by_name.exists():
            return by_name

    return None


def _load_mp3(file_path: Path) -> MP3:
    try:
        try:
            return MP3(str(file_path), ID3=ID3)
        except ID3NoHeaderError:
            audio = MP3(str(file_path))
            audio.add_tags()
            return audio
    except Exception as exc:
        raise TagLoadError(f"Failed loading tags for {file_path.name}: {exc}") from exc


def _extract_cover_frames(audio: MP3) -> list[APIC]:
    if not audio.tags:
        return []
    return list(audio.tags.getall("APIC"))


def read_tags_from_file(file_path: Path) -> dict[str, str]:
    fields = {
        "title": "",
        "year": "",
        "artist": "",
        "album": "",
        "track": "",
        "genre": "",
        "comment": "",
        "album_artist": "",
    }

    if file_path.suffix.lower() != ".mp3":
        return fields

    tag_source = None
    try:
        audio = _load_mp3(file_path)
        tag_source = audio.tags
    except TagLoadError:
        try:
            tag_source = ID3(str(file_path))
        except Exception:
            return fields

    if not tag_source:
        return fields

    tag_map = {
        "TIT2": "title",
        "TDRC": "year",
        "TPE1": "artist",
        "TALB": "album",
        "TRCK": "track",
        "TCON": "genre",
        "TPE2": "album_artist",
    }
    for frame_id, field_name in tag_map.items():
        if frame_id in tag_source:
            fields[field_name] = str(tag_source[frame_id].text[0])

    comm_frames = tag_source.getall("COMM") if hasattr(tag_source, "getall") else []
    if comm_frames:
        fields["comment"] = str(comm_frames[0].text[0])
    elif "COMM" in tag_source:
        fields["comment"] = str(tag_source["COMM"].text[0])

    return fields


def create_backup(file_path: Path, suffix: str = ".bak") -> Path:
    backup = file_path.with_suffix(file_path.suffix + suffix)
    if backup.exists():
        backup.unlink()
    shutil.copy2(file_path, backup)
    return backup


def restore_backup(file_path: Path, backup: Path) -> None:
    shutil.copy2(backup, file_path)


def edit_tags(
    file_path: Path,
    tags: dict,
    config: AppConfig | None = None,
    preserve_cover: bool = True,
) -> None:
    """Write tags to an MP3 file."""
    active_config = config or AppConfig()

    if file_path.suffix.lower() != ".mp3":
        raise UnsupportedFormatError("Unsupported format (only .mp3 supported).")

    audio = _load_mp3(file_path)
    saved_covers = _extract_cover_frames(audio) if preserve_cover else []

    title = tags.get("title")
    if not title and audio.tags and "TIT2" in audio.tags:
        title = clean_title(
            audio.tags["TIT2"].text[0],
            patterns=active_config.watermark_patterns,
            site_names=active_config.site_names,
        )

    year = tags.get("year")
    if not year and audio.tags and "TDRC" in audio.tags:
        year = str(audio.tags["TDRC"].text[0])

    audio.delete()
    try:
        audio.add_tags()
    except Exception:
        pass

    if title:
        audio.tags.add(TIT2(encoding=3, text=title))
    if year:
        audio.tags.add(TDRC(encoding=3, text=str(year)))
    if tags.get("artist"):
        audio.tags.add(TPE1(encoding=3, text=tags["artist"]))
    if tags.get("album"):
        audio.tags.add(TALB(encoding=3, text=tags["album"]))
    if tags.get("track"):
        audio.tags.add(TRCK(encoding=3, text=str(tags["track"])))
    if tags.get("genre"):
        audio.tags.add(TCON(encoding=3, text=tags["genre"]))
    if tags.get("album_artist"):
        audio.tags.add(TPE2(encoding=3, text=tags["album_artist"]))
    if tags.get("comment"):
        audio.tags.add(
            COMM(encoding=3, lang="eng", desc="", text=tags["comment"])
        )

    cover_request = tags.get("cover", "").strip()
    cover_path = resolve_cover_path(file_path, cover_request) if cover_request else None

    if cover_request and not cover_path:
        if saved_covers:
            for frame in saved_covers:
                audio.tags.add(frame)
        raise TagWriteError(
            f"Cover image not found: {cover_request!r} "
            f"(looked next to {file_path.name} and the current folder)"
        )

    if cover_path:
        cover_data, mime = prepare_cover_bytes(
            cover_path,
            size=active_config.cover_size,
            quality=active_config.cover_quality,
        )
        audio.tags.add(
            APIC(
                encoding=3,
                mime=mime,
                type=3,
                desc="Cover",
                data=cover_data,
            )
        )
    elif saved_covers:
        for frame in saved_covers:
            audio.tags.add(frame)

    try:
        audio.save(v2_version=3)
    except Exception as exc:
        raise TagWriteError(f"Failed saving tags for {file_path.name}: {exc}") from exc


def safe_edit_tags(
    file_path: Path,
    tags: dict,
    dry_run: bool = False,
    config: AppConfig | None = None,
    preserve_cover: bool = True,
) -> TagOutcome:
    active_config = config or AppConfig()

    if dry_run:
        logger.info("[dry-run] Would update tags for: %s", file_path.name)
        return TagOutcome(success=True)

    backup = create_backup(file_path, suffix=active_config.backup_suffix)

    try:
        edit_tags(
            file_path,
            tags,
            config=active_config,
            preserve_cover=preserve_cover,
        )
        logger.info("Tags updated for: %s (backup: %s)", file_path.name, backup.name)
        return TagOutcome(success=True)
    except (TagLoadError, TagWriteError, UnsupportedFormatError) as exc:
        logger.warning("Primary tagging failed for %s: %s", file_path.name, exc)
        restore_backup(file_path, backup)

    remux_dir = file_path.parent / "_remux_temp"
    remux_dir.mkdir(exist_ok=True)
    remux_path = remux_dir / f"{file_path.stem}_remux{file_path.suffix}"

    try:
        remux_with_ffmpeg(
            file_path,
            remux_path,
            ffmpeg_path=active_config.ffmpeg_path,
            timeout=active_config.ffmpeg_timeout,
        )
    except RemuxError as exc:
        logger.error("Remux failed for %s: %s", file_path.name, exc)
        return TagOutcome(success=False, error=str(exc))

    try:
        edit_tags(
            remux_path,
            tags,
            config=active_config,
            preserve_cover=preserve_cover,
        )
        file_path.unlink()
        shutil.move(str(remux_path), str(file_path))
        logger.info(
            "Replaced original with remuxed file: %s (backup: %s)",
            file_path.name,
            backup.name,
        )
        return TagOutcome(success=True, remuxed=True)
    except (TagLoadError, TagWriteError, UnsupportedFormatError) as exc:
        logger.error("Tagging failed on remuxed file for %s: %s", file_path.name, exc)
        restore_backup(file_path, backup)
        if remux_path.exists():
            remux_path.unlink()
        return TagOutcome(success=False, error=str(exc))