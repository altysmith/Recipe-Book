import base64
import io
import unittest
from unittest.mock import patch
from PIL import Image
from url_import import image_url, import_photo
import test_server

class PhotoTests(unittest.TestCase):
    def test_schema_image_shapes(self):
        for value in ['/food.jpg', {'url':'/food.jpg'}, [{'contentUrl':'/food.jpg'}]]:
            self.assertEqual(image_url(value,'https://example.com/r'),'https://example.com/food.jpg')
        self.assertIsNone(image_url('file:///private','https://example.com'))
    def test_photo_resize_and_failure(self):
        data=io.BytesIO();Image.new('RGB',(2000,1000),'red').save(data,'PNG')
        with patch('url_import.fetch_page',return_value=(data.getvalue(),'https://example.com/photo')):
            result=import_photo('https://example.com/photo')
        with Image.open(io.BytesIO(base64.b64decode(result['photo'].split(',')[1]))) as image:
            self.assertEqual(image.size,(1400,700));self.assertEqual(image.format,'JPEG')
        with patch('url_import.fetch_page',side_effect=ValueError('Private address')):
            self.assertIsNone(import_photo('http://127.0.0.1/photo')['photo'])

class CategoryTests(unittest.TestCase):
    setUp = test_server.RecipeTests.setUp
    tearDown = test_server.RecipeTests.tearDown
    post = test_server.RecipeTests.post
    def test_preset_categories_only(self):
        from urllib.error import HTTPError
        recipe={'title':'Soup','ingredients':[{'text':'Water'}],'instructions':[],'tags':['Soups & Stews']}
        self.assertEqual(self.post('/api/recipes',recipe)['tags'],['Soups & Stews'])
        recipe['tags']=['Custom category']
        with self.assertRaises(HTTPError) as error:self.post('/api/recipes',recipe)
        self.assertEqual(error.exception.code,400)
