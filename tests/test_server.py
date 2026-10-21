import json
import sqlite3
import zipfile
import base64
import io
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import sys
import struct
import time
from unittest.mock import patch
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

    def test_weekly_menu_save_reopen_and_backup(self):
        week = '2026-10-17'
        empty = json.load(urlopen(self.url+'/api/weekly-menu/'+week))
        self.assertEqual(empty['days'], ['' for _ in range(7)])
        empty['days'][0] = 'Pork butt + baked beans + baked potatoes'
        empty['snacks'] = 'Cucumbers + carrots and hummus\nGrapes'
        empty['lunches'] = 'Crispy grilled chicken + broccoli + rice'
        empty['sweet_treats'] = 'Ice cream bars'
        saved = self.post('/api/weekly-menu', empty)
        self.assertEqual(json.load(urlopen(self.url+'/api/weekly-menu/'+week)), saved)
        self.assertEqual(json.load(urlopen(self.url+'/api/weekly-menu/2026-10-24'))['days'][0], '')
        with zipfile.ZipFile(io.BytesIO(urlopen(self.url+'/api/backup').read())) as archive:
            self.assertEqual(json.loads(archive.read('weekly-menus.json'))[0], saved)
            with sqlite3.connect(':memory:') as restored:
                restored.deserialize(archive.read('recipes.sqlite3'))
                self.assertEqual(restored.execute('SELECT count(*) FROM weekly_menus').fetchone()[0], 1)

    def test_weekly_menu_rejects_invalid_week_and_shape(self):
        with self.assertRaises(HTTPError) as error:
            self.post('/api/weekly-menu', {'week_start': '2026-10-19', 'days': ['']*7})
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            self.post('/api/weekly-menu', {'week_start': '2026-10-17', 'days': ['']*6})
        self.assertEqual(error.exception.code, 400)
        with self.assertRaises(HTTPError) as error:
            urlopen(self.url+'/api/weekly-menu/2026-10-19')
        self.assertEqual(error.exception.code, 400)

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

    def test_chatgpt_recipe_paste(self):
        text=('That’s Smithfield Korean BBQ Seasoned Pork Loin Strips.\n\n'
              'Korean BBQ Pork Rice Bowls\n\nHigh protein30 minutes2–3 servings\n\n'
              'Ingredients\nPork and rice\n* 1 package (16 oz) pork strips\n* 1 cup jasmine rice\n'
              'Optional Korean BBQ drizzle\n* 2 tbsp tamari\n\nInstructions\n'
              '1. Prepare the rice\nCook jasmine rice according to package instructions.\n\n'
              '2. Cook the pork\nSear until cooked through.\n\n'
              'A couple of suggestions\n* For leftovers: refrigerate promptly.\n\n'
              'One important consideration: Check the pork allergen label.')
        draft=self.post('/api/import',{'text':text})
        self.assertEqual(draft['title'],'Korean BBQ Pork Rice Bowls')
        self.assertEqual(draft['total_minutes'],30)
        self.assertEqual(draft['servings'],'2-3')
        self.assertEqual([item['text'] for item in draft['ingredients']],
                         ['1 package (16 oz) pork strips','1 cup jasmine rice','2 tbsp tamari'])
        self.assertEqual(draft['instructions'][0]['text'],
                         'Prepare the rice Cook jasmine rice according to package instructions.')
        self.assertIn('Check the pork allergen label',draft['notes'])
        self.assertEqual(draft['import']['raw_text'],text)
        with server.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM recipes').fetchone()[0],0)

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

    def test_fresh_instagram_entry_uses_versioned_shell(self):
        page=urlopen(self.url+'/instagram').read().decode()
        self.assertIn('Instagram Reel',page)
        self.assertEqual(urlopen(self.url+'/refresh').read().decode(),urlopen(self.url+'/').read().decode())
        self.assertIn('/app-v22.js',page)
        for alias,original in (('/app-v22.js','/app.js'),('/offline-v22.js','/offline.js'),('/style-v22.css','/style.css')):
            self.assertEqual(urlopen(self.url+alias).read(),urlopen(self.url+original).read())

    def test_home_screen_metadata_and_icons_are_served(self):
        page=urlopen(self.url+'/').read().decode()
        self.assertIn('<title>Lolo’s Kitchen</title>',page)
        self.assertIn('<span>Lolo’s<br>Kitchen</span>',page)
        self.assertIn('name="apple-mobile-web-app-title" content="Lolo’s Kitchen"',page)
        self.assertIn('rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png"',page)
        self.assertIn('rel="manifest" href="/manifest.webmanifest"',page)
        self.assertIn('name="apple-mobile-web-app-capable" content="yes"',page)
        with urlopen(self.url+'/manifest.webmanifest') as response:
            self.assertEqual(response.headers.get_content_type(),'application/manifest+json')
            manifest=json.load(response)
        self.assertEqual(manifest['name'],'Lolo’s Kitchen')
        self.assertEqual(manifest['short_name'],'Lolo’s Kitchen')
        self.assertEqual((manifest['start_url'],manifest['scope'],manifest['display']),('/','/','standalone'))
        for path,size in (('/apple-touch-icon.png',180),('/icon-192.png',192),('/icon-512.png',512)):
            with urlopen(self.url+path) as response:
                self.assertEqual(response.headers.get_content_type(),'image/png')
                png=response.read()
            self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II',png[16:24]),(size,size))
        self.assertEqual({icon['src'] for icon in manifest['icons']},{'/icon-192.png','/icon-512.png'})

    def test_shell_updates_from_network_without_caching_recipe_api(self):
        worker=urlopen(self.url+'/sw.js').read().decode()
        self.assertIn("recipe-shell-v22",worker)
        self.assertNotIn("'/refresh'",worker)
        self.assertIn('await fetch(event.request',worker)
        self.assertIn('await cache.match(url.pathname)',worker)
        self.assertNotIn("'/api/recipes'",worker)

    def test_invalid_save_does_not_write(self):
        with self.assertRaises(HTTPError): self.post('/api/recipes',{'title':'Empty'})
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes')),[])

    def test_seasoning_without_directions(self):
        result=self.post('/api/recipes',{'title':'Seasoning', 'ingredients':[{'text':'1 tsp salt'}], 'instructions':[]})
        self.assertEqual(result['instructions'],[])
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes'))[0]['title'],'Seasoning')

    def test_video_job_draft_requires_explicit_save(self):
        source='https://www.instagram.com/reel/AbCd12345/'
        candidate={'title':'Pasta','ingredients':[{'text':'1 cup pasta'}],
                   'instructions':[{'text':'Boil pasta.','number':1}], 'tags':[],
                   'source_url':source,'author':'cookalice',
                   'import':{'method':'instagram_reel','status':'awaiting_user_review','raw_text':'Audio transcript\nBoil pasta.','issues':[]}}
        with patch('video_jobs.import_video', return_value=candidate):
            created=self.post('/api/import-video',{'url':source})
            for _ in range(100):
                request=Request(self.url+'/api/import-video/jobs/'+created['job_id'],headers={'X-Import-Token':created['token']})
                result=json.load(urlopen(request))
                if result['state']=='completed': break
                time.sleep(.01)
        self.assertEqual(result['result']['source_url'],source)
        self.assertEqual(json.load(urlopen(self.url+'/api/recipes')),[])
        with self.assertRaises(HTTPError) as error:
            urlopen(self.url+'/api/import-video/jobs/'+created['job_id'])
        self.assertEqual(error.exception.code,404)
        candidate['title']='My pasta';candidate['tags']=['Pasta'];candidate['import']['status']='reviewed'
        self.post('/api/recipes',candidate)
        reopened=json.load(urlopen(self.url+'/api/recipes'))[0]
        self.assertEqual(reopened['title'],'My pasta')
        self.assertEqual(reopened['tags'],['Pasta'])
        self.assertEqual(reopened['source_url'],source)

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
