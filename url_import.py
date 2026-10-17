"""Fetch public recipe pages without executing website code or following private redirects."""
import base64
import io
import warnings
import http.client
import ipaddress
import socket
import ssl
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin

def public_target(url):
    if not isinstance(url, str) or len(url)>4000:
        raise ValueError('Enter a valid public recipe URL.')
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.port not in (None,80,443):
        raise ValueError('Use a public http or https recipe URL without login details or custom ports.')
    host=p.hostname.encode('idna').decode()
    addresses=socket.getaddrinfo(host,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Only public websites can be imported; local and private addresses are not supported.')
    return p,host,addresses[0][4][0]

def fetch_page(url, image=False):
    for _ in range(5):
        p,host,ip=public_target(url)
        port=p.port or (443 if p.scheme=='https' else 80)
        conn=http.client.HTTPConnection(host,port,timeout=8)
        # Connect to the already-validated address, preventing DNS rebinding.
        sock=socket.create_connection((ip,port),timeout=8)
        try:
            if p.scheme=='https': sock=ssl.create_default_context().wrap_socket(sock,server_hostname=host)
            conn.sock=sock
            conn.request('GET',(p.path or '/')+('?' + p.query if p.query else ''),headers={'Host':p.netloc,'User-Agent':'LittleRecipeBox/1.0','Accept':'image/*' if image else 'text/html','Accept-Encoding':'identity'})
            response=conn.getresponse()
            if response.status in (301,302,303,307,308):
                location=response.getheader('Location')
                if not location: raise ValueError('The website returned an incomplete redirect.')
                url=urljoin(url,location);continue
            if response.status!=200: raise ValueError('This website could not be read. Try its print recipe page or paste the recipe text.')
            if image:
                if not response.getheader('Content-Type','').lower().startswith('image/'):
                    raise ValueError('This link is not an image.')
                data=response.read(8_000_001)
                if len(data)>8_000_000: raise ValueError('Photo is too large.')
                return data,url
            if 'html' not in response.getheader('Content-Type','').lower(): raise ValueError('This link is not a web page. Use PDF upload for PDF links.')
            data=response.read(3_000_001)
            if len(data)>3_000_000: raise ValueError('This page is too large. Try its print recipe page or paste the text.')
            charset=re.search(r'charset=([\w-]+)',response.getheader('Content-Type',''))
            return data.decode(charset.group(1) if charset else 'utf-8',errors='replace'),url
        finally:
            conn.close();sock.close()
    raise ValueError('Too many website redirects. Paste the recipe instead.')

class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.scripts=[];self.parts=[];self.capture=False;self.skip=0;self.buffer=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):
            self.skip+=1
            if tag=='script' and dict(attrs).get('type','').lower()=='application/ld+json': self.capture=True;self.buffer=[]
        if tag in ('p','div','li','h1','h2','h3','br'): self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag=='script' and self.capture:
            self.scripts.append(''.join(self.buffer));self.capture=False
        if tag in ('script','style','noscript'): self.skip=max(0,self.skip-1)
    def handle_data(self,data):
        if self.capture:self.buffer.append(data)
        elif not self.skip:self.parts.append(data)

def clean(value):
    if not isinstance(value,(str,int,float)):return ''
    p=Page();p.feed(str(value));return ' '.join(''.join(p.parts).split())

def lines(value):
    if isinstance(value,list):return [line for item in value for line in lines(item)]
    if isinstance(value,dict):
        nested=value.get('itemListElement') or value.get('item')
        if nested:return lines(nested)
        return lines(value.get('text') or value.get('name') or '')
    if isinstance(value,str):return [clean(x) for x in value.splitlines() if clean(x)]
    return []

def recipes_in(value):
    if isinstance(value,list):
        for v in value:yield from recipes_in(v)
    elif isinstance(value,dict):
        types=value.get('@type',[])
        if isinstance(types,str):types=[types]
        if any(t.rsplit('/',1)[-1]=='Recipe' for t in types if isinstance(t,str)):yield value
        else:
            for v in value.values():yield from recipes_in(v)

def minutes(value):
    m=re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?',str(value))
    return int(m[1] or 0)*60+int(m[2] or 0) if m and any(m.groups()) else None

def parse_page(html,url):
    page=Page();page.feed(html)
    found=[]
    for script in page.scripts:
        try:found.extend(recipes_in(json.loads(script)))
        except (ValueError,RecursionError):continue
    if not found:raise ValueError('No structured recipe found on this page. Try its print recipe link, or copy and paste the recipe below.')
    result=[];seen=set()
    for recipe in found:
        signature=json.dumps(recipe,sort_keys=True)
        if signature in seen:continue
        seen.add(signature)
        authors=recipe.get('author',[])
        if not isinstance(authors,list):authors=[authors]
        ingredients=lines(recipe.get('recipeIngredient',[]))
        steps=lines(recipe.get('recipeInstructions',[]))
        issues=['Imported from a website. Review quantities, steps, and servings before saving.']
        if not ingredients:issues.append('Ingredients were not found. Add them from the source before saving.')
        result.append({'title':clean(recipe.get('name',''))[:200], 'source_url':url,
            'author':', '.join(clean(a.get('name','') if isinstance(a,dict) else a) for a in authors),
            'ingredients':[{'text':x} for x in ingredients], 'instructions':[{'text':x,'number':i+1} for i,x in enumerate(steps)],
            'servings':'; '.join(lines(recipe.get('recipeYield',''))), 'total_minutes':minutes(recipe.get('totalTime')),
            'tags':lines(recipe.get('recipeCategory',[])), 'notes':'',
            'image_url':image_url(recipe.get('image'),url),
            'import':{'status':'awaiting_user_review','method':'website_jsonld','issues':issues,'raw_text':json.dumps(recipe,ensure_ascii=False,indent=2)}})
    return result[:20]

def import_url(url):
    try:html,final=fetch_page(url);return {'candidates':parse_page(html,final)}
    except (OSError,http.client.HTTPException,UnicodeError) as e:raise ValueError('Could not reach this website. Try again, use its print recipe link, or paste the recipe text.') from e

def image_url(value, base):
    if isinstance(value, list):
        return next((url for item in value if (url := image_url(item, base))), None)
    if isinstance(value, dict):
        return image_url(value.get('contentUrl') or value.get('url'), base)
    if isinstance(value, str) and value.strip():
        url = urljoin(base, value.strip())
        if urlsplit(url).scheme in ('http', 'https'): return url
    return None

def import_photo(url):
    try:
        from PIL import Image, ImageOps
        data, final = fetch_page(url, image=True)
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.width * source.height > 20_000_000:
                    raise ValueError('Photo dimensions are too large.')
                photo = ImageOps.exif_transpose(source)
                photo.thumbnail((1400, 1400))
                photo = photo.convert('RGB')
                output = io.BytesIO()
                photo.save(output, 'JPEG', quality=82)
        return {'photo':'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode()}
    except (ValueError, OSError, http.client.HTTPException, Image.DecompressionBombWarning, Image.DecompressionBombError):
        return {'photo':None, 'warning':'The website photo could not be downloaded. You can add one manually.'}
