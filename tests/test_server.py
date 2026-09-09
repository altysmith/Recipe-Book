import json
import base64
import io
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server

class RecipeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = server.DATA
        server.DATA = Path(self.tmp.name)
        self.http = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.http.server_port}'

    def tearDown(self):
        self.http.shutdown(); self.http.server_close(); self.thread.join()
        server.DATA = self.old
        self.tmp.cleanup()

    def post(self, path, data, origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        return json.load(urlopen(Request(self.url+path, json.dumps(data).encode(), headers)))

    def test_save_update_reopen_preserves_source(self):
        recipe={'title':'Test soup', 'ingredients':[{'text':'1 cup water'}], 'instructions':[{'text':'Warm.'}], 'import':{'raw_text':'Original'}, 'original_pdf':'originals/test.pdf'}
        saved=self.post('/api/recipes',recipe)
        saved['notes']='Use a large pot'
        self.post('/api/recipes',saved)
        rows=json.load(urlopen(self.url+'/api/recipes'))
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['notes'],'Use a large pot')
        self.assertEqual(rows[0]['import']['raw_text'],'Original')
        with server.connect() as db: self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_unfamiliar_format_preserved_for_review(self):
        text='Grandma says\nPut a pinch in the bowl\nThen stir until ready'
        draft=self.post('/api/import',{'text':text})
        self.assertEqual(draft['import']['raw_text'],text)
        self.assertEqual(draft['ingredients'],[])
        self.assertEqual(draft['import']['status'],'awaiting_user_review')

    def test_other_headings(self):
        draft=self.post('/api/import',{'text':'Soup\nWhat you need:\n1 cup water\nMethod:\n1. Warm water.'})
        self.assertEqual(draft['ingredients'][0]['text'],'1 cup water')
        self.assertEqual(draft['instructions'][0]['text'],'Warm water.')

    def test_pdf_original_retained(self):
        from reportlab.pdfgen import canvas
        buffer=io.BytesIO()
        page=canvas.Canvas(buffer)
        for y,text in [(750,'Soup'),(730,'Ingredients'),(710,'1 cup water'),(690,'Directions'),(670,'1. Warm water.')]:
            page.drawString(40,y,text)
        page.save()
        content=buffer.getvalue()
        result=self.post('/api/import',{'pdf':base64.b64encode(content).decode()})
        self.assertEqual((server.DATA/result['original_pdf']).read_bytes(),content)
        self.assertIn('1 cup water',result['import']['raw_text'])
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes')),[])

    def test_cross_origin_and_traversal(self):
        with self.assertRaises(HTTPError) as error:
            self.post('/api/import',{'text':'x'},'https://example.com')
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(HTTPError) as error:
            urlopen(self.url+'/originals/../../server.py')
        self.assertEqual(error.exception.code,404)

    def test_invalid_save_does_not_write(self):
        with self.assertRaises(HTTPError): self.post('/api/recipes',{'title':'Empty'})
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes')),[])

    def test_seasoning_without_directions(self):
        result=self.post('/api/recipes',{'title':'Seasoning', 'ingredients':[{'text':'1 tsp salt'}], 'instructions':[]})
        self.assertEqual(result['instructions'],[])
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes'))[0]['title'],'Seasoning')

    def test_backup_trash_and_photo(self):
        import zipfile
        import sqlite3
        from PIL import Image
        photo=io.BytesIO();Image.new('RGB',(20,20),'red').save(photo,'JPEG')
        recipe=self.post('/api/recipes',{'title':'Photo recipe','ingredients':[{'text':'Salt'}],'instructions':[], 'photo':'data:image/jpeg;base64,'+base64.b64encode(photo.getvalue()).decode()})
        recipe['deleted']=True;self.post('/api/recipes',recipe)
        with zipfile.ZipFile(io.BytesIO(urlopen(self.url+'/api/backup').read())) as archive:
            exported=json.loads(archive.read('recipes.json'))
            self.assertTrue(exported[0]['deleted']);self.assertEqual(exported[0]['photo'],recipe['photo'])
            target=server.DATA/'restored.sqlite3';target.write_bytes(archive.read('recipes.sqlite3'))
            db=sqlite3.connect(target)
            try:self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:db.close()
        recipe['deleted']=False;self.post('/api/recipes',recipe)
        self.assertFalse(json.load(urlopen(self.url+'/api/recipes'))[0]['deleted'])

if __name__=='__main__': unittest.main()
