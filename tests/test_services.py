import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.models import SongRow
from app.services import (
    dataframe_from_songs,
    default_csv_path,
    load_library,
    save_library,
    songs_from_dataframe,
)
from core.csv_store import CSV_COLUMNS


class ServicesTests(unittest.TestCase):
    def test_default_csv_path(self):
        self.assertTrue(default_csv_path("C:/Music").endswith("tags.csv"))

    def test_roundtrip_songs_csv(self):
        songs = [
            SongRow(
                filename="a.mp3",
                title="Song A",
                artist="Artist",
                genre="Gospel",
            )
        ]
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "tags.csv"
            save_library(songs, str(csv_path))
            loaded = load_library(tmp, str(csv_path))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0].artist, "Artist")

    def test_songs_from_dataframe_marks_new_files(self):
        df = pd.DataFrame(
            {
                "filename": ["new.mp3"],
                "title": ["Title"],
                "year": [""],
                "artist": [""],
                "album": [""],
                "track": [""],
                "genre": [""],
                "comment": [""],
                "cover": [""],
            }
        )
        songs = songs_from_dataframe(df, new_files={"new.mp3"})
        self.assertTrue(songs[0].is_new)

    def test_dataframe_from_songs_has_all_columns(self):
        df = dataframe_from_songs([SongRow(filename="a.mp3")])
        self.assertEqual(list(df.columns), CSV_COLUMNS)


if __name__ == "__main__":
    unittest.main()