import json
import tempfile
import unittest
from pathlib import Path

from core.report import ProcessResult


class ReportTests(unittest.TestCase):
    def test_save_json_writes_summary(self):
        result = ProcessResult(dry_run=True)
        result.updated.append("song.mp3")
        result.add_detail("song.mp3", "updated", "Tags applied")

        with tempfile.TemporaryDirectory() as tmp:
            report_path = Path(tmp) / "report.json"
            result.save_json(report_path)

            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["updated"], 1)
            self.assertTrue(payload["dry_run"])
            self.assertEqual(payload["details"][0]["filename"], "song.mp3")


if __name__ == "__main__":
    unittest.main()