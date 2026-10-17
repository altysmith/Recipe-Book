"""Conservative recipe interpretation from caption, speech, and frame OCR."""
import re
from fractions import Fraction

NUMERIC = r'(?:\d+\s+\d+\s*/\s*\d+|\d+\s*/\s*\d+|\d+(?:[.,]\d+)?[¼½¾⅓⅔⅛⅜⅝⅞]?|[¼½¾⅓⅔⅛⅜⅝⅞]|one|two|three|four|five|six|seven|eight|nine|ten|some|a little|a pinch|an?|half)'
MEASURE = r'(?:cups?|tbsp|tablespoons?|tsp|teaspoons?|lbs?|pounds?|oz|ounces?|grams?|g|kg|ml|cloves?|cans?|bunch(?:es)?|slices?|pieces?)'
AMOUNT = re.compile(r'(?<!\w)(?P<value>' + NUMERIC + r')\s*(?P<unit>' + MEASURE + r')?\b', re.I)
UNIT = re.compile(r'\b(?:cups?|tbsp|tablespoons?|tsp|teaspoons?|lbs?|pounds?|oz|ounces?|grams?|kg|ml|cloves?|cans?|slices?)\b', re.I)
ACTION = re.compile(r'\b(?:add|mix|stir|whisk|chop|dice|slice|cut|heat|cook|bake|roast|boil|simmer|fry|saute|sauté|sear|flip|pour|toss|season|sprinkle|fold|serve|combine|preheat|blend|marinate|drain|top|spread)\b', re.I)
FOOD = re.compile(r'\b(?:oil|butter|salt|pepper|garlic|onion|chicken|beef|pork|fish|salmon|shrimp|rice|pasta|flour|sugar|milk|cream|cheese|parmesan|egg|tomato|broth|paprika|cumin|basil|oregano|potato|carrot|lemon|lime|water|vinegar|sauce|honey|bread|beans|chocolate|vanilla|cinnamon|yogurt|spinach|mushroom|zucchini|chili|cocoa|baking powder)\b', re.I)
HEADINGS = re.compile(r'^\s*(?:ingredients?|directions?|instructions?|method|steps?|what you need)\s*:?\s*$', re.I)
PROMO = re.compile(r'\b(?:follow me|link in bio|subscribe|comment below|sponsored|shop now|save this reel|views?|likes?|followers?)\b', re.I)
TIME_OR_TEMP = re.compile(r'^(?:minutes?|mins?|hours?|hrs?|seconds?|secs?|degrees?|°[CF]|°|followers?|people)\b', re.I)
NUMBER_WORDS = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
                'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'a': 1, 'an': 1, 'half': Fraction(1, 2)}
FRACTIONS = {'¼': Fraction(1, 4), '½': Fraction(1, 2), '¾': Fraction(3, 4),
             '⅓': Fraction(1, 3), '⅔': Fraction(2, 3), '⅛': Fraction(1, 8),
             '⅜': Fraction(3, 8), '⅝': Fraction(5, 8), '⅞': Fraction(7, 8)}
UNITS = {'cup': 'cup', 'cups': 'cup', 'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp',
         'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp', 'lb': 'lb', 'lbs': 'lb',
         'pound': 'lb', 'pounds': 'lb', 'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
         'gram': 'g', 'grams': 'g', 'g': 'g', 'kg': 'kg', 'ml': 'ml',
         'clove': 'clove', 'cloves': 'clove', 'can': 'can', 'cans': 'can'}
ALIASES = {'oil': re.compile(r'^(?:olive|vegetable|canola|avocado|sesame) oil$'),
           'cheese': re.compile(r'^(?:shredded|grated|sliced) cheese$'),
           'chicken': re.compile(r'^chicken (?:thighs?|breasts?|pieces?)$')}


def clean(line):
    return re.sub(r'\s+', ' ', re.sub(r'^[\s•●*\-]+|^\d+[.)]\s+', '', line)).strip()


def ingredient_key(line):
    s = AMOUNT.sub('', line.casefold(), count=1)
    s = UNIT.sub('', s)
    return re.sub(r'^of\s+', '', re.sub(r'[^a-z]+', ' ', s).strip())


def amount(line):
    m = AMOUNT.search(line)
    if not m: return ''
    value = m.group('value').casefold()
    return '' if value in ('some', 'a little', 'a pinch') or value in ('a', 'an') and not m.group('unit') else m.group(0).strip()


def quantity_signature(line):
    m = AMOUNT.search(line)
    if not m or not amount(line): return None
    raw_value = m.group('value').casefold().strip()
    value = raw_value.replace(' ', '')
    try:
        if re.fullmatch(r'\d+\s+\d+\s*/\s*\d+', raw_value):
            whole, part = raw_value.split(None, 1)
            number = Fraction(int(whole)) + Fraction(part.replace(' ', ''))
        elif value in NUMBER_WORDS: number = Fraction(NUMBER_WORDS[value])
        elif value[-1:] in FRACTIONS:
            number = Fraction(value[:-1].replace(',', '.')) + FRACTIONS[value[-1]] if value[:-1] else FRACTIONS[value[-1]]
        elif '/' in value and value.count('/') == 1:
            number = Fraction(value)
        else: number = Fraction(value.replace(',', '.'))
    except (ValueError, ZeroDivisionError): return None
    unit = (m.group('unit') or '').casefold()
    return number, UNITS.get(unit, unit)


def measured_parts(text):
    """Split lists at each stated amount; never supply an amount of our own."""
    matches = list(AMOUNT.finditer(text))
    parts = []
    for index, match in enumerate(matches):
        tail = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        if TIME_OR_TEMP.match(tail.lstrip()): continue
        tail = re.split(r'[,;.]|\b(?:then|until|before|after)\b|\bfor\s+(?:about\s+)?\d', tail, maxsplit=1, flags=re.I)[0]
        tail = re.sub(r'\s+and\s*$', '', tail).strip(' ,.;')
        candidate = clean(match.group(0) + ' ' + tail)
        if not tail or len(candidate) > 100: continue
        if match.group('unit') or FOOD.search(tail) or match.group('value')[0].isdigit():
            parts.append(candidate)
    return parts


def ingredient_lines(line):
    parts = measured_parts(line)
    return parts if parts else [line]


def matched_evidence(key, evidence):
    if key in evidence: return evidence[key]
    for generic, specific in ALIASES.items():
        if key == generic:
            return next((item for other, item in evidence.items() if specific.fullmatch(other)), None)
        if specific.fullmatch(key):
            return evidence.get(generic)
    return None


def explicit_lines(text):
    ingredients = []; steps = []; section = None; title = ''
    for raw in text.splitlines():
        line = clean(raw)
        if not line: continue
        if HEADINGS.fullmatch(line):
            section = 'ingredients' if 'ingredient' in line.casefold() or 'need' in line.casefold() else 'steps'
            continue
        if PROMO.search(line): continue
        if section == 'ingredients':
            if ACTION.search(line) and not AMOUNT.match(line): section = 'steps'
            else:
                ingredients.append(line); continue
        if section == 'steps': steps.append(line); continue
        if not title and len(line) < 100 and not ACTION.search(line) and not AMOUNT.match(line): title = line
    return title, ingredients, steps


def speech_parts(text):
    # Whisper plain text has sentence boundaries but may not have line breaks.
    sentences = [clean(s) for s in re.split(r'(?<=[.!?])\s+|\n+', text) if clean(s)]
    ingredients = []; steps = []
    for sentence in sentences:
        if PROMO.search(sentence): continue
        if ACTION.search(sentence):
            clauses = re.split(r',\s*(?:then\s+)?(?=(?:add|mix|stir|flip|pour|toss|cook|bake|simmer|sear|serve)\b)|\s+(?:then|and)\s+(?=(?:add|mix|stir|flip|pour|toss|cook|bake|simmer|sear|serve)\b)', sentence, flags=re.I)
            steps.extend(clean(clause) for clause in clauses if clean(clause))
            quantified = measured_parts(sentence)
            if quantified:
                ingredients.extend(quantified)
                continue
            m = re.search(r'\b(?:add|use|with|need)\s+(.+?)(?:\s+(?:and then|then|to the|into the|in the|until)\b|[.!?]|$)', sentence, re.I)
            if m and FOOD.search(m.group(1)):
                part = clean(re.split(r'\s+and\s+(?=' + ACTION.pattern + r')', m.group(1), maxsplit=1, flags=re.I)[0])
                if 2 < len(part) < 90: ingredients.append(part)
            elif FOOD.search(sentence):
                for food in dict.fromkeys(x.casefold() for x in FOOD.findall(sentence)):
                    ingredients.append(food)
        else: ingredients.extend(measured_parts(sentence))
    return ingredients, steps


def visual_ingredients(text):
    return [line for raw in text.splitlines() if (line := clean(raw)) and len(line) < 100
            and not PROMO.search(line) and (UNIT.search(line) or
            re.match(r'^(?:\d|[¼½¾⅓⅔⅛⅜⅝⅞])', line) and FOOD.search(line))]


def interpret(source, info, caption, transcript, onscreen, stage_warnings=(), timestamped=None):
    caption_title, cap_ing, cap_steps = explicit_lines(caption)
    speech_ing, speech_steps = speech_parts(transcript)
    visual_ing = visual_ingredients(onscreen)
    warnings = list(stage_warnings); ingredients = []; evidence = {}; conflicts = set()
    if len(re.findall(r'(?im)^\s*ingredients?\s*:', caption)) > 1:
        warnings.append('The caption may contain more than one recipe. Separate them before saving.')
    if re.search(r'https?://|link in bio', caption, re.I):
        warnings.append('The creator caption points to an external recipe source. Check it for missing details.')
    for kind, lines in (('caption', cap_ing), ('audio', speech_ing), ('on-screen text', visual_ing)):
        for line in lines:
            for part in ingredient_lines(line):
                key = ingredient_key(part)
                if not key: continue
                existing = matched_evidence(key, evidence)
                if existing:
                    original_quantity = quantity_signature(existing['text'])
                    new_quantity = quantity_signature(part)
                    if original_quantity and new_quantity and original_quantity != new_quantity:
                        if key not in conflicts:
                            warnings.append(f'Quantity for {key} differs between {existing["source"]} ("{existing["text"]}") and {kind} ("{part}").')
                            conflicts.add(key)
                    elif not amount(existing['text']) and amount(part):
                        existing.update(text=part, source=kind)
                        evidence[key] = existing
                else:
                    item = {'text': part, 'source': kind}
                    evidence[key] = item; ingredients.append(item)
    steps = cap_steps or speech_steps
    steps = list(dict.fromkeys(steps))[:60]
    spoken_title = re.search(r"\b(?:today\s+(?:we\s+are|we're|i\s+am|i'm)\s+(?:making|cooking)|let's\s+make|this\s+is\s+my)\s+([^.!?]{3,90})", transcript, re.I)
    title = caption_title or (spoken_title.group(1).strip() if spoken_title else '') or str(info.get('title') or '')
    title = re.sub(r'^@?[^:]{1,35}:\s*', '', title).strip()[:200]
    if not title or title.casefold() in ('instagram', 'reel', 'instagram reel') or ' on instagram' in title.casefold():
        title = 'Review recipe title'; warnings.append('The recipe title could not be identified. Enter it before saving.')
    if not ingredients and not steps:
        raise ValueError('No recipe ingredients or cooking directions were detected in this video.')
    if not ingredients: warnings.append('No ingredients were detected. Add them from the video before saving.')
    if not steps: warnings.append('No cooking instructions were detected.')
    for item in ingredients:
        if not amount(item['text']): warnings.append(f'Quantity for {ingredient_key(item["text"])} was not specified.')
    creator = info.get('uploader_id') or ''
    if not isinstance(creator, str) or not creator or creator.isdigit(): creator = info.get('uploader') or ''
    if not isinstance(creator, str): creator = ''
    combined = caption + '\n' + transcript
    servings = re.search(r'\b(?:serves|servings?\s*:?|makes\s+enough\s+for)\s*(\d{1,3})\b', combined, re.I)
    total = re.search(r'\btotal\s+(?:time\s*)?:?\s*(\d{1,3})\s*(minutes?|mins?|hours?|hrs?)\b', combined, re.I)
    total_minutes = int(total.group(1)) * (60 if total and total.group(2).lower().startswith(('h',)) else 1) if total else None
    raw = 'Original caption\n' + (caption or '(none)') + '\n\nAudio transcript\n' + (timestamped or transcript or '(none)') + '\n\nOn-screen text\n' + (onscreen or '(none)')
    return {'title': title, 'ingredients': [{'text': x['text']} for x in ingredients],
            'instructions': [{'text': x, 'number': i + 1} for i, x in enumerate(steps)],
            'servings': servings.group(1) if servings else '', 'total_minutes': total_minutes, 'author': creator[:200], 'source_url': source,
            'tags': [], 'notes': '',
            'import': {'method': 'instagram_reel', 'status': 'awaiting_user_review',
                       'issues': warnings, 'raw_text': raw}}
