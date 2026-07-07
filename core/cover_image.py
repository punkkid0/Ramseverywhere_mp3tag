import io
from pathlib import Path

from PIL import Image, ImageOps

from core.exceptions import TagWriteError

# Standard square album-art size used by most players and tools.
DEFAULT_COVER_SIZE = 1000
DEFAULT_JPEG_QUALITY = 90


def crop_to_square(image: Image.Image) -> Image.Image:
    """Center-crop an image to a square."""
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def prepare_cover_bytes(
    cover_path: Path,
    size: int = DEFAULT_COVER_SIZE,
    quality: int = DEFAULT_JPEG_QUALITY,
) -> tuple[bytes, str]:
    """
    Prepare cover art for ID3 embedding.

    - Center-crops to square (fixes portrait/landscape photos)
    - Resizes to `size` x `size`
    - Saves as JPEG for broad player support
    """
    try:
        with Image.open(cover_path) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode in {"RGBA", "LA", "P"}:
                background = Image.new("RGB", image.size, (255, 255, 255))
                rgba = image.convert("RGBA")
                background.paste(rgba, mask=rgba.split()[-1])
                image = background
            else:
                image = image.convert("RGB")

            square = crop_to_square(image)
            if square.size != (size, size):
                square = square.resize((size, size), Image.Resampling.LANCZOS)

            buffer = io.BytesIO()
            square.save(buffer, format="JPEG", quality=quality, optimize=True)
            return buffer.getvalue(), "image/jpeg"
    except Exception as exc:
        raise TagWriteError(f"Failed to prepare cover image {cover_path.name}: {exc}") from exc