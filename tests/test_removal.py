"""Behavioral checks using synthetic PDFs, no user document data."""
import io
import json
import unittest

import pymupdf as fitz
from PIL import Image
import removal


def png(color, size=(40, 40)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, 'PNG')
    return buf.getvalue()


def fixture(pages=2, rotation=0, crop=False, nested=False):
    with fitz.open() as doc:
        for _ in range(pages):
            page = doc.new_page(width=400, height=500)
            page.insert_image(fitz.Rect(80, 80, 300, 300), stream=png('red'))
            page.insert_text((100, 150), 'KEEP OVERLAP', fontsize=15)
            page.insert_text((40, 450), 'FOOTER REMOVE', fontsize=12)
            if nested:
                page.insert_image(fitz.Rect(120, 180, 160, 220), stream=png('blue'))
            if crop:
                page.set_cropbox(fitz.Rect(20, 30, 380, 480))
            page.set_rotation(rotation)
        return doc.tobytes()


def opts(**kw):
    values = dict(regions='[]', images='[]', pages='all')
    values.update(kw)
    return removal.settings(values)


class RemovalTests(unittest.TestCase):
    def test_image_preserves_overlapping_text_and_unselected_page(self):
        data = fixture()
        selected = removal.inspect(data, 1)['candidates'][0]['id']
        result, count = removal.process(data, opts(images=json.dumps([selected]), pages='custom', page_range='1'))
        self.assertEqual(count, 1)
        with fitz.open(stream=result, filetype='pdf') as doc:
            self.assertIn('KEEP OVERLAP', doc[0].get_text())
            self.assertEqual(len(doc[0].get_image_info()), 0)
            self.assertEqual(len(doc[1].get_image_info()), 1)
            self.assertIn('FOOTER REMOVE', doc[0].get_text())

    def test_region_removes_footer_text_leaves_body(self):
        result, _ = removal.process(fixture(), opts(regions='[[0,0.85,1,1]]'))
        with fitz.open(stream=result, filetype='pdf') as doc:
            for page in doc:
                self.assertNotIn('FOOTER REMOVE', page.get_text())
                self.assertIn('KEEP OVERLAP', page.get_text())
                self.assertEqual(len(page.get_image_info()), 1)

    def test_region_scan_pixels_white_and_rotation_crop(self):
        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                data = fixture(pages=1, rotation=rotation, crop=True)
                with fitz.open(stream=data, filetype='pdf') as source:
                    page = source[0]
                    # A small visible area wholly inside the red image, away from text.
                    rect = fitz.Rect(80, 60, 100, 80) * page.rotation_matrix
                    normalized = [rect.x0/page.rect.width, rect.y0/page.rect.height, rect.x1/page.rect.width, rect.y1/page.rect.height]
                    point = rect.tl + (rect.br - rect.tl) * .5
                result, _ = removal.process(data, opts(regions=json.dumps([normalized])))
                with fitz.open(stream=result, filetype='pdf') as doc:
                    pix = doc[0].get_pixmap(alpha=False)
                    self.assertEqual(pix.pixel(int(point.x), int(point.y)), (255, 255, 255))

    def test_image_removal_rotated_cropped_pages(self):
        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                data = fixture(pages=1, rotation=rotation, crop=True)
                inspection = removal.inspect(data, 1)
                self.assertEqual(inspection['pages'], 1)
                self.assertEqual(len(inspection['candidates']), 1)
                candidate = inspection['candidates'][0]
                self.assertTrue(all(0 <= value <= 1 for value in candidate['rect']))
                result, count = removal.process(data, opts(images=json.dumps([candidate['id']])))
                with fitz.open(stream=result, filetype='pdf') as doc:
                    self.assertEqual(count, 1)
                    self.assertEqual(len(doc[0].get_image_info()), 0)
                    self.assertIn('KEEP OVERLAP', doc[0].get_text())
                    self.assertEqual(doc[0].rotation, rotation)

    def test_selected_image_keeps_other_contained_image(self):
        data = fixture(pages=1, nested=True)
        selected = removal.inspect(data, 1)['candidates'][0]['id']
        result, _ = removal.process(data, opts(images=json.dumps([selected])))
        with fitz.open(stream=result, filetype='pdf') as doc:
            self.assertEqual(len(doc[0].get_image_info()), 1, 'Unselected blue image inside selected logo must remain')

    def test_image_name_do_inside_text_must_be_preserved(self):
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_image(fitz.Rect(10, 10, 50, 50), stream=png('red'))
            name = page.get_images(full=True)[0][7]
            expected = '/' + name + ' Do KEEP'
            page.insert_text((100, 100), expected)
            data = doc.tobytes()
        selected = removal.inspect(data, 1)['candidates'][0]['id']
        result, count = removal.process(data, opts(images=json.dumps([selected])))
        with fitz.open(stream=result, filetype='pdf') as doc:
            self.assertEqual(doc[0].get_text().strip(), expected)
            self.assertEqual(count, 1)

    def test_inline_image_binary_data_stays_intact_or_is_rejected(self):
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_image(fitz.Rect(10, 10, 50, 50), stream=png('red'))
            name = page.get_images(full=True)[0][7]
            xref = doc.get_new_xref()
            doc.update_object(xref, '<<>>')
            inline = b'/fzImg0 Do X '
            stream = b'q 30 0 0 30 10 10 cm /' + name.encode() + b' Do Q\n'
            stream += b'q 30 0 0 30 100 100 cm BI /W 4 /H 1 /CS /RGB /BPC 8 ID ' + inline + b' EI Q'
            doc.update_stream(xref, stream)
            page.set_contents(xref)
            data = doc.tobytes()
            before = page.get_image_info(hashes=True, xrefs=True)[1]['digest']
        inspected = removal.inspect(data, 1)
        if not inspected['candidates']:
            return  # Conservative refusal is valid for unsupported mixed streams.
        selected = inspected['candidates'][0]['id']
        try:
            result, count = removal.process(data, opts(images=json.dumps([selected])))
        except ValueError:
            return
        with fitz.open(stream=result, filetype='pdf') as doc:
            infos = doc[0].get_image_info(hashes=True, xrefs=True)
            self.assertEqual(count, 1)
            self.assertEqual(len(infos), 1)
            self.assertEqual(infos[0]['digest'], before)

    def test_inherited_page_resources_are_removed(self):
        with fitz.open(stream=fixture(1), filetype='pdf') as doc:
            page = doc[0]
            resource = doc.xref_get_key(page.xref, 'Resources')[1]
            parent = int(doc.xref_get_key(page.xref, 'Parent')[1].split()[0])
            doc.xref_set_key(parent, 'Resources', resource)
            doc.xref_set_key(page.xref, 'Resources', 'null')
            data = doc.tobytes()
        selected = removal.inspect(data, 1)['candidates'][0]['id']
        result, count = removal.process(data, opts(images=json.dumps([selected])))
        self.assertEqual(count, 1)
        with fitz.open(stream=result, filetype='pdf') as doc:
            self.assertEqual(len(doc[0].get_image_info()), 0)
            self.assertIn('KEEP OVERLAP', doc[0].get_text())

    def test_nested_shared_form_removal_preserves_text_images_and_scope(self):
        with fitz.open(stream=fixture(1, nested=True), filetype='pdf') as source, fitz.open() as doc:
            for _ in range(2):
                page = doc.new_page(width=400, height=500)
                page.show_pdf_page(page.rect, source, 0)
            data = doc.tobytes()
        inspected = removal.inspect(data, 1)
        self.assertEqual(len(inspected['candidates']), 2)
        selected = inspected['candidates'][0]['id']
        result, count = removal.process(data, opts(images=json.dumps([selected]), pages='custom', page_range='1'))
        self.assertEqual(count, 1)
        with fitz.open(stream=data, filetype='pdf') as before, fitz.open(stream=result, filetype='pdf') as after:
            for original, changed in zip(before, after):
                self.assertEqual(original.get_text(), changed.get_text())
            self.assertEqual(len(after[0].get_image_info()), 1)
            self.assertEqual(len(after[1].get_image_info()), 2)
            self.assertEqual(before[1].get_pixmap().samples, after[1].get_pixmap().samples)
            blue_before = before[0].get_image_info(hashes=True)[1]['digest']
            self.assertEqual(after[0].get_image_info(hashes=True)[0]['digest'], blue_before)
        all_result, all_count = removal.process(data, opts(images=json.dumps([selected])))
        self.assertEqual(all_count, 2)
        with fitz.open(stream=all_result, filetype='pdf') as after:
            self.assertEqual([len(p.get_image_info()) for p in after], [1, 1])

    def test_preview_matches_export(self):
        data = fixture(pages=1)
        config = opts(regions='[[0,0.85,1,1]]')
        preview, _ = removal.process(data, config, 1)
        result, _ = removal.process(data, config)
        with fitz.open(stream=result, filetype='pdf') as doc:
            page = doc[0]
            zoom = min(1.5, 1400/max(page.rect.width, page.rect.height))
            self.assertEqual(preview, page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png'))

    def test_reject_bad_settings(self):
        for value in ('null', '{}', '[null]', '[[0,0,0,1]]', '[[0,0,NaN,1]]', '[[0,0,2,1]]'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                opts(regions=value)
        with self.assertRaises(ValueError):
            opts(images='[123]')
        with self.assertRaises(ValueError):
            removal.process(fixture(1), opts())
        with self.assertRaises(ValueError):
            removal.inspect(fixture(1), 2)

    def test_batch_process_zip_and_naming(self):
        import zipfile
        pdf1 = fixture(1)
        pdf2 = fixture(2)
        selected = removal.inspect(pdf1, 1)['candidates'][0]['id']
        options = opts(images=json.dumps([selected]))
        files = [('test1.pdf', pdf1), ('test2.pdf', pdf2), ('test1.pdf', pdf1)]
        zip_bytes, reports = removal.batch_process(files, options)
        self.assertEqual(len(reports), 3)
        self.assertTrue(all(r['status'] == 'ok' for r in reports))
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            names = z.namelist()
            self.assertIn('test1_da_xoa_watermark.pdf', names)
            self.assertIn('test2_da_xoa_watermark.pdf', names)
            self.assertIn('test1_da_xoa_watermark (2).pdf', names)
            self.assertIn('bao-cao.json', names)
            report_data = json.loads(z.read('bao-cao.json').decode('utf-8'))
            self.assertEqual(len(report_data), 3)
            with fitz.open(stream=z.read('test1_da_xoa_watermark.pdf'), filetype='pdf') as doc:
                self.assertEqual(len(doc[0].get_image_info()), 0)

    def test_batch_process_validation_and_partial_errors(self):
        with self.assertRaises(ValueError):
            removal.batch_process([], opts(regions='[[0,0,1,1]]'))
        with self.assertRaises(ValueError):
            removal.batch_process([('a.pdf', b'%PDF')], opts())
        zip_bytes, reports = removal.batch_process([('good.pdf', fixture(1)), ('bad.pdf', b'not a pdf'), ('text.txt', b'hello')], opts(regions='[[0,0.85,1,1]]'))
        self.assertEqual(len(reports), 3)
        self.assertEqual(reports[0]['status'], 'ok')
        self.assertEqual(reports[1]['status'], 'error')
        self.assertEqual(reports[2]['status'], 'error')


class RemovalApiTests(unittest.TestCase):
    def setUp(self):
        from app import app
        self.client = app.test_client()

    def post(self, action, data=None, source=None, **kw):
        fields = dict(data or {})
        fields['pdf'] = (io.BytesIO(source or fixture(2)), 'source.pdf')
        return self.client.post('/api/removal/' + action, data=fields, **kw)

    def test_inspect_preview_export_end_to_end(self):
        response = self.post('inspect')
        self.assertEqual(response.status_code, 200)
        inspected = response.get_json()
        self.assertEqual(inspected['pages'], 2)
        self.assertTrue(inspected['image'])
        config = dict(images=json.dumps([inspected['candidates'][0]['id']]), pages='odd')
        preview = self.post('preview', config)
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(preview.mimetype, 'image/png')
        self.assertTrue(preview.data.startswith(b'\x89PNG'))
        result = self.post('export', config)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.mimetype, 'application/pdf')
        self.assertIn('source_da_xoa_watermark.pdf', result.headers.get('Content-Disposition', ''))
        self.assertEqual(result.headers['X-Removed-Images'], '1')
        with fitz.open(stream=result.data, filetype='pdf') as doc:
            self.assertEqual(len(doc[0].get_image_info()), 0)
            self.assertEqual(len(doc[1].get_image_info()), 1)
            self.assertIn('KEEP OVERLAP', doc[0].get_text())

    def test_api_batch_export(self):
        import zipfile
        inspected = self.post('inspect').get_json()
        config = dict(images=json.dumps([inspected['candidates'][0]['id']]), pages='all')
        data = {
            'pdfs': [
                (io.BytesIO(fixture(1)), 'first.pdf'),
                (io.BytesIO(fixture(2)), 'second.pdf')
            ],
            **config
        }
        res = self.client.post('/api/removal/batch', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/zip')
        self.assertEqual(res.headers.get('X-Success-Count'), '2')
        self.assertEqual(res.headers.get('X-Total-Count'), '2')
        with zipfile.ZipFile(io.BytesIO(res.data)) as z:
            self.assertIn('first_da_xoa_watermark.pdf', z.namelist())
            self.assertIn('second_da_xoa_watermark.pdf', z.namelist())

    def test_invalid_inputs_and_local_origin_protection(self):
        self.assertEqual(self.client.post('/api/removal/inspect').status_code, 400)
        for fields in ({'page': 'wrong'}, {'page': '0'}, {'page': '3'}):
            self.assertEqual(self.post('inspect', fields).status_code, 400)
        for fields in ({}, {'regions': 'null'}, {'regions': '[[0,0,1,1]]', 'pages': 'custom', 'page_range': '5'}):
            self.assertEqual(self.post('export', fields).status_code, 400)
        self.assertEqual(self.post('inspect', source=b'broken').status_code, 400)
        self.assertEqual(self.post('unknown').status_code, 404)
        self.assertEqual(self.post('inspect', headers={'Origin': 'https://other.example'}).status_code, 403)
        self.assertEqual(self.post('inspect', base_url='http://evil.example').status_code, 403)


if __name__ == '__main__':
    unittest.main()
