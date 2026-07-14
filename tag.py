"""
Auto MP3 tagger — bulk or single file.

Examples:
  python tag.py --folder "C:\\Music" --artist "Nathaniel Bassey" --genre "Gospel"
  python tag.py --file "C:\\Music\\song.mp3" --artist "Nathaniel Bassey" --year 2024
  python tag.py --folder "C:\\Music" --artist "Sinach" --dry-run
"""

import argparse
import logging
import sys

from core.auto_tag import TagJobOptions, collect_mp3_files, preview_tags, process_files
from core.config import AppConfig


def print_preview(previews) -> None:
    for item in previews:
        print(f"\n=== {item.filename} ({item.mode}) ===")
        for field in (
            "title",
            "artist",
            "year",
            "album",
            "track",
            "genre",
            "comment",
            "album_artist",
        ):
            before = item.before.get(field, "")
            after = item.after.get(field, "")
            if before != after or after:
                print(f"  {field:13}  {before or '-':30} -> {after or '-'}")


def print_summary(result) -> None:
    print("\n--- Summary ---")
    print(f"Updated: {len(result.updated)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Failed:  {len(result.failed)}")
    print(f"Remuxed: {len(result.remuxed)}")
    if result.dry_run:
        print("Mode:    dry-run (no files modified)")
    for detail in result.details:
        if detail.status in {"skipped", "failed"}:
            print(f"  - {detail.filename}: {detail.message}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Auto-tag MP3 files for workers (bulk or single)."
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--folder", help="Folder containing MP3 files")
    target.add_argument(
        "--file",
        help="Tag one MP3 file, or a folder of MP3s if you pass a directory path",
    )

    parser.add_argument(
        "--artist",
        default="",
        help=(
            'Optional artist override. If omitted, uses the tag on each file '
            '(formatted, e.g. "Nathaniel Bassey" -> nathaniel-Bassey).'
        ),
    )
    parser.add_argument("--genre", default="", help="Genre for files that do not already have one")
    parser.add_argument("--year", default="", help="Year for files that do not already have one")
    parser.add_argument("--album", default="", help="Manual album name override")
    parser.add_argument("--track", default="", help="Manual track number override")
    parser.add_argument(
        "--mode",
        choices=["auto", "single", "album"],
        default="auto",
        help="auto trusts existing album tags; single/album forces the type",
    )
    parser.add_argument(
        "--cover",
        default="",
        help="Cover image for the batch/file. Existing cover is kept if this is omitted.",
    )
    parser.add_argument(
        "--comment",
        default="",
        help="ID3 comment text (any string). Overrides config.yaml. Leave blank to skip or keep existing.",
    )
    parser.add_argument("--config", help="Path to config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="Preview tags without writing")
    parser.add_argument("--report", help="Save JSON report to this path")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    config = AppConfig.load(args.config)
    options = TagJobOptions(
        artist=args.artist,
        genre=args.genre,
        year=args.year,
        album=args.album,
        track=args.track,
        mode=args.mode,
        cover=args.cover,
        comment=args.comment,
    )

    try:
        files = collect_mp3_files(folder=args.folder, file_path=args.file)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    if not files:
        print("No MP3 files found in that location.")
        return 1

    if args.cover.strip():
        from core.tagger import resolve_cover_path

        if not resolve_cover_path(files[0], args.cover.strip()):
            print(
                f"Error: Cover image not found: {args.cover!r}\n"
                f"  Put the image in the music folder (e.g. {files[0].parent})\n"
                f"  or pass a full path like C:\\path\\to\\image.png"
            )
            return 1
        print(f"Using cover: {resolve_cover_path(files[0], args.cover.strip())}")

    print(f"Found {len(files)} MP3 file(s).")

    if args.dry_run:
        print("\n*** DRY-RUN: No files will be modified. Remove --dry-run to apply. ***\n")
        previews = [preview_tags(path, options, config) for path in files]
        print_preview(previews)
        result = process_files(files, options, config=config, dry_run=True)
        print_summary(result)
        return 0

    result = process_files(files, options, config=config, dry_run=False)
    print_summary(result)

    if args.report:
        result.save_json(args.report)
        print(f"Report saved to: {args.report}")

    return 0 if not result.failed else 1


if __name__ == "__main__":
    raise SystemExit(main())