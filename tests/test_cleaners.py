import unittest

from core.cleaners import clean_title


class CleanTitleTests(unittest.TestCase):
    def test_removes_pipe_watermark(self):
        title = "Amazing Grace || CeeNaija.com"
        self.assertEqual(clean_title(title), "Amazing Grace")

    def test_removes_single_pipe_site_suffix(self):
        title = "Amen | JustNaija.com"
        self.assertEqual(clean_title(title), "Amen")

    def test_removes_parenthetical_watermark(self):
        title = "Holy Spirit (CeeNaija.com)"
        self.assertEqual(clean_title(title), "Holy Spirit")

    def test_preserves_clean_title(self):
        title = "Way Maker"
        self.assertEqual(clean_title(title), "Way Maker")

    def test_handles_empty_title(self):
        self.assertEqual(clean_title(""), "")


if __name__ == "__main__":
    unittest.main()