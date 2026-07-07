import tempfile
import unittest
from pathlib import Path

from core.config import AppConfig


class ConfigTests(unittest.TestCase):
    def test_loads_custom_watermark_patterns(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "config.yaml"
            config_path.write_text(
                "watermark_patterns:\n  - 'TestSite.com'\n",
                encoding="utf-8",
            )
            config = AppConfig.load(config_path)
            self.assertEqual(config.watermark_patterns, ["TestSite.com"])

    def test_defaults_when_file_missing(self):
        config = AppConfig.load(Path("/nonexistent/config.yaml"))
        self.assertEqual(config.ffmpeg_path, "ffmpeg")
        self.assertTrue(config.watermark_patterns)


if __name__ == "__main__":
    unittest.main()