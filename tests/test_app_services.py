import tempfile
import unittest
from pathlib import Path

from app.models import SongItem
from app.services import (
    list_mp3_items_from_file,
    list_mp3_items_from_folder,
    validate_cover,
)
from core.auto_tag import TagJobOptions


class AppServicesTests(unittest.TestCase):
    def test_list_mp3_items_from_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "a.mp3").write_bytes(b"x")
            (folder / "b.txt").write_bytes(b"x")
            items = list_mp3_items_from_folder(str(folder))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].filename, "a.mp3")

    def test_list_mp3_items_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp3 = Path(tmp) / "single.mp3"
            mp3.write_bytes(b"x")
            items = list_mp3_items_from_file(str(mp3))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].filename, "single.mp3")

    def test_validate_cover_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            mp3 = folder / "song.mp3"
            mp3.write_bytes(b"x")
            songs = [SongItem(path=mp3)]
            error = validate_cover(songs, "missing.jpg")
            self.assertIsNotNone(error)


if __name__ == "__main__":
    unittest.main()