"""Deprecated — use tag.py instead."""

import sys


def main() -> int:
    print("This CLI has been replaced by tag.py")
    print()
    print("Examples:")
    print('  python tag.py --folder "C:\\Music" --artist "kelvin" --genre "afropop"')
    print('  python tag.py --file "C:\\Music\\song.mp3" --artist "kelvin" --dry-run')
    print()
    print("For the desktop app: python gui.py")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())