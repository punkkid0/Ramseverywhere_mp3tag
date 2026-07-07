import unittest

from core.detection import (
    detect_mode,
    parse_track_from_filename,
    resolve_track,
    single_album_name,
)


class DetectionTests(unittest.TestCase):
    def test_detect_single_when_no_album(self):
        self.assertEqual(detect_mode(""), "single")

    def test_detect_album_from_existing_tag(self):
        self.assertEqual(detect_mode("The Name of Jesus"), "album")

    def test_detect_single_marker(self):
        self.assertEqual(detect_mode("Way Maker (single)"), "single")

    def test_manual_override(self):
        self.assertEqual(detect_mode("Album Name", "single"), "single")

    def test_parse_track_from_filename(self):
        self.assertEqual(parse_track_from_filename("03 Holy Spirit.mp3"), "3")

    def test_single_track_is_one(self):
        self.assertEqual(resolve_track("single", "", "song.mp3"), "1")

    def test_single_album_name(self):
        self.assertEqual(single_album_name("Way Maker"), "Way Maker (single)")


if __name__ == "__main__":
    unittest.main()