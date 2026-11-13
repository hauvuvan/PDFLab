"""Independent behavioral regression checks; all document data stays in memory."""
import io
import json
import unittest
import zipfile

import pymupdf as fitz
from PIL import Image, ImageChops
from werkzeug.datastructures import MultiDict

from app import app
from watermark import image_bytes, open_pdf, options, preview, process


def pdf_bytes(pages=2, rotation=0, crop=False):
    with fitz.open() as doc:
        for _ in range(pages):
            page = doc.new_page(width=400, height=500)
            page.insert_text((80, 100), 'Original selectable text')
            if crop:
                page.set_cropbox(fitz.Rect(40, 50, 360, 450))
            page.set_rotation(rotation)
        return doc.tobytes()


def logo_bytes():
    image = Image.new('RGBA', (200, 40), (255, 0, 0, 255))
    image.paste((0, 0, 255, 255), (100, 0, 200, 40))
    output = io.BytesIO()
    image.save(output, 'PNG')
    return output.getvalue()


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.opts = options({})
        self.image, self.size = image_bytes(logo_bytes(), 100)

    def test_all_pages_text_link_source_unchanged(self):
        source = pdf_bytes()
        result, pages = process(source, self.image, self.size, self.opts)
        self.assertEqual(pages, 2)
        with fitz.open(stream=source, filetype='pdf') as original, fitz.open(stream=result, filetype='pdf') as doc:
            for before, after in zip(original, doc):
                self.assertEqual(before.get_text(), after.get_text())
                self.assertEqual(len(before.get_images()), 0)
                self.assertEqual(len(before.get_links()), 0)
                self.assertEqual(len(after.get_images()), 1)
                self.assertEqual(after.get_links()[0]['uri'], 'https://tailieuonthi.org/')

    def test_visible_footer_orientation_for_rotations_and_crop(self):
        for rotation in (0, 90, 180, 270):
            for crop in (False, True):
                with self.subTest(rotation=rotation, crop=crop):
                    result, _ = process(pdf_bytes(1, rotation, crop), self.image, self.size, self.opts)
                    with fitz.open(stream=result, filetype='pdf') as doc:
                        page = doc[0]
                        pix = page.get_pixmap(alpha=False)
                        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                        # Original black text cannot satisfy these pure red/blue tests.
                        reds = [(x, y) for y in range(image.height) for x in range(image.width) if (lambda p: p[0] > 220 and p[1] < 30 and p[2] < 30)(image.getpixel((x, y)))]
                        blues = [(x, y) for y in range(image.height) for x in range(image.width) if (lambda p: p[2] > 220 and p[0] < 30 and p[1] < 30)(image.getpixel((x, y)))]
                        self.assertTrue(reds)
                        self.assertTrue(blues)
                        self.assertLess(sum(x for x, _ in reds)/len(reds), sum(x for x, _ in blues)/len(blues))
                        all_pixels = reds + blues
                        self.assertAlmostEqual(max(y for _, y in all_pixels), image.height - 21, delta=1)
                        self.assertAlmostEqual((min(x for x, _ in all_pixels)+max(x for x, _ in all_pixels))/2, image.width/2, delta=1)
                        link_rect = page.get_links()[0]['from']
                        self.assertAlmostEqual(link_rect.y1, image.height - 20, delta=1)
                        self.assertAlmostEqual((link_rect.x0 + link_rect.x1) / 2, image.width / 2, delta=1)
                        self.assertTrue(all(link_rect.contains(fitz.Point(x + .5, y + .5)) for x, y in all_pixels[::100]))

    def test_opacity_and_alpha_preserved(self):
        source = Image.new('RGBA', (2, 1), (1, 2, 3, 128))
        source.putpixel((0, 0), (0, 0, 0, 0))
        buf = io.BytesIO(); source.save(buf, 'PNG')
        result, _ = image_bytes(buf.getvalue(), 50)
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.getpixel((0, 0))[3], 0)
            self.assertEqual(image.getpixel((1, 0))[3], 64)

    def test_preview_equals_export_render(self):
        source = pdf_bytes(2, 90, True)
        png, pages = preview(source, self.image, self.size, self.opts, 2)
        result, _ = process(source, self.image, self.size, self.opts)
        with fitz.open(stream=result, filetype='pdf') as doc:
            page = doc[1]
            zoom = min(1.4, 1400 / max(page.rect.width, page.rect.height))
            expected = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png')
        actual_image = Image.open(io.BytesIO(png)).convert('RGB')
        expected_image = Image.open(io.BytesIO(expected)).convert('RGB')
        self.assertEqual(actual_image.size, expected_image.size)
        # Rendering text before/after serialization differs by one antialias level.
        difference = ImageChops.difference(actual_image, expected_image)
        self.assertTrue(all(maximum <= 1 for minimum, maximum in difference.getextrema()))
        self.assertEqual(pages, 2)

    def test_locked_pdf_and_corrupt_rejected(self):
        with fitz.open(stream=pdf_bytes(), filetype='pdf') as doc:
            encrypted = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, user_pw='secret', owner_pw='owner')
        for data in (encrypted, b'not a pdf'):
            with self.assertRaises(ValueError):
                open_pdf(data)

    def test_invalid_values_and_no_link(self):
        for values in ({'width': 'nan'}, {'height': '-1'}, {'margin': 'inf'}, {'position': 'other'}, {'link': 'javascript:alert(1)'}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                options(values)
        opts = options({'link': ''})
        result, _ = process(pdf_bytes(1), self.image, self.size, opts)
        with fitz.open(stream=result, filetype='pdf') as doc:
            self.assertEqual(doc[0].get_links(), [])
        with self.assertRaises(ValueError):
            preview(pdf_bytes(1), self.image, self.size, opts, 2)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def post(self, path, pdfs=None, extra=None):
        data = MultiDict([('watermark', (io.BytesIO(logo_bytes()), 'logo.png'))])
        if pdfs:
            for name, raw in pdfs:
                data.add('pdfs', (io.BytesIO(raw), name))
        for key, value in (extra or {}).items():
            data.add(key, value)
        return self.client.post(path, data=data, content_type='multipart/form-data')

    def test_dashboard_health_and_local_protection(self):
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertIn('Watermark PDF'.encode(), self.client.get('/').data)
        self.assertEqual(self.client.get('/health').json['status'], 'ok')
        self.assertEqual(self.client.get('/health', headers={'Host':'untrusted.example'}).status_code, 403)
        self.assertEqual(self.client.post('/api/process', headers={'Origin':'https://untrusted.example'}).status_code, 403)

    def test_batch_mixed_results_duplicate_names_and_report(self):
        response = self.post('/api/process', [('tài liệu.pdf', pdf_bytes()), ('tài liệu.pdf', pdf_bytes(1)), ('hỏng.pdf', b'broken')])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['X-Success-Count'], '2')
        self.assertEqual(response.headers['X-Failure-Count'], '1')
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            names = archive.namelist()
            self.assertIn('[tailieuonthi.org]tài liệu.pdf', names)
            self.assertIn('[tailieuonthi.org]tài liệu (2).pdf', names)
            report = json.loads(archive.read('bao-cao.json'))
            self.assertEqual([r['status'] for r in report], ['ok', 'ok', 'error'])
            self.assertEqual(report[0]['pages'], 2)

    def test_long_unicode_filenames_keep_headers_bounded(self):
        response = self.post('/api/process', [('ệ' * 170 + str(i) + '.pdf', pdf_bytes(1)) for i in range(10)])
        self.assertEqual(response.status_code, 200)
        self.assertLess(len(response.headers['X-Reports']), 6000)
        with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
            report = json.loads(archive.read('bao-cao.json'))
            self.assertEqual(len(report), 10)
            self.assertTrue(all(r['status'] == 'ok' for r in report))

    def test_all_failed_and_missing_inputs(self):
        response = self.post('/api/process', [('bad.pdf', b'broken')])
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['reports'][0]['status'], 'error')
        self.assertEqual(self.client.post('/api/process').status_code, 400)
        self.assertEqual(self.post('/api/process').status_code, 400)
        self.assertEqual(self.post('/api/process', [('a.pdf', pdf_bytes())], {'width':'101'}).status_code, 400)

    def test_preview_api_png_page_count_and_bad_page(self):
        for page, expected in [('2',200), ('3',400), ('no',400)]:
            response = self.post('/api/preview', extra={'pdf':(io.BytesIO(pdf_bytes()), 'a.pdf'), 'page':page})
            self.assertEqual(response.status_code, expected)
            if expected == 200:
                self.assertEqual(response.headers['X-Page-Count'], '2')
                self.assertTrue(response.data.startswith(b'\x89PNG'))

    def test_request_size_error_is_json(self):
        old = app.config['MAX_CONTENT_LENGTH']
        try:
            app.config['MAX_CONTENT_LENGTH'] = 10
            response = self.post('/api/process', [('a.pdf', pdf_bytes())])
            self.assertEqual(response.status_code, 413)
            self.assertIn('error', response.json)
        finally:
            app.config['MAX_CONTENT_LENGTH'] = old


if __name__ == '__main__':
    unittest.main()
