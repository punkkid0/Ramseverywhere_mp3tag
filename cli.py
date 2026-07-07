import argparse
import logging
import sys

from core.config import AppConfig
from core.csv_store import process_csv, sync_csv_with_folder
from core.remux import ffmpeg_available


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def prompt_for_bulk_tags() -> dict[str, str]:
    print("\nNew songs detected!")
    print(
        "You can enter details once, and they'll apply to all new songs.\n"
        "(Title and year will be kept automatically.)\n"
    )
    return {
        "artist": input("Enter artist name (leave blank to skip): ").strip(),
        "album": input("Enter album name (leave blank to skip): ").strip(),
        "genre": input("Enter genre (leave blank to skip): ").strip(),
        "comment": input("Enter comment (leave blank to skip): ").strip(),
        "cover": input(
            "Enter cover file name (e.g., ram.jpg, leave blank to skip): "
        ).strip(),
    }


def apply_bulk_tags(df, new_files: list[str], tags: dict[str, str]) -> None:
    for index, row in df.iterrows():
        if row["filename"] not in new_files:
            continue
        for field, value in tags.items():
            if value:
                df.at[index, field] = value


def print_summary(result) -> None:
    print("\n--- Summary ---")
    print(f"Updated: {len(result.updated)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Failed:  {len(result.failed)}")
    print(f"Remuxed: {len(result.remuxed)}")
    if result.dry_run:
        print("Mode:    dry-run (no files modified)")
    if result.remuxed:
        print("Remuxed files:")
        for name in result.remuxed:
            print(f"  - {name}")
    if result.failed:
        print("Failed files:")
        for name in result.failed:
            print(f"  - {name}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch edit MP3 tags (preserves title/year) with auto-sync prompt."
    )
    parser.add_argument("--folder", required=True, help="Folder containing music files")
    parser.add_argument("--csv", required=True, help="Path to tags_template.csv")
    parser.add_argument(
        "--config",
        help="Path to config.yaml (defaults to ./config.yaml if present)",
    )
    parser.add_argument(
        "--sync", action="store_true", help="Sync new files and prompt for tags"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying MP3 files",
    )
    parser.add_argument(
        "--report",
        help="Write a JSON report of the batch run to this path",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show debug logging output"
    )
    args = parser.parse_args(argv)

    configure_logging(args.verbose)
    config = AppConfig.load(args.config)

    if not ffmpeg_available(config.ffmpeg_path):
        logging.warning(
            "ffmpeg not found (%s). Remux recovery will not be available.",
            config.ffmpeg_path,
        )

    if args.sync:
        df, new_files = sync_csv_with_folder(args.folder, args.csv, config=config)
        if new_files:
            bulk_tags = prompt_for_bulk_tags()
            apply_bulk_tags(df, new_files, bulk_tags)
            df.to_csv(args.csv, index=False)
            print("\nTags updated in CSV for all new songs.")

    if not args.sync:
        result = process_csv(
            args.folder,
            args.csv,
            dry_run=args.dry_run,
            config=config,
        )
        print_summary(result)
        if args.report:
            result.save_json(args.report)
            print(f"Report saved to: {args.report}")

    print("\nOperation completed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())