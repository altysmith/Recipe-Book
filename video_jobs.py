"""Small in-process import queue; results are private to a random browser token."""
from concurrent.futures import ThreadPoolExecutor
import copy
import secrets
import threading
import time

from video_import import Canceled, VideoError, import_video, reel_url

TTL = 30 * 60
_lock = threading.Lock()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='recipe-video')
_jobs = {}


def _expiry_loop():
    while True:
        time.sleep(60)
        with _lock: _prune()


threading.Thread(target=_expiry_loop, name='recipe-video-expiry', daemon=True).start()


def _prune():
    now = time.monotonic()
    for key, job in list(_jobs.items()):
        if job['state'] in ('completed', 'failed', 'canceled') and now - job['updated'] > TTL:
            del _jobs[key]


def _update(job, state, **values):
    with _lock:
        if job['cancel'].is_set(): state = 'canceled'; values = {}
        job.update(state=state, updated=time.monotonic(), **values)


def _run(job):
    try:
        if job['cancel'].is_set(): return
        result = import_video(job['url'], lambda state: _update(job, state), job['cancel'])
        _update(job, 'completed', result=result)
    except Canceled:
        _update(job, 'canceled')
    except (VideoError, ValueError) as exc:
        _update(job, 'failed', error=str(exc)[:300])
    except Exception:
        _update(job, 'failed', error='The video could not be processed. Try another public Reel.')


def create(url):
    url = reel_url(url)
    with _lock:
        _prune()
        if sum(j['state'] not in ('completed', 'failed', 'canceled') for j in _jobs.values()) >= 2:
            raise VideoError('Video importer is busy. Try again after the current imports finish.')
        job_id = secrets.token_urlsafe(24)
        token = secrets.token_urlsafe(32)
        job = {'id': job_id, 'token': token, 'url': url, 'state': 'queued',
               'updated': time.monotonic(), 'cancel': threading.Event()}
        _jobs[job_id] = job
        _executor.submit(_run, job)
        return {'job_id': job_id, 'token': token, 'state': 'queued'}


def get(job_id, token):
    with _lock:
        _prune()
        job = _jobs.get(job_id)
        if not job or not isinstance(token, str) or not secrets.compare_digest(job['token'], token):
            raise VideoError('Video import job was not found or has expired.')
        return copy.deepcopy({key: job[key] for key in ('state', 'result', 'error') if key in job})


def cancel(job_id, token):
    with _lock:
        job = _jobs.get(job_id)
        if not job or not isinstance(token, str) or not secrets.compare_digest(job['token'], token):
            raise VideoError('Video import job was not found or has expired.')
        job['cancel'].set()
        if job['state'] == 'queued': job['state'] = 'canceled'
        return {'state': job['state']}
