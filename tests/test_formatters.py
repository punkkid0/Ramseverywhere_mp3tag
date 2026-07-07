import unittest

from core.formatters import format_artist


class FormatArtistTests(unittest.TestCase):
    def test_two_part_name(self):
        self.assertEqual(format_artist("Nathaniel Bassey"), "nathaniel-Bassey")

    def test_three_part_name(self):
        self.assertEqual(format_artist("John Mark McMillan"), "john-Mark-McMillan")

    def test_single_word(self):
        self.assertEqual(format_artist("Sinach"), "sinach")


if __name__ == "__main__":
    unittest.main()