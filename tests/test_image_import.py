import base64
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import Image, ImageDraw, ImageFont
import image_import
import server


def recipe_image():
    image = Image.new('RGB', (1400, 1000), 'white')
    candidates = ['C:/Windows/Fonts/arial.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    font = next((ImageFont.truetype(p, 44) for p in candidates if Path(p).exists()), ImageFont.load_default(size=44))
    ImageDraw.Draw(image).multiline_text((80, 70), 'Simple Soup\n\nIngredients\n1 cup water\n2 cups stock\n\nDirections\n1. Mix in a pot.\n2. Simmer for 10 minutes.', font=font, fill='black', spacing=16)
    output = io.BytesIO(); image.save(output, 'JPEG')
    return 'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode()


class ImageImportTests(unittest.TestCase):
    def test_reject_invalid_uploads(self):
        for value in (None, [], ['x'] * 5, ['data:image/jpeg;base64,invalid']):
            with self.subTest(value=value), self.assertRaises(ValueError):
                image_import.read_pages(value)

    def test_timeout_is_actionable(self):
        with patch('image_import.shutil.which', return_value='tesseract'), patch('image_import.subprocess.run', side_effect=subprocess.TimeoutExpired('tesseract', 20)):
            with self.assertRaisesRegex(ValueError, 'too long'):
                image_import.read_pages([recipe_image()])

    def test_missing_engine_is_actionable(self):
        with patch.dict('os.environ', {}, clear=True), patch('image_import.shutil.which', return_value=None):
            with self.assertRaisesRegex(ValueError, 'not set up'):
                image_import.read_pages([recipe_image()])

    @unittest.skipUnless(shutil.which('tesseract'), 'Tesseract not installed')
    def test_real_ocr_http_review_and_save(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(server, 'DATA', Path(folder)):
            http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
            thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
            url = f'http://127.0.0.1:{http.server_port}'
            def post(path, body):
                return json.load(urlopen(Request(url + path, json.dumps(body).encode(), {'Content-Type': 'application/json'})))
            try:
                draft = post('/api/import-images', {'images': [recipe_image()]})
                self.assertEqual(draft['title'], 'Simple Soup')
                self.assertEqual(draft['ingredients'][0]['text'], '1 cup water')
                self.assertIn('Simmer for 10 minutes.', draft['instructions'][1]['text'])
                self.assertEqual(len(draft['source_photos']), 1)
                self.assertEqual(json.load(urlopen(url + '/api/recipes')), [])
                saved = post('/api/recipes', draft)
                self.assertEqual(saved['source_photos'], draft['source_photos'])
            finally:
                http.shutdown(); http.server_close(); thread.join()
