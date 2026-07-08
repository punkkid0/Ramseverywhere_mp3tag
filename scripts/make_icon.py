"""Build assets/app_icon.ico from assets/app_icon_source.png (or generate fallback)."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SOURCE = ASSETS / "app_icon_source.png"
OUTPUT = ASSETS / "app_icon.ico"


def _draw_fallback(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), "#0A0A0A")
    draw = ImageDraw.Draw(img)
    margin = size // 8
    draw.rounded_rectangle(
        (margin, margin, size - margin, size - margin),
        radius=size // 6,
        fill="#141414",
        outline="#FACC15",
        width=max(2, size // 32),
    )
    # Simple note + tag shapes in gold
    gold = "#FACC15"
    cx = size // 2
    cy = size // 2
    r = size // 10
    draw.ellipse((cx - r, cy - r * 2, cx + r, cy), fill=gold)
    draw.rectangle((cx, cy - r * 3, cx + r // 3, cy - r), fill=gold)
    draw.polygon(
        [
            (cx + size // 5, cy + size // 10),
            (cx + size // 3, cy + size // 6),
            (cx + size // 6, cy + size // 4),
        ],
        fill=gold,
    )
    return img


def main() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    if SOURCE.exists():
        base = Image.open(SOURCE).convert("RGBA")
        base = base.resize((512, 512), Image.Resampling.LANCZOS)
    else:
        base = _draw_fallback(512)

    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(OUTPUT, format="ICO", sizes=sizes)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()