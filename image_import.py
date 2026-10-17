"""Private photo OCR. Images never leave the recipe server."""
import base64
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from PIL import Image, ImageOps, UnidentifiedImageError


def read_pages(pages):
    if not isinstance(pages, list) or not 1 <= len(pages) <= 4:
        raise ValueError('Choose between 1 and 4 recipe photos.')
    executable = os.environ.get('RECIPE_TESSERACT') or shutil.which('tesseract')
    if not executable:
        raise ValueError('Photo reading is not set up on the server yet. You can still paste recipe text.')
    normalized = []
    for page in pages:
        if not isinstance(page, str) or len(page) > 3_500_000 or not page.startswith('data:image/jpeg;base64,'):
            raise ValueError('Choose a smaller JPEG or PNG photo.')
        try:
            content = base64.b64decode(page.split(',', 1)[1], validate=True)
            with Image.open(io.BytesIO(content)) as image:
                if image.format != 'JPEG' or image.width * image.height > 12_000_000:
                    raise ValueError('Recipe photos must be at most 12 megapixels.')
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.thumbnail((2400, 2400))
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=90)
                normalized.append(output.getvalue())
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as error:
            raise ValueError('This photo could not be opened. Try a JPEG or PNG screenshot.') from error
    texts = []
    with tempfile.TemporaryDirectory(prefix='recipe-ocr-') as folder:
        for index, content in enumerate(normalized):
            source = Path(folder) / f'page-{index}.jpg'
            source.write_bytes(content)
            try:
                result = subprocess.run([executable, str(source), 'stdout', '-l', 'eng', '--psm', '3'],
                                        capture_output=True, timeout=20, check=True,
                                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except subprocess.TimeoutExpired as error:
                raise ValueError('Reading took too long. Try one cropped, clear recipe photo at a time.') from error
            except (OSError, subprocess.CalledProcessError) as error:
                raise ValueError('The server could not read this photo. Check that Tesseract and its English language data are installed.') from error
            texts.append(result.stdout.decode('utf-8', errors='replace').strip())
    return texts, ['data:image/jpeg;base64,' + base64.b64encode(content).decode('ascii') for content in normalized]
