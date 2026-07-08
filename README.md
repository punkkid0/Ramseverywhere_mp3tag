# Ramseverywhere MP3 Tag

Bulk auto-tagging tool for downloaded MP3s. Cleans site watermarks from titles, formats artist names, handles singles vs albums, embeds cover art (auto square resize), and sets a default comment.

## Requirements

- **Python 3.10+** (3.11 or 3.12 recommended)
- **pip**
- **ffmpeg** (optional but recommended — used to fix broken MP3 files before tagging)

### Install ffmpeg (optional)

- Windows: download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH  
- Or: `winget install Gyan.FFmpeg`

## Setup

```powershell
git clone https://github.com/punkkid0/Ramseverywhere_mp3tag.git
cd Ramseverywhere_mp3tag
pip install -r requirements.txt
```

### Python packages (`requirements.txt`)

| Package | Purpose |
|---------|---------|
| `mutagen` | Read/write MP3 ID3 tags |
| `pandas` | Legacy CSV support (optional CLI) |
| `PyYAML` | Load `config.yaml` |
| `Pillow` | Resize/crop cover art to square |
| `customtkinter` | Desktop GUI (when using `gui.py`) |

## Quick start (CLI)

**Preview changes (no files modified):**

```powershell
python tag.py --folder "C:\Music\MyFolder" --artist "Nathaniel Bassey" --genre "Gospel" --dry-run
```

**Apply tags to a whole folder:**

```powershell
python tag.py --folder "C:\Music\MyFolder" --artist "Nathaniel Bassey" --genre "Gospel" --year 2026
```

**Single file:**

```powershell
python tag.py --file "C:\Music\song.mp3" --artist "Sinach" --genre "afropop" --mode single
```

**With cover image** (place image in music folder or use full path):

```powershell
python tag.py --folder "C:\Music\MyFolder" --artist "kelvin" --genre "afropop" --cover cover.jpg
```

Remove `--dry-run` when you are ready to write tags.

## What gets applied automatically

| Field | Rule |
|-------|------|
| **Title** | Strips site names (CeeNaija, JustNaija, waploaded, jointearn, etc.) |
| **Artist** | `Nathaniel Bassey` → `nathaniel-Bassey` |
| **Year** | Keeps existing tag, or uses `--year` |
| **Album** | Single → `Title (single)`; album → keeps existing album name |
| **Track** | Single → `1`; album → existing tag or number from filename (`03 song.mp3`) |
| **Genre** | Uses `--genre` if provided, else keeps existing |
| **Comment** | `downloaded from jointearn.com` (editable in `config.yaml`) |
| **Album artist** | Set for albums; empty for singles |
| **Cover** | Keeps existing art unless `--cover` is set; new images are cropped to 1000×1000 |

## CLI flags

| Flag | Description |
|------|-------------|
| `--folder` | Folder of MP3 files |
| `--file` | One MP3 file (or folder of MP3s) |
| `--artist` | **Required** — artist name |
| `--genre` | Genre (batch) |
| `--year` | Year when file has none |
| `--album` | Manual album override |
| `--track` | Manual track override |
| `--mode` | `auto`, `single`, or `album` |
| `--cover` | Cover image path |
| `--dry-run` | Preview only — **does not modify files** |
| `--config` | Path to custom `config.yaml` |
| `--report` | Save JSON report after run |

## Configuration

Edit `config.yaml` in the project folder:

- `site_names` — sites to strip from titles  
- `tags.comment` — default comment text  
- `cover.size` — embedded cover size in pixels (default `1000`)  
- `ffmpeg.path` — path to ffmpeg executable  

## Desktop GUI

```powershell
python gui.py
```

> **Note:** GUI is being rebuilt to match `tag.py`. Use the CLI for production tagging until the new GUI is released.

## Backups

Every tagged file gets a `.bak` copy next to the original before changes are written.

## Tests

```powershell
python -m unittest discover -s tests -v
```

## Project layout

```
Ramseverywhere_mp3tag/
├── tag.py          # Main CLI (use this)
├── gui.py          # Desktop app launcher
├── config.yaml     # Rules and defaults
├── core/           # Tagging engine
├── app/            # GUI (legacy, being rebuilt)
└── tests/
```

## License

Private / internal worker tool — adjust as needed for your team.