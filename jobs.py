"""Local background jobs; PDFs expire after 24 hours, logs remain available meanwhile."""
import json
import logging
import shutil
import threading
import time
import traceback
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from watermark import process

ROOT = Path(__file__).resolve().parent / 'output' / 'jobs'
EXECUTOR = ThreadPoolExecutor(max_workers=1)
ENGINE_LOCK = threading.Lock()
LOCK = threading.RLock()
JOBS = {}
TTL = 24 * 3600


def cleanup():
    ROOT.mkdir(parents=True, exist_ok=True)
    with LOCK:
        active = {key for key, value in JOBS.items() if value['state'] in ('queued', 'running')}
        for folder in ROOT.iterdir():
            if folder.is_dir() and folder.name not in active and time.time() - folder.stat().st_mtime > TTL:
                shutil.rmtree(folder)
                JOBS.pop(folder.name, None)


def event(job, kind, **details):
    record = dict(time=datetime.now(ZoneInfo('Asia/Ho_Chi_Minh')).isoformat(), event=kind, **details)
    with (ROOT / job['id'] / 'progress.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + '\n')


def snapshot(key):
    with LOCK:
        job = JOBS.get(key)
        return json.loads(json.dumps(job)) if job else None


def submit(files, image, size, opts, converter=None):
    cleanup()
    key = uuid.uuid4().hex
    folder = ROOT / key
    folder.mkdir()
    job = dict(id=key, state='queued', total=len(files), completed=0, page=0, pages=0,
               current='', reports=[], success=0, failed=0, error=None, tool='word' if converter else 'watermark')
    event(job, 'queued', total=len(files))
    with LOCK:
        JOBS[key] = job
    EXECUTOR.submit(run, job, files, image, size, opts, converter)
    return key


def run(job, files, image, size, opts, converter=None):
    folder = ROOT / job['id']
    try:
        with LOCK:
            job['state'] = 'running'
        event(job, 'started')
        used = set()
        with zipfile.ZipFile(folder / 'result.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, raw in files:
                with LOCK:
                    job.update(current=name, page=0, pages=0)
                event(job, 'file_started', file=name)
                def progress(page, pages):
                    with LOCK:
                        job.update(page=page, pages=pages)
                    event(job, 'page', file=name, page=page, pages=pages)
                try:
                    if converter:
                        result, pages = converter(raw, name)
                        progress(pages, pages)
                        desired = Path(name).stem + '.pdf'
                    else:
                        if not name.lower().endswith('.pdf'):
                            raise ValueError('File không có phần mở rộng PDF.')
                        with ENGINE_LOCK:
                            result, pages = process(raw, image, size, opts, progress=progress)
                        desired = opts['prefix'] + name
                    candidate, index = desired, 2
                    while candidate.casefold() in used:
                        candidate = f'{Path(desired).stem} ({index}).pdf'
                        index += 1
                    used.add(candidate.casefold())
                    archive.writestr(candidate, result)
                    report = dict(file=name, output=candidate, status='ok', pages=pages)
                    event(job, 'file_completed', **report)
                except Exception as exc:
                    report = dict(file=name, status='error', error=str(exc) if isinstance(exc, ValueError) else 'Không xử lý được file PDF này.')
                    event(job, 'file_error', **report, traceback=traceback.format_exc())
                with LOCK:
                    job['reports'].append(report)
                    job['completed'] += 1
                    job['success' if report['status'] == 'ok' else 'failed'] += 1
            archive.writestr('bao-cao.json', json.dumps(job['reports'], ensure_ascii=False, indent=2))
            event(job, 'completed', success=job['success'], failed=job['failed'])
            archive.write(folder / 'progress.jsonl', 'tien-trinh.jsonl')
        with LOCK:
            job['state'] = 'completed'
    except Exception:
        logging.exception('Background job %s failed', job['id'])
        try:
            event(job, 'job_error', traceback=traceback.format_exc())
        finally:
            with LOCK:
                job.update(state='error', error='Lượt xử lý bị gián đoạn. Xem log để kiểm tra và chạy lại file gốc.')
