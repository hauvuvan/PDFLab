"""Independent Word conversion checks: real engine and failure isolation."""
import io
import json
import subprocess
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import fitz
from werkzeug.datastructures import MultiDict
from app import app
import jobs
import word_converter


def docx_bytes():
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        archive.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
        archive.writestr('_rels/.rels', '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        archive.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Tài liệu tiếng Việt thử nghiệm Paperdesk</w:t></w:r></w:p><w:sectPr/></w:body></w:document>')
    return output.getvalue()


class WordTests(unittest.TestCase):
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

    def wait(self, key):
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            state = jobs.snapshot(key)
            if state['state'] in ('completed', 'error'):
                return state
            time.sleep(.03)
        self.fail('Word job did not finish')

    def test_missing_engine_and_empty_input(self):
        self.assertEqual(self.client.post('/api/word/jobs').status_code, 400)
        with patch.object(word_converter, 'executable', return_value=None):
            self.assertFalse(self.client.get('/api/word/status').json['available'])
            response = self.client.post('/api/word/jobs', data={'documents': (io.BytesIO(b'word'), 'a.docx')})
            self.assertEqual(response.status_code, 503)
            with self.assertRaisesRegex(ValueError, 'LibreOffice'):
                word_converter.convert(b'word', 'a.docx')

    def test_timeout_and_failed_engine(self):
        with patch.object(word_converter, 'executable', return_value='/fake/soffice'):
            with patch.object(word_converter.subprocess, 'run', side_effect=subprocess.TimeoutExpired('soffice', 120)):
                with self.assertRaisesRegex(ValueError, '120'):
                    word_converter.convert(b'word', 'a.docx')
            with patch.object(word_converter.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
                with self.assertRaisesRegex(ValueError, 'Không chuyển'):
                    word_converter.convert(b'word', 'a.docx')
        for raw, name in [(b'', 'empty.docx'), (b'abc', 'wrong.pdf')]:
            with self.assertRaises(ValueError):
                word_converter.convert(raw, name)

    @unittest.skipUnless(word_converter.executable(), 'LibreOffice not installed')
    def test_real_batch_unicode_duplicates_and_bad_file(self):
        data = MultiDict()
        for name, raw in [('Tài liệu.docx', docx_bytes()), ('Tài liệu.docx', docx_bytes()), ('bad.pdf', b'bad')]:
            data.add('documents', (io.BytesIO(raw), name))
        response = self.client.post('/api/word/jobs', data=data)
        self.assertEqual(response.status_code, 202)
        key = response.json['id']
        self.keys.append(key)
        state = self.wait(key)
        self.assertEqual((state['state'], state['success'], state['failed']), ('completed', 2, 1))
        response = self.client.get(f'/api/jobs/{key}/result')
        self.assertEqual(response.status_code, 200)
        self.assertIn('word-sang-pdf.zip', response.headers['Content-Disposition'])
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            self.assertEqual(set(archive.namelist()), {'Tài liệu.pdf', 'Tài liệu (2).pdf', 'bao-cao.json', 'tien-trinh.jsonl'})
            reports = json.loads(archive.read('bao-cao.json'))
            self.assertEqual(reports[2]['status'], 'error')
            for name in ['Tài liệu.pdf', 'Tài liệu (2).pdf']:
                with fitz.open(stream=archive.read(name), filetype='pdf') as pdf:
                    self.assertEqual(len(pdf), 1)
                    self.assertIn('Tài liệu tiếng Việt thử nghiệm Paperdesk', pdf[0].get_text())
        log = self.client.get(f'/api/jobs/{key}/log')
        self.assertEqual(log.status_code, 200)
        self.assertIn(b'file_error', log.data)
        self.assertIn(b'+07:00', log.data)
        response.close()
        log.close()

    @unittest.skipUnless(word_converter.executable(), 'LibreOffice not installed')
    def test_real_legacy_doc(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source.docx'
            source.write_bytes(docx_bytes())
            output = root / 'legacy'
            output.mkdir()
            result = subprocess.run([word_converter.executable(), '-env:UserInstallation=' + (root / 'profile').as_uri(), '--headless', '--convert-to', 'doc:MS Word 97', '--outdir', str(output), str(source)], capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0)
            raw = (output / 'source.doc').read_bytes()
            self.assertTrue(raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')))
            pdf_raw, pages = word_converter.convert(raw, 'legacy.DOC')
            self.assertEqual(pages, 1)
            with fitz.open(stream=pdf_raw, filetype='pdf') as pdf:
                self.assertIn('Tài liệu tiếng Việt thử nghiệm Paperdesk', pdf[0].get_text())

    def test_all_invalid_batch_has_log_but_no_download(self):
        with patch.object(word_converter, 'executable', return_value='/fake/soffice'):
            response = self.client.post('/api/word/jobs', data={'documents': (io.BytesIO(b''), 'empty.docx')})
            self.assertEqual(response.status_code, 202)
            key = response.json['id']
            self.keys.append(key)
            state = self.wait(key)
            self.assertEqual((state['success'], state['failed']), (0, 1))
            self.assertEqual(self.client.get(f'/api/jobs/{key}/result').status_code, 409)
            log = self.client.get(f'/api/jobs/{key}/log')
            self.assertEqual(log.status_code, 200)
            self.assertIn(b'file_error', log.data)
            log.close()
