"""Local recipe book. Run python server.py; data stays in user_data."""
import argparse
from contextlib import contextmanager
import base64
import io
import json
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import uuid
import tempfile
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

ROOT = Path(__file__).resolve().parent
CATEGORIES = json.loads((ROOT / 'web/categories.json').read_text())

def category_tags(tags):
    lookup = {name.casefold(): name for name in CATEGORIES}
    return list(dict.fromkeys(lookup[t.strip().casefold()] for t in tags if isinstance(t, str) and t.strip().casefold() in lookup)) if isinstance(tags, list) else []

DATA = Path(os.environ.get('RECIPE_DATA_DIR', ROOT / 'user_data'))

@contextmanager
def connect():
    DATA.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATA / 'recipes.sqlite3')
    db.execute('CREATE TABLE IF NOT EXISTS recipes (id TEXT PRIMARY KEY, title TEXT NOT NULL, document_json TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
    try:
        with db:
            yield db
    finally:
        db.close()

def draft(text):
    result = {'title': '', 'ingredients': [], 'instructions': [], 'tags': [], 'notes': '', 'import': {'status': 'awaiting_user_review', 'raw_text': text, 'issues': ['Check reading order, quantities, and completeness against the original before saving.']}}
    lines = [line.strip() for line in text.splitlines()]
    headings = {'ingredients', 'ingredient list', 'what you need'}
    first_ingredients = next((i for i, line in enumerate(lines) if line.lower().rstrip(':') in headings), None)
    if first_ingredients is not None:
        # ChatGPT often puts an introduction before the actual recipe title.
        preface = [line for line in lines[:first_ingredients] if line]
        for line in reversed(preface):
            if re.search(r'\d+\s*(?:minutes?|mins?|servings?)\b', line, re.I):
                continue
            result['title'] = line.lstrip('# ').strip('* ')[:200]
            break
        metadata = ' '.join(preface)
        minutes = re.search(r'(\d+)\s*(?:minutes?|mins?)', metadata, re.I)
        servings = re.search(r'(\d+(?:\s*[-–]\s*\d+)?)\s*servings?\b', metadata, re.I)
        if minutes:
            result['total_minutes'] = int(minutes.group(1))
        if servings:
            result['servings'] = servings.group(1).replace('–', '-').replace(' ', '')
    section = None
    current_step = None
    notes = []
    ingredient_lines = lines[first_ingredients + 1:] if first_ingredients is not None else lines
    ingredient_lines = ingredient_lines[:next((i for i, line in enumerate(ingredient_lines)
                                              if line.lower().rstrip(':') in ('instructions', 'directions', 'method', 'preparation', 'steps')),
                                             len(ingredient_lines))]
    bulleted_ingredients = any(re.match(r'^[*•●-]\s+', line) for line in ingredient_lines)
    for line in lines:
        if not line:
            continue
        heading = line.lower().rstrip(':')
        if heading in headings:
            section = 'ingredients'; continue
        if heading in ('instructions', 'directions', 'method', 'preparation', 'steps'):
            section = 'instructions'; continue
        if heading in ('notes', 'nutrition', 'nutrition facts') or heading.startswith(('a couple of suggestions', 'one important consideration')):
            section = 'notes'; current_step = None
            if heading not in ('notes', 'nutrition', 'nutrition facts'):
                notes.append(line)
            continue
        if section == 'ingredients':
            if re.match(r'^[*•●-]\s+', line):
                result['ingredients'].append({'text': re.sub(r'^[*•●-]\s+', '', line)})
            elif not bulleted_ingredients or re.match(r'^\d', line):
                result['ingredients'].append({'text': line})
            # Subheadings such as "Pork and rice" and "Optional drizzle" organize
            # the source, but are not ingredients themselves.
        elif section == 'instructions':
            match = re.match(r'^\d+[.)]\s*(.*)', line)
            if match:
                current_step = {'text': match.group(1)}
                result['instructions'].append(current_step)
            elif current_step is not None:
                current_step['text'] += (' ' if current_step['text'] else '') + line
            else:
                result['instructions'].append({'text': line})
        elif section == 'notes':
            notes.append(re.sub(r'^[*•●-]\s+', '', line))
        elif not result['title']:
            result['title'] = line[:200]
    result['notes'] = '\n'.join(notes)
    if not result['ingredients'] or not result['instructions']:
        result['import']['issues'].append('Some sections could not be recognized. Fill them from the source text; nothing has been discarded from the original.')
    return result

class Handler(BaseHTTPRequestHandler):
    def respond(self, value, status=200):
        self.send_bytes(json.dumps(value, ensure_ascii=False).encode(), 'application/json; charset=utf-8', status)

    def send_bytes(self, content, mime, status=200):
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(content)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        match = re.fullmatch(r'/api/import-video/jobs/([A-Za-z0-9_-]{20,64})', path)
        if match:
            from video_jobs import get
            try: return self.respond(get(match.group(1), self.headers.get('X-Import-Token')))
            except ValueError as error: return self.respond({'error': str(error)}, 404)
        if path == '/health':
            return self.respond({'app': 'little-recipe-box', 'version': 1})
        if path == '/api/import-video/health':
            from video_import import health
            return self.respond(health())
        if path == '/api/recipes':
            with connect() as db:
                rows = db.execute('SELECT document_json,created_at FROM recipes ORDER BY created_at DESC, rowid DESC').fetchall()
            return self.respond([dict(json.loads(r[0]), tags=category_tags(json.loads(r[0]).get('tags', [])), created_at=r[1]) for r in rows])
        if path == '/api/backup':
            # SQLite's backup API makes a consistent snapshot while the app is open.
            with tempfile.TemporaryDirectory() as folder:
                target = Path(folder) / 'recipes.sqlite3'
                with connect() as source:
                    backup = sqlite3.connect(target)
                    try:
                        source.backup(backup)
                        if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                            raise RuntimeError('Backup integrity check failed')
                        records = [json.loads(row[0]) for row in backup.execute('SELECT document_json FROM recipes')]
                    finally:
                        backup.close()
                output = io.BytesIO()
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.write(target, 'recipes.sqlite3')
                    archive.writestr('recipes.json', json.dumps(records, ensure_ascii=False, indent=2))
                    for file in (DATA / 'originals').glob('*'):
                        if file.is_file(): archive.write(file, 'originals/' + file.name)
                    archive.writestr('RESTORE.txt', 'Close Recipe Book. Keep a copy of your current user_data folder. Extract recipes.sqlite3 and originals into user_data, then restart. recipes.json is a portable text export. Photos are included in recipe records. Trash is retained. Browser ingredient checkmarks are device-specific and are not in this backup.')
                content = output.getvalue()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="recipe-book-backup.zip"')
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return self.wfile.write(content)
        if path.startswith('/originals/'):
            base = (DATA / 'originals').resolve()
            file = (base / path.removeprefix('/originals/')).resolve()
        else:
            base = (ROOT / 'web').resolve()
            # Versioned shell paths bypass older cache-first service workers.
            aliases = {'/instagram': 'index.html', '/refresh': 'index.html',
                       '/app-v12.js': 'app.js', '/offline-v12.js': 'offline.js', '/style-v12.css': 'style.css',
                       '/app-v13.js': 'app.js', '/offline-v13.js': 'offline.js', '/style-v13.css': 'style.css',
                       '/app-v14.js': 'app.js', '/offline-v14.js': 'offline.js', '/style-v14.css': 'style.css',
                       '/app-v15.js': 'app.js', '/offline-v15.js': 'offline.js', '/style-v15.css': 'style.css',
                       '/app-v16.js': 'app.js', '/offline-v16.js': 'offline.js', '/style-v16.css': 'style.css',
                       '/app-v17.js': 'app.js', '/offline-v17.js': 'offline.js', '/style-v17.css': 'style.css',
                       '/app-v18.js': 'app.js', '/offline-v18.js': 'offline.js', '/style-v18.css': 'style.css',
                       '/app-v19.js': 'app.js', '/offline-v19.js': 'offline.js', '/style-v19.css': 'style.css',
                       '/app-v20.js': 'app.js', '/offline-v20.js': 'offline.js', '/style-v20.css': 'style.css',
                       '/app-v21.js': 'app.js', '/offline-v21.js': 'offline.js', '/style-v21.css': 'style.css'}
            file = (base / aliases.get(path, 'index.html' if path == '/' else path.lstrip('/'))).resolve()
        if not file.is_relative_to(base) or not file.is_file():
            return self.respond({'error': 'Not found'}, 404)
        self.send_bytes(file.read_bytes(), mimetypes.guess_type(file)[0] or 'application/octet-stream')

    def do_POST(self):
        # Local-only app: reject browser cross-origin writes and non-JSON forms.
        allowed_origin = os.environ.get('RECIPE_PUBLIC_ORIGIN') or 'http://' + self.headers.get('Host', '')
        if self.headers.get('Origin') and self.headers['Origin'] != allowed_origin:
            return self.respond({'error': 'Origin rejected'}, 403)
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            return self.respond({'error': 'Expected JSON'}, 415)
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 15_000_000:
                raise ValueError('Upload must be smaller than 10 MB.')
            body = json.loads(self.rfile.read(size))
            if self.path == '/api/import-video':
                from video_jobs import create
                return self.respond(create(body.get('url')), 202)
            match = re.fullmatch(r'/api/import-video/jobs/([A-Za-z0-9_-]{20,64})/cancel', self.path)
            if match:
                from video_jobs import cancel
                return self.respond(cancel(match.group(1), self.headers.get('X-Import-Token')))
            if self.path == '/api/import-images':
                from image_import import read_pages
                texts, images = read_pages(body.get('images'))
                result = draft('\n\n'.join(texts))
                result['source_photos'] = images
                result['import']['issues'].insert(0, 'Read from photos. Compare quantities, fractions, temperatures, and page order with the photos before saving.')
                for index, text in enumerate(texts):
                    if not text:
                        result['import']['issues'].append(f'No text could be read on page {index + 1}. Retake that page or fill in its text manually.')
                return self.respond(result)
            if self.path == '/api/import-photo':
                from url_import import import_photo
                return self.respond(import_photo(body.get('url')))
            if self.path == '/api/import-url':
                from url_import import import_url
                return self.respond(import_url(body.get('url')))
            if self.path == '/api/import':
                text = body.get('text', '')
                original = None
                if body.get('pdf'):
                    import pdfplumber
                    content = base64.b64decode(body['pdf'], validate=True)
                    if len(content) > 10_000_000 or not content.startswith(b'%PDF-'):
                        raise ValueError('Choose a PDF smaller than 10 MB.')
                    with pdfplumber.open(io.BytesIO(content)) as pdf:
                        if len(pdf.pages) > 30:
                            raise ValueError('Please import at most 30 pages at a time.')
                        text = '\n\n'.join(p.extract_text() or '' for p in pdf.pages)
                    original = f'originals/{uuid.uuid4().hex}.pdf'
                    (DATA / 'originals').mkdir(parents=True, exist_ok=True)
                    (DATA / original).write_bytes(content)
                if not isinstance(text, str) or len(text) > 500_000:
                    raise ValueError('Recipe text is too large.')
                result = draft(text)
                if original:
                    result['original_pdf'] = original
                if not text.strip():
                    result['import']['issues'].append('No readable text found. This PDF may be scanned. OCR is not available yet; type or paste the recipe while viewing the original.')
                return self.respond(result)
            if self.path == '/api/recipes':
                tags = body.get('tags', [])
                if not isinstance(tags, list) or any(t not in CATEGORIES for t in tags):
                    raise ValueError('Choose categories from the preset list.')
                body['tags'] = list(dict.fromkeys(tags))
                photo = body.get('photo')
                if photo:
                    if not isinstance(photo, str) or not photo.startswith('data:image/jpeg;base64,') or len(photo)>3_000_000:
                        raise ValueError('Choose a smaller photo.')
                    from PIL import Image
                    with Image.open(io.BytesIO(base64.b64decode(photo.split(',',1)[1], validate=True))) as img:
                        if img.format != 'JPEG' or img.width > 1600 or img.height > 1600:
                            raise ValueError('Photo must be a JPEG up to 1600 pixels.')
                        img.verify()
                title = body.get('title', '')
                if not isinstance(title, str) or not title.strip() or len(title) > 200:
                    raise ValueError('Enter a title of 1–200 characters.')
                for field in ('ingredients', 'instructions'):
                    if not isinstance(body.get(field), list) or (field == 'ingredients' and not body[field]) or any(not isinstance(x, dict) or not isinstance(x.get('text'), str) or not x['text'].strip() for x in body[field]):
                        raise ValueError('Add at least one ingredient. Directions are optional; provided lines must contain text.')
                body['title'] = title.strip()
                body['id'] = body.get('id') or uuid.uuid4().hex
                with connect() as db:
                    db.execute('INSERT INTO recipes(id,title,document_json) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, document_json=excluded.document_json, updated_at=CURRENT_TIMESTAMP', (body['id'], body['title'], json.dumps(body, ensure_ascii=False)))
                return self.respond(body)
            self.respond({'error': 'Not found'}, 404)
        except (ValueError, TypeError, KeyError) as error:
            self.respond({'error': str(error)}, 400)
        except Exception:
            self.respond({'error': 'Could not process this file or save the recipe. Try another PDF or paste its text.'}, 500)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8771)
    args = parser.parse_args()
    with connect():
        pass
    print(f'Recipe Book: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()
