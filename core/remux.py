import logging
import shutil
import subprocess
from pathlib import Path

from core.exceptions import RemuxError

logger = logging.getLogger(__name__)


def resolve_ffmpeg_path(ffmpeg_path: str = "ffmpeg") -> str | None:
    """Resolve ffmpeg to an executable path."""
    candidate = Path(ffmpeg_path)
    if candidate.exists():
        return str(candidate)
    return shutil.which(ffmpeg_path)


def ffmpeg_available(ffmpeg_path: str = "ffmpeg") -> bool:
    """Return True when ffmpeg is available."""
    return resolve_ffmpeg_path(ffmpeg_path) is not None


def remux_with_ffmpeg(
    src_path: Path,
    dest_path: Path,
    ffmpeg_path: str = "ffmpeg",
    timeout: int = 60,
) -> None:
    """Rewrap an MP3 into a new container without re-encoding."""
    executable = resolve_ffmpeg_path(ffmpeg_path)
    if not executable:
        raise RemuxError(f"ffmpeg not found: {ffmpeg_path}")

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        executable,
        "-y",
        "-i",
        str(src_path),
        "-c",
        "copy",
        str(dest_path),
    ]

    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise RemuxError(f"ffmpeg timed out for {src_path.name}") from exc
    except OSError as exc:
        raise RemuxError(f"ffmpeg failed to start for {src_path.name}: {exc}") from exc

    if proc.returncode != 0 or not dest_path.exists():
        logger.debug("ffmpeg stderr for %s: %s", src_path.name, proc.stderr.strip())
        raise RemuxError(
            f"ffmpeg failed for {src_path.name} (exit code {proc.returncode})"
        )