import json
import socket
import sys
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import video_import
import video_jobs
from video_recipe import interpret

URL = 'https://www.instagram.com/reel/AbCd12345/'
INFO = {'title': 'Chicken pasta', 'uploader': 'cookalice', 'duration': 42}


class VideoImportTests(unittest.TestCase):
    def test_reel_normalization_and_rejections(self):
        self.assertEqual(video_import.reel_url(URL + '?igsh=abc'), URL)
        for bad in ('http://www.instagram.com/reel/AbCd12345/',
                    'https://www.instagram.com.evil.com/reel/AbCd12345/',
                    'https://127.0.0.1/reel/AbCd12345/',
                    'https://www.instagram.com/p/AbCd12345/',
                    'https://www.instagram.com/reel/AbCd12345/../admin', 'x' * 3000):
            with self.subTest(bad=bad), self.assertRaises(video_import.VideoError):
                video_import.reel_url(bad)

    def test_media_host_and_private_dns(self):
        with patch('video_import.public_host', return_value='1.2.3.4'):
            for bad in ('https://127.0.0.1/x', 'https://evil.com/x', 'https://fbcdn.net.evil.com/x'):
                with self.assertRaises(video_import.VideoError): video_import.media_target(bad)
        with patch('video_import.socket.getaddrinfo', return_value=[(None, None, None, None, ('10.0.0.1', 443))]):
            with self.assertRaises(video_import.VideoError): video_import.public_host('www.instagram.com')

    def test_metadata_proxy_rejects_private_and_unapproved_connect(self):
        with video_import.metadata_proxy() as proxy:
            host, port=video_import.urlsplit(proxy).hostname, video_import.urlsplit(proxy).port
            for target in ('127.0.0.1:443', 'evil.example:443', 'www.instagram.com:80'):
                with socket.create_connection((host, port), timeout=2) as client:
                    client.sendall(f'CONNECT {target} HTTP/1.1\r\n\r\n'.encode())
                    self.assertIn(b'403', client.recv(100))

    def test_metadata_limits_and_unexpected_output(self):
        with patch('video_import.shutil.which', return_value='yt-dlp'), patch('video_import.public_host'):
            with patch('video_import.checked_run', return_value='not json'):
                with self.assertRaises(video_import.VideoError): video_import.metadata(URL)
            candidate={'url':'https://video.cdninstagram.com/x.mp4','ext':'mp4','protocol':'https'}
            with patch('video_import.checked_run', return_value=json.dumps({'duration': video_import.MAX_SECONDS + 1,'formats':[candidate]})):
                with self.assertRaisesRegex(video_import.VideoError, 'import limit'): video_import.metadata(URL)
            with patch('video_import.checked_run', return_value=json.dumps({'duration': None,'formats':[candidate]})):
                self.assertIsNone(video_import.metadata(URL)[0]['duration'])
            oversized={'duration': 30, 'formats':[{'url':'https://video.cdninstagram.com/x.mp4',
                       'ext':'mp4', 'protocol':'https', 'filesize':video_import.MAX_BYTES + 1}]}
            with patch('video_import.checked_run', return_value=json.dumps(oversized)):
                with self.assertRaises(video_import.VideoError): video_import.metadata(URL)

    def test_progressive_video_preferred_over_video_only_dash(self):
        formats = [
            {'url': 'https://video.cdninstagram.com/silent.mp4', 'ext': 'mp4',
             'protocol': 'https', 'height': 2560, 'acodec': 'none'},
            {'url': 'https://video.cdninstagram.com/playable.mp4', 'ext': 'mp4',
             'protocol': 'https', 'height': None, 'acodec': None},
        ]
        with (patch('video_import.shutil.which', return_value='yt-dlp'),
              patch('video_import.public_host', return_value='1.2.3.4'),
              patch('video_import.checked_run', return_value=json.dumps({'formats': formats}))):
            self.assertEqual(video_import.metadata(URL)[1], formats[1]['url'])

    def test_audio_probe_and_companion_selection(self):
        with (patch('video_import.shutil.which', return_value='ffprobe'),
              patch('video_import.checked_run', return_value=json.dumps({'streams': []}))):
            self.assertFalse(video_import.has_audio(Path('video.mp4')))
        with (patch('video_import.shutil.which', return_value='ffprobe'),
              patch('video_import.checked_run', return_value=json.dumps({'streams': [{'index': 1}]}))):
            self.assertTrue(video_import.has_audio(Path('video.mp4')))
        info = {'formats': [{'url': 'https://video.cdninstagram.com/audio.m4a', 'ext': 'm4a',
                            'protocol': 'https', 'vcodec': 'none', 'acodec': 'mp4a.40.5', 'filesize': 100}]}
        with patch('video_import.public_host', return_value='1.2.3.4'):
            self.assertIsNone(video_import.companion_audio(info, 99))
            self.assertEqual(video_import.companion_audio(info, 100), info['formats'][0]['url'])

    def test_downloaded_duration_is_verified(self):
        with patch('video_import.shutil.which', return_value='ffprobe'):
            for payload in ({'format':{'duration':'42.5'},'streams':[{'duration':'N/A'}]},
                            {'format':{},'streams':[{'duration':'42.5'}]}):
                with patch('video_import.checked_run', return_value=json.dumps(payload)):
                    self.assertEqual(video_import.verify_duration(Path('video.mp4')),42.5)
            with patch('video_import.checked_run', return_value=json.dumps({'format':{'duration':str(video_import.MAX_SECONDS + 1)}})):
                with self.assertRaisesRegex(video_import.VideoError, 'import limit'):
                    video_import.verify_duration(Path('video.mp4'))
            with patch('video_import.checked_run', return_value='{}'):
                with self.assertRaisesRegex(video_import.VideoError, 'could not be verified'):
                    video_import.verify_duration(Path('video.mp4'))
        with patch('video_import.shutil.which', return_value=None):
            with self.assertRaisesRegex(video_import.VideoError, 'FFprobe'):
                video_import.verify_duration(Path('video.mp4'))

    def test_process_failure_and_timeout(self):
        with self.assertRaises(video_import.VideoError):
            video_import.checked_run([sys.executable, '-c', 'raise SystemExit(2)'], 5)
        with self.assertRaisesRegex(video_import.VideoError, 'timed out'):
            video_import.checked_run([sys.executable, '-c', 'import time;time.sleep(5)'], .1)

    def test_transcription_missing_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch('video_import.shutil.which', side_effect=lambda name: '/fake/ffmpeg' if name == 'ffmpeg' else None):
            with self.assertRaisesRegex(video_import.VideoError, 'Whisper'):
                video_import.transcribe(Path(tmp) / 'video.mp4', Path(tmp))

    def test_transcription_output_and_invalid_audio(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp); model=folder/'tiny.bin'; model.write_bytes(b'model')
            def fake_run(args, *unused, **kwargs):
                if args[0]=='ffmpeg': (folder/'audio.wav').write_bytes(b'0'*2048)
                else: (folder/'transcript.txt').write_text('Add 2 tbsp oil.', encoding='utf-8')
                return ''
            with (patch.dict(video_import.os.environ, {'RECIPE_WHISPER_MODEL':str(model)}),
                  patch('video_import.shutil.which', side_effect=lambda name:name),
                  patch('video_import.checked_run', side_effect=fake_run)):
                transcript, warning=video_import.transcribe(folder/'video.mp4', folder)
            self.assertEqual(transcript, 'Add 2 tbsp oil.')
            self.assertIsNone(warning)
            (folder/'audio.wav').unlink(); (folder/'transcript.txt').unlink()
            with (patch.dict(video_import.os.environ, {'RECIPE_WHISPER_MODEL':str(model)}),
                  patch('video_import.shutil.which', side_effect=lambda name:name),
                  patch('video_import.checked_run', side_effect=lambda *a, **k: (_ for _ in ()).throw(video_import.VideoError('The video audio could not be decoded.')))):
                with self.assertRaisesRegex(video_import.VideoError, 'audio could not be decoded'):
                    video_import.transcribe(folder/'video.mp4', folder)

    def test_ocr_deduplicates_and_missing_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            with patch('video_import.shutil.which', return_value=None):
                self.assertIn('skipped', video_import.screen_text(folder/'video.mp4', folder)[1])
            def fake_run(args, *unused, **kwargs):
                if 'ffmpeg' in args[0]:
                    (folder/'frames'/'001.jpg').write_bytes(b'jpeg')
                    (folder/'frames'/'002.jpg').write_bytes(b'jpeg')
                    return ''
                return '2 tbsp olive oil\n'
            with patch('video_import.shutil.which', side_effect=lambda name: name), patch('video_import.checked_run', side_effect=fake_run):
                text, warning=video_import.screen_text(folder/'video.mp4', folder)
            self.assertEqual(text, '2 tbsp olive oil')
            self.assertIsNone(warning)

    def test_complete_caption_and_review(self):
        result = interpret(URL, INFO, 'Chicken pasta\nIngredients:\n2 tbsp olive oil\n1 cup pasta\nDirections:\nBoil pasta.\nAdd olive oil.', '', '')
        self.assertEqual(result['ingredients'][0]['text'], '2 tbsp olive oil')
        self.assertEqual(len(result['instructions']), 2)
        self.assertEqual(result['author'], 'cookalice')
        self.assertEqual(result['source_url'], URL)
        self.assertEqual(result['import']['status'], 'awaiting_user_review')

    def test_visual_amount_combines_and_conflict_warns(self):
        result = interpret(URL, INFO, '', 'Add olive oil. Cook the chicken.', '2 tbsp olive oil')
        self.assertEqual(sum(x['text'] == '2 tbsp olive oil' for x in result['ingredients']), 1)
        self.assertIn('chicken', [x['text'] for x in result['ingredients']])
        result = interpret(URL, INFO, '', 'Add 2 tsp garlic powder.', '2 tbsp garlic powder')
        self.assertTrue(any('differs' in w for w in result['import']['issues']))
        self.assertIn('2 tbsp garlic powder', result['import']['raw_text'])

    def test_full_caption_preserves_ranges_and_ignores_spoken_fragments(self):
        caption = ('Roasted Red Pepper Soup!\nIngredients:\n'
                   '- 3 red bell peppers (Cut in half)\n'
                   '- ~4 lbs tomatoes (2 large hot house, 2 Roma - use whatever combo you like)\n'
                   '- 2 onions, halved\n- 2 heads of garlic\n'
                   '- 2-4 tbsp Olive or avocado oil\n'
                   '- ½ tsp each dried basil, dried oregano, dried thyme, chili flakes and paprika\n'
                   '- Salt & pepper, to taste\n- Pinch of brown sugar\n'
                   '- 1 tbsp balsamic vinegar\n- 2–3 cups vegetable broth\n'
                   'Instructions:\n1. Preheat oven to 400°F\n2. Roast for 40–50 minutes.')
        transcript = ('Today we are making a roasted garlic red pepper soup. '
                      'Toss onion and garlic onto a sheet. Add a pinch of brown sugar and some broth.')
        result = interpret(URL, INFO, caption, transcript, '')
        lines = [item['text'] for item in result['ingredients']]
        self.assertEqual(len(lines), 10)
        self.assertIn('~4 lbs tomatoes (2 large hot house, 2 Roma - use whatever combo you like)', lines)
        self.assertIn('2-4 tbsp Olive or avocado oil', lines)
        self.assertIn('2–3 cups vegetable broth', lines)
        self.assertFalse(any('soup' in line for line in lines))

    def test_vague_amount_and_nonrecipe(self):
        result = interpret(URL, INFO, '', 'Add some parmesan. Stir.', '')
        self.assertTrue(any('not specified' in w for w in result['import']['issues']))
        with self.assertRaises(ValueError): interpret(URL, INFO, '', 'Follow me for more.', '')

    def test_caption_skips_transcription_and_cleans_media(self):
        caption = 'Pasta\nIngredients:\n1 cup pasta\nDirections:\nBoil pasta.'
        with (patch('video_import.metadata', return_value=({'description': caption, **INFO}, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download') as download,
              patch('video_import.transcribe') as transcribe,
              patch('video_import.screen_text', return_value=('', None))):
            result = video_import.import_video(URL, lambda stage: None)
            transcribe.assert_not_called()
            download.assert_not_called()
            self.assertEqual(result['title'], 'Pasta')

    def test_full_pipeline_uses_visual_only_quantities(self):
        locations=[]; stages=[]
        def fake_download(url, target, cancel):
            locations.append(target); target.write_bytes(b'video fixture')
        with (patch('video_import.metadata', return_value=(INFO, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download', side_effect=fake_download),
              patch('video_import.verify_duration', return_value=42.0) as probe,
              patch('video_import.has_audio', return_value=True),
              patch('video_import.transcribe', return_value=('Chop the garlic. Add olive oil. Cook in a pan.', None)),
              patch('video_import.screen_text', return_value=('3 cloves garlic\n2 tbsp olive oil', None))):
            draft=video_import.import_video(URL, stages.append)
        self.assertEqual([item['text'] for item in draft['ingredients']], ['3 cloves garlic', '2 tbsp olive oil'])
        self.assertIn('Audio transcript\nChop the garlic.', draft['import']['raw_text'])
        self.assertIn('On-screen text\n3 cloves garlic', draft['import']['raw_text'])
        self.assertEqual(stages, ['downloading', 'transcribing', 'extracting_text', 'interpreting'])
        probe.assert_called_once()
        self.assertFalse(locations[0].parent.exists())

    def test_incomplete_caption_still_reads_video_for_amounts(self):
        info={**INFO, 'description':'Garlic Sauce\nIngredients:\ngarlic\nDirections:\nAdd garlic to the pan.'}
        with (patch('video_import.metadata', return_value=(info, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download') as download,
              patch('video_import.verify_duration', return_value=42.0),
              patch('video_import.has_audio', return_value=True),
              patch('video_import.transcribe', return_value=('Add garlic to the pan.', None)) as transcribe,
              patch('video_import.screen_text', return_value=('3 cloves garlic', None)) as ocr):
            draft=video_import.import_video(URL, lambda stage: None)
        download.assert_called_once(); transcribe.assert_called_once(); ocr.assert_called_once()
        self.assertEqual([item['text'] for item in draft['ingredients']], ['3 cloves garlic'])

    def test_unknown_metadata_duration_uses_probe_before_speech(self):
        info={**INFO, 'duration':None}
        holder=[]
        def fake_download(url, target, cancel):
            holder.append(target); target.write_bytes(b'bounded video')
        with (patch('video_import.metadata', return_value=(info, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download', side_effect=fake_download),
              patch('video_import.verify_duration', return_value=42.0) as probe,
              patch('video_import.has_audio', return_value=True),
              patch('video_import.transcribe', return_value=('Add 2 tbsp olive oil. Stir.', None)) as speech,
              patch('video_import.screen_text', return_value=('', None))):
            draft=video_import.import_video(URL, lambda stage: None)
        self.assertEqual(draft['ingredients'][0]['text'],'2 tbsp olive oil')
        probe.assert_called_once(); speech.assert_called_once()
        self.assertFalse(holder[0].parent.exists())

    def test_separate_audio_is_downloaded_within_total_limit(self):
        audio = 'https://video.cdninstagram.com/speech.m4a'
        info = {**INFO, 'formats': [{'url': audio, 'ext': 'm4a', 'protocol': 'https',
                                    'vcodec': 'none', 'acodec': 'mp4a.40.5', 'filesize': 100}]}
        calls = []
        def fake_download(url, target, cancel, max_bytes=None):
            calls.append((url, target, max_bytes)); target.write_bytes(b'fixture')
        with (patch('video_import.metadata', return_value=(info, 'https://video.cdninstagram.com/silent.mp4')),
              patch('video_import.download', side_effect=fake_download),
              patch('video_import.verify_duration', return_value=25.0) as duration,
              patch('video_import.has_audio', return_value=False),
              patch('video_import.public_host', return_value='1.2.3.4'),
              patch('video_import.transcribe', return_value=('Add 2 tbsp olive oil. Stir.', None)) as speech,
              patch('video_import.screen_text', return_value=('', None))):
            draft = video_import.import_video(URL, lambda stage: None)
        self.assertEqual(draft['ingredients'][0]['text'], '2 tbsp olive oil')
        self.assertEqual(calls[1][0], audio)
        self.assertEqual(calls[1][2], video_import.MAX_BYTES - len(b'fixture'))
        self.assertEqual(speech.call_args.args[0], calls[1][1])
        self.assertEqual(duration.call_count, 2)
        self.assertFalse(calls[0][1].parent.exists())

    def test_missing_audio_uses_caption_and_onscreen_evidence(self):
        info = {**INFO, 'description': 'Add olive oil and stir.'}
        def fake_download(url, target, cancel): target.write_bytes(b'video fixture')
        with (patch('video_import.metadata', return_value=(info, 'https://video.cdninstagram.com/silent.mp4')),
              patch('video_import.download', side_effect=fake_download),
              patch('video_import.verify_duration', return_value=25.0),
              patch('video_import.has_audio', return_value=False),
              patch('video_import.transcribe') as speech,
              patch('video_import.screen_text', return_value=('2 tbsp olive oil', None))):
            draft = video_import.import_video(URL, lambda stage: None)
        speech.assert_not_called()
        self.assertEqual(draft['ingredients'][0]['text'], '2 tbsp olive oil')
        self.assertTrue(any('No downloadable audio stream' in issue for issue in draft['import']['issues']))

    def test_oversized_duration_stops_before_transcription(self):
        holder=[]
        def fake_download(url, target, cancel):
            holder.append(target); target.write_bytes(b'bounded video')
        with (patch('video_import.metadata', return_value=({**INFO, 'duration':None}, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download', side_effect=fake_download),
              patch('video_import.verify_duration', side_effect=video_import.VideoError('This video is 200 seconds long; the import limit is 180 seconds.')),
              patch('video_import.transcribe') as speech):
            with self.assertRaisesRegex(video_import.VideoError, '200 seconds'):
                video_import.import_video(URL, lambda stage: None)
        speech.assert_not_called()
        self.assertFalse(holder[0].parent.exists())

    def test_temp_media_removed_after_failure(self):
        holder=[]
        def fail_download(url, target, cancel):
            holder.append(target)
            target.write_bytes(b'partial video')
            raise video_import.VideoError('download failed')
        with (patch('video_import.metadata', return_value=(INFO, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download', side_effect=fail_download)):
            with self.assertRaises(video_import.VideoError): video_import.import_video(URL, lambda stage: None)
        self.assertFalse(holder[0].parent.exists())

    def test_job_token_and_no_save(self):
        with patch('video_jobs.import_video', return_value=interpret(URL, INFO, 'Pasta\nIngredients:\n1 cup pasta\nDirections:\nBoil pasta.', '', '')):
            created = video_jobs.create(URL)
            with self.assertRaises(video_import.VideoError): video_jobs.get(created['job_id'], 'wrong')
            for _ in range(100):
                result = video_jobs.get(created['job_id'], created['token'])
                if result['state'] == 'completed': break
                time.sleep(.01)
            self.assertEqual(result['state'], 'completed')
            self.assertNotIn('id', result['result'])


if __name__ == '__main__': unittest.main()
