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
            for duration in (video_import.MAX_SECONDS + 1, None):
                with patch('video_import.checked_run', return_value=json.dumps({'duration': duration})):
                    with self.assertRaises(video_import.VideoError): video_import.metadata(URL)
            oversized={'duration': 30, 'formats':[{'url':'https://video.cdninstagram.com/x.mp4',
                       'ext':'mp4', 'protocol':'https', 'filesize':video_import.MAX_BYTES + 1}]}
            with patch('video_import.checked_run', return_value=json.dumps(oversized)):
                with self.assertRaises(video_import.VideoError): video_import.metadata(URL)

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
              patch('video_import.transcribe', return_value=('Chop the garlic. Add olive oil. Cook in a pan.', None)),
              patch('video_import.screen_text', return_value=('3 cloves garlic\n2 tbsp olive oil', None))):
            draft=video_import.import_video(URL, stages.append)
        self.assertEqual([item['text'] for item in draft['ingredients']], ['3 cloves garlic', '2 tbsp olive oil'])
        self.assertIn('Audio transcript\nChop the garlic.', draft['import']['raw_text'])
        self.assertIn('On-screen text\n3 cloves garlic', draft['import']['raw_text'])
        self.assertEqual(stages, ['downloading', 'transcribing', 'extracting_text', 'interpreting'])
        self.assertFalse(locations[0].parent.exists())

    def test_incomplete_caption_still_reads_video_for_amounts(self):
        info={**INFO, 'description':'Garlic Sauce\nIngredients:\ngarlic\nDirections:\nAdd garlic to the pan.'}
        with (patch('video_import.metadata', return_value=(info, 'https://video.cdninstagram.com/x.mp4')),
              patch('video_import.download') as download,
              patch('video_import.transcribe', return_value=('Add garlic to the pan.', None)) as transcribe,
              patch('video_import.screen_text', return_value=('3 cloves garlic', None)) as ocr):
            draft=video_import.import_video(URL, lambda stage: None)
        download.assert_called_once(); transcribe.assert_called_once(); ocr.assert_called_once()
        self.assertEqual([item['text'] for item in draft['ingredients']], ['3 cloves garlic'])

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
