"""Representative interpretation fixtures, including visual-only quantities."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from video_recipe import interpret, quantity_signature

CASES = json.loads((Path(__file__).parent / 'fixtures/video_recipe_cases.json').read_text(encoding='utf-8'))
URL = 'https://www.instagram.com/reel/AbCd12345/'
INFO = {'title': 'Instagram Reel', 'uploader': 'cookalice'}


class RecipeEvidenceFixtures(unittest.TestCase):
    def test_fraction_and_unit_equivalence(self):
        self.assertEqual(quantity_signature('1.5 lbs chicken'), quantity_signature('1½ pounds chicken'))
        self.assertEqual(quantity_signature('1.5 lbs chicken'), quantity_signature('1 1/2 lb chicken'))
        self.assertEqual(quantity_signature('2 tsp paprika'), quantity_signature('two teaspoons paprika'))
        self.assertNotEqual(quantity_signature('2 tsp paprika'), quantity_signature('2 tbsp paprika'))

    def test_interpretation_cases(self):
        for case in CASES:
            with self.subTest(case=case['name']):
                args=(URL, INFO, case['caption'], case['transcript'], case['onscreen'])
                if case.get('fails'):
                    with self.assertRaises(ValueError): interpret(*args)
                    continue
                draft=interpret(*args)
                actual=[item['text'] for item in draft['ingredients']]
                self.assertEqual(actual, case['ingredients'])
                if 'title' in case: self.assertEqual(draft['title'].casefold(), case['title'].casefold())
                self.assertGreaterEqual(len(draft['instructions']), case.get('minimum_steps', 0))
                issues=' '.join(draft['import']['issues']).casefold()
                for ingredient in case.get('quantity_warnings', []):
                    self.assertIn(f'quantity for {ingredient} was not specified', issues)
                if 'conflict' in case: self.assertEqual('differs between' in issues, case['conflict'])
                self.assertEqual(draft['source_url'], URL)
                self.assertEqual(draft['import']['status'], 'awaiting_user_review')
                self.assertIn(case['transcript'] or '(none)', draft['import']['raw_text'])
                self.assertIn(case['onscreen'] or '(none)', draft['import']['raw_text'])

    def test_stated_cook_time_is_not_invented_as_total_time(self):
        draft=interpret(URL, INFO, '', 'Add 1 cup rice. Bake at 375 degrees for 20 minutes.', '')
        self.assertEqual([item['text'] for item in draft['ingredients']], ['1 cup rice'])
        self.assertIsNone(draft['total_minutes'])
        self.assertIn('375 degrees for 20 minutes', draft['instructions'][1]['text'])


if __name__ == '__main__': unittest.main()
