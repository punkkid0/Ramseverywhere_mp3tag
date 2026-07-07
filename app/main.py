import logging
import sys

from app.window import Mp3TagApp


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app = Mp3TagApp()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())