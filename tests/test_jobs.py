"""Behavioral checks for background progress and downloadable diagnostics."""
import io
import json
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from werkzeug.datastructures import MultiDict
from app import app
import jobs
from test_watermark import pdf_bytes, logo_bytes


class JobTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(jobs, 'ROOT', Path(self.temp.name))
        self.root_patch.start()
        self.client = app.test_client()
        self.keys = []

    def tearDown(self):
        for key in self.keys:
            self.wait(key)
            with jobs.LOCK:
                jobs.JOBS.pop(key, None)
        self.root_patch.stop()
        self.temp.cleanup()

    def submit(self, files):
        data = MultiDict([('watermark', (io.BytesIO(logo_bytes()), 'logo.png'))])
        for name, raw in files:
            data.add('pdfs', (io.BytesIO(raw), name))
        response = self.client.post('/api/jobs', data=data)
        self.assertEqual(response.status_code, 202)
        key = response.json['id']
        self.keys.append(key)
        return key

    def wait(self, key):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            state = self.client.get('/api/jobs/' + key).json
            if state['state'] in ('completed', 'error'):
                return state
            time.sleep(.01)
        self.fail('Job did not finish within 10 seconds')

    def log(self, key):
        response = self.client.get(f'/api/jobs/{key}/log')
        self.assertEqual(response.status_code, 200)
        records = [json.loads(line) for line in response.data.decode().splitlines()]
        response.close()
        return records

    def test_single_pdf_has_page_progress_while_running_and_zip_log(self):
        entered, release = threading.Event(), threading.Event()
        real_process = jobs.process
        def pause(*args, progress=None, **kwargs):
            def callback(page, pages):
                progress(page, pages)
                if page == 1:
                    entered.set()
                    self.assertTrue(release.wait(5))
            return real_process(*args, progress=callback, **kwargs)
        with patch.object(jobs, 'process', pause):
            key = self.submit([('single.pdf', pdf_bytes(3))])
            try:
                self.assertTrue(entered.wait(5))
                status = self.client.get('/api/jobs/' + key).json
                self.assertEqual((status['state'], status['current'], status['page'], status['pages']), ('running', 'single.pdf', 1, 3))
                self.assertEqual(status['completed'], 0)
                self.assertTrue(any(r['event'] == 'page' and r['page'] == 1 for r in self.log(key)))
                self.assertEqual(self.client.get(f'/api/jobs/{key}/result').status_code, 409)
            finally:
                release.set()
            result = self.wait(key)
        self.assertEqual((result['success'], result['failed'], result['completed']), (1, 0, 1))
        response = self.client.get(f'/api/jobs/{key}/result')
        self.assertEqual(response.status_code, 200)
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            self.assertIn('[tailieuonthi.org]single.pdf', archive.namelist())
            self.assertEqual(json.loads(archive.read('bao-cao.json'))[0]['pages'], 3)
            records = [json.loads(line) for line in archive.read('tien-trinh.jsonl').decode().splitlines()]
            self.assertEqual(records[-1]['event'], 'completed')
            self.assertTrue(records[-1]['time'].endswith('+07:00'))
        response.close()

    def test_batch_continues_after_error_and_preserves_duplicate_outputs(self):
        key = self.submit([('bad.pdf', b'bad'), ('same.pdf', pdf_bytes(1)), ('same.pdf', pdf_bytes(2))])
        result = self.wait(key)
        self.assertEqual((result['state'], result['completed'], result['success'], result['failed']), ('completed', 3, 2, 1))
        self.assertEqual([r['status'] for r in result['reports']], ['error', 'ok', 'ok'])
        errors = [r for r in self.log(key) if r['event'] == 'file_error']
        self.assertEqual(errors[0]['file'], 'bad.pdf')
        self.assertIn('ValueError', errors[0]['traceback'])
        response = self.client.get(f'/api/jobs/{key}/result')
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            self.assertIn('[tailieuonthi.org]same (2).pdf', archive.namelist())
        response.close()

    def test_all_failed_still_has_log_and_reports(self):
        key = self.submit([('broken.pdf', b'broken')])
        result = self.wait(key)
        self.assertEqual((result['state'], result['success'], result['failed']), ('completed', 0, 1))
        self.assertIn('error', result['reports'][0])
        self.assertTrue(any(r['event'] == 'file_error' for r in self.log(key)))
        self.assertEqual(self.client.get(f'/api/jobs/{key}/result').status_code, 409)

    def test_expired_finished_jobs_cleaned_without_touching_active_job(self):
        import os
        key = self.submit([('old.pdf', pdf_bytes(1))])
        self.wait(key)
        folder = jobs.ROOT / key
        old = time.time() - jobs.TTL - 10
        os.utime(folder, (old, old))
        active_key = 'f' * 32
        active_folder = jobs.ROOT / active_key
        active_folder.mkdir()
        os.utime(active_folder, (old, old))
        with jobs.LOCK:
            jobs.JOBS[active_key] = dict(state='running')
        try:
            jobs.cleanup()
            self.assertFalse(folder.exists())
            self.assertIsNone(jobs.snapshot(key))
            self.assertTrue(active_folder.exists())
        finally:
            with jobs.LOCK:
                jobs.JOBS.pop(active_key, None)
            self.keys.remove(key)

    def test_bad_requests_and_unknown_job(self):
        self.assertEqual(self.client.post('/api/jobs').status_code, 400)
        self.assertEqual(self.client.get('/api/jobs/unknown').status_code, 404)
        self.assertEqual(self.client.get('/api/jobs/unknown/log').status_code, 404)
