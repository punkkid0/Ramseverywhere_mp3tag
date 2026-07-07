import unittest
from pathlib import Path

from core.tagger import cover_mime_type


class CoverMimeTests(unittest.TestCase):
    def test_jpeg(self):
        self.assertEqual(cover_mime_type(Path("cover.jpg")), "image/jpeg")

    def test_png(self):
        self.assertEqual(cover_mime_type(Path("art.PNG")), "image/png")

    def test_webp(self):
        self.assertEqual(cover_mime_type(Path("cover.webp")), "image/webp")

    def test_unsupported_raises(self):
        with self.assertRaises(Exception):
            cover_mime_type(Path("cover.svg"))


if __name__ == "__main__":
    unittest.main()