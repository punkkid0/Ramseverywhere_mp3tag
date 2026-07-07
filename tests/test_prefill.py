import tempfile
import unittest
from pathlib import Path

from mutagen.id3 import ID3, TIT2, TPE1, TDRC

from core.csv_store import sync_csv_with_folder
from core.tagger import read_tags_from_file


class PrefillTests(unittest.TestCase):
    def _write_tagged_mp3(self, path: Path) -> None:
        tags = ID3()
        tags.add(TIT2(encoding=3, text="Holy Spirit || CeeNaija.com"))
        tags.add(TDRC(encoding=3, text="2024"))
        tags.add(TPE1(encoding=3, text="Nathaniel Bassey"))
        tags.save(path, v2_version=3)

    def test_read_tags_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            mp3_path = Path(tmp) / "song.mp3"
            self._write_tagged_mp3(mp3_path)

            tags = read_tags_from_file(mp3_path)

            self.assertEqual(tags["title"], "Holy Spirit || CeeNaija.com")
            self.assertEqual(tags["year"], "2024")
            self.assertEqual(tags["artist"], "Nathaniel Bassey")

    def test_sync_prefills_csv_columns(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            mp3_path = folder / "song.mp3"
            self._write_tagged_mp3(mp3_path)
            csv_path = folder / "tags.csv"

            df, new_files = sync_csv_with_folder(str(folder), str(csv_path))

            self.assertEqual(new_files, ["song.mp3"])
            row = df.iloc[0]
            self.assertEqual(row["title"], "Holy Spirit || CeeNaija.com")
            self.assertEqual(row["artist"], "Nathaniel Bassey")
            self.assertEqual(row["year"], "2024")


if __name__ == "__main__":
    unittest.main()