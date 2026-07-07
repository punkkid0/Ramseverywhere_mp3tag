import tempfile
import unittest
from pathlib import Path

import pandas as pd

from core.csv_store import normalize_cell, process_csv, sync_csv_with_folder


class NormalizeCellTests(unittest.TestCase):
    def test_none_becomes_empty(self):
        self.assertEqual(normalize_cell(None), "")

    def test_nan_becomes_empty(self):
        self.assertEqual(normalize_cell(float("nan")), "")

    def test_string_nan_becomes_empty(self):
        self.assertEqual(normalize_cell("nan"), "")

    def test_strips_whitespace(self):
        self.assertEqual(normalize_cell("  gospel  "), "gospel")


class CsvStoreTests(unittest.TestCase):
    def test_sync_adds_new_mp3_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "song1.mp3").write_bytes(b"fake")
            (folder / "song2.mp3").write_bytes(b"fake")
            csv_path = folder / "tags.csv"

            df, new_files = sync_csv_with_folder(str(folder), str(csv_path))

            self.assertEqual(sorted(new_files), ["song1.mp3", "song2.mp3"])
            self.assertEqual(len(df), 2)
            self.assertTrue(csv_path.exists())

    def test_process_csv_skips_nan_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "song.mp3").write_bytes(b"fake")
            csv_path = folder / "tags.csv"
            pd.DataFrame(
                {
                    "filename": ["song.mp3"],
                    "artist": [float("nan")],
                    "genre": [""],
                    "comment": [""],
                    "cover": [""],
                }
            ).to_csv(csv_path, index=False)

            result = process_csv(str(folder), str(csv_path), dry_run=True)

            self.assertEqual(result.updated, [])
            self.assertIn("song.mp3", result.skipped)


if __name__ == "__main__":
    unittest.main()