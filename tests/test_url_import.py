import json
import unittest
from unittest.mock import patch
from url_import import parse_page, public_target, fetch_page

class URLTests(unittest.TestCase):
    def page(self,recipes):return '<script type="application/ld+json">'+json.dumps(recipes)+'</script>'
    def test_graph_sections_and_optional_instructions(self):
        recipe={'@type':'Recipe','name':'<b>Rub</b>','recipeIngredient':['1 tsp salt'], 'recipeInstructions':[{'@type':'HowToSection','itemListElement':[{'text':'Mix.'}]}],'totalTime':'PT1H15M','author':{'name':'Chef'}}
        r=parse_page(self.page({'@graph':[recipe]}),'https://example.com/r')[0]
        self.assertEqual(r['title'],'Rub');self.assertEqual(r['total_minutes'],75)
        self.assertEqual(r['instructions'][0]['text'],'Mix.')
        del recipe['recipeInstructions']
        self.assertEqual(parse_page(self.page(recipe),'https://example.com')[0]['instructions'],[])
    def test_multiple_recipes_and_invalid_json(self):
        recipes=[{'@type':'Recipe','name':name,'recipeIngredient':['salt']} for name in ['A','B']]
        self.assertEqual(len(parse_page('<script type="application/ld+json">bad</script>'+self.page(recipes),'https://example.com')),2)
    def test_no_recipe(self):
        with self.assertRaisesRegex(ValueError,'copy and paste'):parse_page('<h1>Article</h1>','https://example.com')
    def test_private_and_unsafe_targets(self):
        for url in ['file:///etc/passwd','https://user:pass@example.com','http://example.com:8080']:
            with self.assertRaises(ValueError):public_target(url)
        with patch('url_import.socket.getaddrinfo',return_value=[(2,1,6,'',('127.0.0.1',80))]):
            with self.assertRaises(ValueError):public_target('http://example.com')

if __name__=='__main__':unittest.main()
