"""Bounded, local Instagram Reel extraction. No downloaded media is retained."""
import http.client
import ipaddress
import json
import os
from pathlib import Path
import re
import select
import shutil
import socket
import socketserver
import ssl
import subprocess
import tempfile
import threading
import time
from contextlib import contextmanager
from urllib.parse import urljoin, urlsplit, urlunsplit


def limit(name, default, low, high):
    try: return max(low, min(high, int(os.environ.get(name, default))))
    except ValueError: return default


MAX_BYTES = limit('RECIPE_VIDEO_MAX_BYTES', 80_000_000, 1_000_000, 200_000_000)
MAX_SECONDS = limit('RECIPE_VIDEO_MAX_SECONDS', 180, 15, 600)
MAX_FRAMES = limit('RECIPE_VIDEO_MAX_FRAMES', 16, 0, 40)
PROCESS_TIMEOUT = limit('RECIPE_VIDEO_PROCESS_TIMEOUT', 900, 60, 3600)


class VideoError(ValueError):
    pass


class Canceled(VideoError):
    pass


def health():
    model = os.environ.get('RECIPE_WHISPER_MODEL', '')
    def available(key, name): return bool(shutil.which(os.environ.get(key) or name))
    tools = {'yt_dlp': available('RECIPE_YTDLP', 'yt-dlp'),
             'ffmpeg': available('RECIPE_FFMPEG', 'ffmpeg'),
             'whisper': available('RECIPE_WHISPER_CLI', 'whisper-cli') and bool(model and Path(model).is_file()),
             'tesseract': available('RECIPE_TESSERACT', 'tesseract')}
    return {'ready': all(tools.values()), 'tools': tools}


def reel_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise VideoError('Paste a valid public Instagram Reel link.')
    try: p = urlsplit(value.strip())
    except ValueError: raise VideoError('Paste a valid public Instagram Reel link.') from None
    if (p.scheme != 'https' or p.hostname not in ('instagram.com', 'www.instagram.com')
            or p.port is not None or p.username or p.password or p.fragment
            or not re.fullmatch(r'/reel/[A-Za-z0-9_-]{5,64}/?', p.path)):
        raise VideoError('Only public HTTPS Instagram Reel links are supported.')
    # Share parameters are tracking data; the shortcode identifies the Reel.
    return urlunsplit(('https', 'www.instagram.com', p.path.rstrip('/') + '/', '', ''))


def public_host(host, port=443):
    try: addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError: raise VideoError('The video host could not be reached.') from None
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise VideoError('Private or local video addresses are blocked.')
    return addresses[0][4][0]


def media_target(value):
    try: p = urlsplit(value)
    except ValueError: raise VideoError('The video download address is invalid.') from None
    host = (p.hostname or '').lower()
    if (p.scheme != 'https' or p.username or p.password or p.port is not None
            or not (host in ('instagram.com', 'www.instagram.com', 'cdninstagram.com', 'fbcdn.net')
                    or host.endswith('.cdninstagram.com') or host.endswith('.fbcdn.net'))):
        raise VideoError('The video redirected to an unsupported host.')
    return p, host, public_host(host)


class SafeConnect(socketserver.BaseRequestHandler):
    """Tunnel only TLS to approved public Meta hosts, with DNS pinned per connection."""
    def handle(self):
        self.request.settimeout(10)
        line = bytearray()
        try:
            while not line.endswith(b'\r\n') and len(line) < 4096:
                chunk = self.request.recv(1)
                if not chunk: return
                line.extend(chunk)
            match = re.fullmatch(rb'CONNECT ([A-Za-z0-9.-]+):443 HTTP/1\.[01]\r\n', bytes(line))
            if not match:
                self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n'); return
            host = match.group(1).decode('ascii').lower()
            if not (host == 'instagram.com' or host.endswith('.instagram.com')
                    or host == 'cdninstagram.com' or host.endswith('.cdninstagram.com')
                    or host == 'fbcdn.net' or host.endswith('.fbcdn.net')):
                self.request.sendall(b'HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n'); return
            ip = public_host(host)
            # Consume CONNECT headers; never forward proxy headers to the destination.
            headers = bytearray()
            while not headers.endswith(b'\r\n\r\n') and len(headers) < 8192:
                chunk = self.request.recv(1)
                if not chunk: return
                headers.extend(chunk)
            if not headers.endswith(b'\r\n\r\n'): return
            with socket.create_connection((ip, 443), timeout=10) as upstream:
                self.request.sendall(b'HTTP/1.1 200 Connection Established\r\n\r\n')
                self.request.setblocking(False); upstream.setblocking(False)
                deadline = time.monotonic() + 65
                while time.monotonic() < deadline:
                    ready, _, _ = select.select([self.request, upstream], [], [], 1)
                    for source in ready:
                        data = source.recv(64 * 1024)
                        if not data: return
                        (upstream if source is self.request else self.request).sendall(data)
        except (OSError, ValueError, VideoError): return


class SafeProxy(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


@contextmanager
def metadata_proxy():
    with SafeProxy(('127.0.0.1', 0), SafeConnect) as proxy:
        worker = threading.Thread(target=proxy.serve_forever, daemon=True)
        worker.start()
        try: yield f'http://127.0.0.1:{proxy.server_address[1]}'
        finally: proxy.shutdown(); worker.join(timeout=2)


def checked_run(args, timeout, cancel=None, output_limit=2_000_000, failure='A video processing tool failed.'):
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    try: proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=flags)
    except FileNotFoundError: raise VideoError(f'{Path(args[0]).name} is not installed on the recipe server.') from None
    deadline = time.monotonic() + timeout
    try:
        while True:
            if cancel is not None and cancel.is_set(): raise Canceled('Video import canceled.')
            if time.monotonic() >= deadline: raise VideoError('Video processing timed out.')
            try:
                out, err = proc.communicate(timeout=.2)
                break
            except subprocess.TimeoutExpired: pass
    except (Canceled, VideoError):
        proc.kill(); proc.communicate()
        raise
    if len(out) > output_limit or len(err) > output_limit:
        raise VideoError('The video tool returned too much data.')
    if proc.returncode: raise VideoError(failure)
    return out.decode('utf-8', 'replace')


def metadata(url, cancel=None):
    executable = os.environ.get('RECIPE_YTDLP') or shutil.which('yt-dlp')
    if not executable: raise VideoError('Video importing needs yt-dlp installed on the server.')
    public_host('www.instagram.com')
    with metadata_proxy() as proxy:
        output = checked_run([executable, '--ignore-config', '--no-playlist', '--skip-download',
                              '--dump-single-json', '--no-warnings', '--socket-timeout', '15',
                              '--proxy', proxy, url], 60, cancel,
                             failure='Instagram prevented this video from being downloaded. Try another public Reel.')
    try: info = json.loads(output)
    except (ValueError, TypeError): raise VideoError('Instagram returned unexpected video information.') from None
    if not isinstance(info, dict) or info.get('_type') in ('playlist', 'url', 'url_transparent'):
        raise VideoError('This link did not resolve to a single video.')
    duration = info.get('duration')
    if not isinstance(duration, (int, float)) or duration <= 0 or duration > MAX_SECONDS:
        raise VideoError(f'Only videos with a known duration up to {MAX_SECONDS} seconds can be imported.')
    formats = info.get('formats') or [info]
    candidates = [f for f in formats if isinstance(f, dict) and isinstance(f.get('url'), str)
                  and f.get('protocol', 'https') in ('https', 'http')
                  and f.get('vcodec') != 'none' and f.get('ext') in ('mp4', 'mov')]
    candidates = [f for f in candidates if not f.get('filesize') or f['filesize'] <= MAX_BYTES]
    if not candidates: raise VideoError('No supported downloadable video format was available.')
    candidates.sort(key=lambda f: (min(f.get('height') or 0, 720), -(f.get('filesize') or 0)), reverse=True)
    media_target(candidates[0]['url'])
    return info, candidates[0]['url']


def download(url, target, cancel=None):
    deadline = time.monotonic() + 180
    for _ in range(4):
        p, host, ip = media_target(url)
        sock = socket.create_connection((ip, 443), timeout=15)
        conn = http.client.HTTPSConnection(host, timeout=15)
        try:
            conn.sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
            conn.request('GET', (p.path or '/') + ('?' + p.query if p.query else ''),
                         headers={'Host': host, 'User-Agent': 'Mozilla/5.0',
                                  'Referer': 'https://www.instagram.com/', 'Accept-Encoding': 'identity'})
            response = conn.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader('Location')
                if not location: raise VideoError('The video returned an invalid redirect.')
                url = urljoin(url, location)
                media_target(url)
                continue
            if response.status != 200:
                raise VideoError('Instagram prevented this video from being downloaded. Try another public Reel.')
            content_type = response.getheader('Content-Type', '').lower()
            if content_type and not (content_type.startswith('video/') or content_type.startswith('application/octet-stream')):
                raise VideoError('Instagram did not return a video file.')
            size = response.getheader('Content-Length')
            if size and int(size) > MAX_BYTES: raise VideoError('The video is too large to import.')
            total = 0
            with target.open('wb') as output:
                while chunk := response.read(64 * 1024):
                    if cancel is not None and cancel.is_set(): raise Canceled('Video import canceled.')
                    if time.monotonic() > deadline: raise VideoError('The video download timed out.')
                    total += len(chunk)
                    if total > MAX_BYTES: raise VideoError('The video is too large to import.')
                    output.write(chunk)
            return
        except (OSError, ValueError) as exc:
            if isinstance(exc, VideoError): raise
            raise VideoError('The video download failed. Try another public Reel.') from None
        finally: conn.close(); sock.close()
    raise VideoError('The video redirected too many times.')


def transcribe(video, folder, cancel=None):
    ffmpeg = os.environ.get('RECIPE_FFMPEG') or shutil.which('ffmpeg')
    whisper = os.environ.get('RECIPE_WHISPER_CLI') or shutil.which('whisper-cli')
    model = os.environ.get('RECIPE_WHISPER_MODEL', '')
    if not ffmpeg: raise VideoError('FFmpeg is not installed on the recipe server.')
    if not whisper or not model or not Path(model).is_file():
        raise VideoError('Local Whisper transcription is not configured on the recipe server.')
    audio = folder / 'audio.wav'
    checked_run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(video), '-vn', '-ac', '1', '-ar', '16000',
                 '-t', str(MAX_SECONDS), '-f', 'wav', str(audio)], 120, cancel,
                failure='The video audio could not be decoded.')
    if not audio.is_file() or audio.stat().st_size < 1024:
        return '', 'No usable speech audio was found.'
    outbase = folder / 'transcript'
    checked_run([whisper, '-m', model, '-f', str(audio), '-l', 'en', '-otxt', '-osrt', '-of', str(outbase)],
                PROCESS_TIMEOUT, cancel, failure='Local speech transcription failed.')
    transcript_file = outbase.with_suffix('.txt')
    if not transcript_file.is_file(): raise VideoError('Local speech transcription returned no transcript file.')
    transcript = transcript_file.read_text(encoding='utf-8', errors='replace').strip()
    return transcript[:100_000], None if transcript else 'No speech was detected in the video.'


def screen_text(video, folder, cancel=None):
    ffmpeg = os.environ.get('RECIPE_FFMPEG') or shutil.which('ffmpeg')
    tesseract = os.environ.get('RECIPE_TESSERACT') or shutil.which('tesseract')
    if not tesseract: return '', 'On-screen text was skipped because Tesseract is unavailable.'
    if not ffmpeg or not MAX_FRAMES: return '', 'On-screen text was skipped.'
    frames = folder / 'frames'; frames.mkdir()
    try:
        checked_run([ffmpeg, '-nostdin', '-v', 'error', '-i', str(video), '-vf', 'fps=1/10,scale=640:-1',
                     '-frames:v', str(MAX_FRAMES), str(frames / '%03d.jpg')], 120, cancel,
                    failure='Video frames could not be decoded.')
    except Canceled: raise
    except VideoError: return '', 'On-screen text could not be read from this video.'
    found = []; seen = set(); warnings = []
    for frame in sorted(frames.glob('*.jpg')):
        try:
            raw = checked_run([tesseract, str(frame), 'stdout', '-l', 'eng', '--psm', '11'], 20, cancel)
        except Canceled: raise
        except VideoError:
            warnings.append('Some on-screen text could not be read.'); continue
        for line in raw.splitlines():
            line = ' '.join(line.split())
            key = re.sub(r'\W+', '', line).casefold()
            if len(key) >= 4 and key not in seen:
                seen.add(key); found.append(line)
    return '\n'.join(found[:200]), warnings[0] if warnings else (None if found else 'No on-screen text was detected.')


def import_video(url, progress, cancel=None):
    source = reel_url(url)
    with tempfile.TemporaryDirectory(prefix='recipe-video-') as tmp:
        folder = Path(tmp)
        progress('downloading')
        info, media = metadata(source, cancel)
        caption = str(info.get('description') or '')[:50_000]
        from video_recipe import amount, explicit_lines
        _, cap_ingredients, cap_steps = explicit_lines(caption)
        if cap_ingredients and cap_steps and all(amount(line) for line in cap_ingredients):
            progress('interpreting')
            from video_recipe import interpret
            return interpret(source, info, caption, '', '',
                             ['Audio and on-screen text were skipped because the caption contained ingredients and directions.'])
        video = folder / 'video.mp4'
        download(media, video, cancel)
        progress('transcribing')
        transcript, speech_warning = transcribe(video, folder, cancel)
        progress('extracting_text')
        onscreen, text_warning = screen_text(video, folder, cancel)
        progress('interpreting')
        from video_recipe import interpret
        timed = folder.joinpath('transcript.srt')
        return interpret(source, info, caption, transcript, onscreen,
                         [x for x in (speech_warning, text_warning) if x],
                         timed.read_text(encoding='utf-8', errors='replace')[:120_000] if timed.is_file() else None)
