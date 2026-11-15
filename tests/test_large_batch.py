"""Independent checks for disk-backed, unrestricted watermark batches."""
import io
import tempfile
import threading
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from werkzeug.datastructures import FileStorage, MultiDict
from app import app
import jobs
from test_watermark import logo_bytes, pdf_bytes


class LargeBatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(jobs, 'ROOT', self.root)
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

    def data(self, count=1, raw=None):
        raw = raw if raw is not None else pdf_bytes(1)
        data = MultiDict([('watermark', (io.BytesIO(logo_bytes()), 'logo.png'))])
        for index in range(count):
            data.add('pdfs', (io.BytesIO(raw), f'file-{index}.pdf'))
        return data

    def submit(self, data):
        response = self.client.post('/api/jobs', data=data)
        self.assertEqual(response.status_code, 202, response.get_data(as_text=True))
        key = response.json['id']
        self.keys.append(key)
        return key

    def wait(self, key):
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            status = jobs.snapshot(key)
            if status['state'] in ('completed', 'error'):
                return status
            time.sleep(.01)
        self.fail('Background batch did not finish')

    def assert_no_inputs(self, key):
        deadline = time.monotonic() + 2
        folder = self.root / key
        while time.monotonic() < deadline:
            files = [path.name for path in folder.iterdir()]
            if all(name in ('result.zip', 'progress.jsonl') for name in files):
                return
            time.sleep(.01)
        self.fail(f'Input data remained after batch: {files}')

    def test_accepts_over_1000_files_and_processes_in_order(self):
        seen = []
        def lightweight(raw, image, size, opts, progress=None):
            seen.append(raw)
            return b'%PDF-output', 1
        with patch.object(jobs, 'process', lightweight):
            key = self.submit(self.data(1005, b'%PDF-input'))
            state = self.wait(key)
        self.assertEqual((state['state'], state['total'], state['success']), ('completed', 1005, 1005))
        self.assertEqual([r['file'] for r in state['reports']], [f'file-{i}.pdf' for i in range(1005)])
        self.assertEqual(seen, [b'%PDF-input'] * 1005)
        with zipfile.ZipFile(self.root / key / 'result.zip') as archive:
            self.assertEqual(len([name for name in archive.namelist() if name.endswith('.pdf')]), 1005)
        self.assert_no_inputs(key)

    def test_jobs_and_preview_bypass_old_request_cap_but_word_keeps_it(self):
        with patch.dict(app.config, MAX_CONTENT_LENGTH=1024):
            key = self.submit(self.data())
            self.assertEqual(self.wait(key)['success'], 1)
            response = self.client.post('/api/preview', data={
                'watermark': (io.BytesIO(logo_bytes()), 'logo.png'),
                'pdf': (io.BytesIO(pdf_bytes(1)), 'large.pdf'),
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'image/png')
            response = self.client.post('/api/word/jobs', data={
                'documents': (io.BytesIO(b'x' * 2048), 'large.docx'),
            })
            self.assertEqual(response.status_code, 413)

    def test_inputs_staged_on_disk_and_deleted_per_file_including_errors(self):
        entered = threading.Event()
        release = threading.Event()
        calls = []
        def controlled(raw, image, size, opts, progress=None):
            calls.append(raw)
            if len(calls) == 1:
                entered.set()
                self.assertTrue(release.wait(5))
                raise ValueError('Damaged PDF')
            return pdf_bytes(1), 1
        with patch.object(jobs, 'process', controlled):
            key = self.submit(self.data(3, b'input-bytes'))
            try:
                self.assertTrue(entered.wait(5))
                staged = [path for path in (self.root / key).rglob('*') if path.is_file() and path.read_bytes() == b'input-bytes']
                self.assertEqual(len(staged), 3)
                self.assertEqual(calls, [b'input-bytes'])
            finally:
                release.set()
            state = self.wait(key)
        self.assertEqual((state['success'], state['failed']), (2, 1))
        self.assert_no_inputs(key)

    def test_duplicate_names_and_sources_survive_worker_failures(self):
        original = pdf_bytes(1)
        data = MultiDict([('watermark', (io.BytesIO(logo_bytes()), 'logo.png'))])
        for raw in (original, b'broken', original):
            data.add('pdfs', (io.BytesIO(raw), 'same.pdf'))
        key = self.submit(data)
        state = self.wait(key)
        self.assertEqual((state['success'], state['failed']), (2, 1))
        with zipfile.ZipFile(self.root / key / 'result.zip') as archive:
            self.assertIn('[tailieuonthi.org]same.pdf', archive.namelist())
            self.assertIn('[tailieuonthi.org]same (2).pdf', archive.namelist())
        self.assert_no_inputs(key)

    def test_failed_staging_or_submission_leaves_no_inputs_or_phantom_job(self):
        before = set(jobs.JOBS)
        for method in ('save', 'submit'):
            with self.subTest(method=method):
                if method == 'save':
                    context = patch.object(FileStorage, 'save', side_effect=OSError('Disk full'))
                else:
                    context = patch.object(jobs.EXECUTOR, 'submit', side_effect=RuntimeError('Worker unavailable'))
                with context:
                    response = self.client.post('/api/jobs', data=self.data())
                self.assertEqual(response.status_code, 503)
                self.assertTrue(response.json['error'])
                self.assertEqual(list(self.root.iterdir()), [])
                self.assertEqual(set(jobs.JOBS), before)


class DiskUploadTests(unittest.TestCase):
    def test_disk_stream_read_seek_and_close_semantics(self):
        from upload_stream import DiskUpload
        stream = DiskUpload()
        path = stream.path
        try:
            self.assertEqual(stream.write(b'abcdef'), 6)
            self.assertEqual(stream.tell(), 6)
            self.assertEqual(stream.seek(-3, 2), 3)
            self.assertEqual(stream.read(2), b'de')
            self.assertEqual(stream.seek(-2, 1), 3)
            self.assertEqual(stream.write(b'XY'), 2)
            stream.seek(0)
            self.assertEqual(stream.read(), b'abcXYf')
        finally:
            stream.close()
        self.assertFalse(path.exists())
        stream.close()
        with self.assertRaises(ValueError):
            stream.read()

    def test_malformed_multipart_does_not_leave_disk_uploads(self):
        import upload_stream
        created = []
        real_create = upload_stream.tempfile.mkstemp
        with tempfile.TemporaryDirectory() as root:
            def create(*args, **kwargs):
                kwargs['dir'] = root
                fd, name = real_create(*args, **kwargs)
                created.append(Path(name))
                return fd, name
            body = (b'--test-boundary\r\n'
                    b'Content-Disposition: form-data; name="pdfs"; filename="first.pdf"\r\n'
                    b'Content-Type: application/pdf\r\n\r\n'
                    b'first-content\r\n--test-boundary\r\n'
                    b'Content-Disposition: form-data; name="pdfs"; filename="partial.pdf"\r\n'
                    b'Content-Type: application/pdf\r\n\r\n'
                    b'partial-data-no-terminator')
            with patch.object(upload_stream.tempfile, 'mkstemp', create):
                response = app.test_client().post('/api/jobs', data=body,
                    content_type='multipart/form-data; boundary=test-boundary')
            self.assertEqual(response.status_code, 400)
            self.assertTrue(created)
            self.assertTrue(all(not path.exists() for path in created))
