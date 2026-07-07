import tempfile
import unittest
from pathlib import Path

from mutagen.id3 import ID3, TALB, TIT2

from core.auto_tag import TagJobOptions, build_auto_tags
from core.config import AppConfig


class AutoTagTests(unittest.TestCase):
    def test_single_rules(self):
        existing = {
            "title": "Way Maker || jointearn.com",
            "year": "",
            "artist": "",
            "album": "",
            "track": "",
            "genre": "",
            "comment": "",
        }
        options = TagJobOptions(artist="Sinach", genre="Gospel")
        tags = build_auto_tags(Path("way_maker.mp3"), existing, options, AppConfig())

        self.assertEqual(tags["title"], "Way Maker")
        self.assertEqual(tags["artist"], "sinach")
        self.assertEqual(tags["album"], "Way Maker (single)")
        self.assertEqual(tags["track"], "1")
        self.assertEqual(tags["genre"], "Gospel")
        self.assertEqual(tags["comment"], "downloaded from jointearn.com")
        self.assertEqual(tags["album_artist"], "")

    def test_album_rules_trust_existing_album(self):
        existing = {
            "title": "Holy Spirit",
            "year": "2024",
            "artist": "",
            "album": "The Name of Jesus",
            "track": "2",
            "genre": "Worship",
            "comment": "",
        }
        options = TagJobOptions(artist="Nathaniel Bassey")
        tags = build_auto_tags(Path("02 Holy Spirit.mp3"), existing, options, AppConfig())

        self.assertEqual(tags["artist"], "nathaniel-Bassey")
        self.assertEqual(tags["album"], "The Name of Jesus")
        self.assertEqual(tags["track"], "2")
        self.assertEqual(tags["year"], "2024")
        self.assertEqual(tags["genre"], "Worship")
        self.assertEqual(tags["album_artist"], "nathaniel-Bassey")

    def test_track_from_filename_when_missing(self):
        existing = {
            "title": "Holy Spirit",
            "year": "",
            "artist": "",
            "album": "The Name of Jesus",
            "track": "",
            "genre": "",
            "comment": "",
        }
        options = TagJobOptions(artist="Nathaniel Bassey")
        tags = build_auto_tags(Path("03 Holy Spirit.mp3"), existing, options, AppConfig())
        self.assertEqual(tags["track"], "3")


if __name__ == "__main__":
    unittest.main()