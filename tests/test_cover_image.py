import io
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from core.cover_image import crop_to_square, prepare_cover_bytes


class CoverImageTests(unittest.TestCase):
    def test_crop_portrait_to_square(self):
        image = Image.new("RGB", (1170, 1560), color="red")
        square = crop_to_square(image)
        self.assertEqual(square.size, (1170, 1170))

    def test_prepare_cover_outputs_square_jpeg(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "portrait.png"
            Image.new("RGB", (800, 1200), color="blue").save(path)

            data, mime = prepare_cover_bytes(path, size=500, quality=85)

            self.assertEqual(mime, "image/jpeg")
            self.assertGreater(len(data), 1000)
            with Image.open(io.BytesIO(data)) as result:
                self.assertEqual(result.size, (500, 500))


if __name__ == "__main__":
    unittest.main()