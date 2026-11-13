"""Independent checks of exported pixels, page geometry and HTTP failures."""
import io
import unittest
import zipfile
from unittest.mock import patch
import fitz
from PIL import Image
from werkzeug.datastructures import MultiDict
import image_converter as converter
from app import app


def image(color='red', size=(120, 60), fmt='PNG', exif=None):
    buffer = io.BytesIO()
    source = Image.new('RGBA' if isinstance(color, tuple) else 'RGB', size, color)
    source.save(buffer, fmt, **({'exif': exif} if exif else {}))
    return buffer.getvalue()


def pdf(pages=2, password=None, width=72, height=144):
    with fitz.open() as doc:
        for color in [(1, 0, 0), (0, 0, 1)][:pages]:
            page = doc.new_page(width=width, height=height)
            page.draw_rect(page.rect, color=color, fill=color)
        return doc.tobytes(**({'encryption': fitz.PDF_ENCRYPT_AES_256, 'owner_pw': password, 'user_pw': password} if password else {}))


class ImageConverterTests(unittest.TestCase):
    def test_pdf_zip_formats_dpi_page_order(self):
        for fmt, dpi in [('png', 72), ('jpg', 150)]:
            with self.subTest(fmt=fmt):
                with zipfile.ZipFile(io.BytesIO(converter.pdf_to_images(pdf(), fmt, dpi))) as archive:
                    self.assertEqual(archive.namelist(), [f'trang-0001.{fmt}', f'trang-0002.{fmt}'])
                    for number, expected_channel in [(1, 0), (2, 2)]:
                        with Image.open(io.BytesIO(archive.read(f'trang-{number:04d}.{fmt}'))) as output:
                            self.assertEqual(output.size, (dpi, dpi * 2))
                            color = output.getpixel((dpi//2, dpi))
                            self.assertGreater(color[expected_channel], 240)

    def test_merge_order_a4_orientation_and_proportions(self):
        data = converter.images_to_pdf([('red.png', image()), ('blue.png', image('blue', (60,120)))])
        with fitz.open(stream=data, filetype='pdf') as doc:
            self.assertEqual(len(doc), 2)
            self.assertEqual(tuple(doc[0].rect), (0, 0, 842, 595))
            self.assertEqual(tuple(doc[1].rect), (0, 0, 595, 842))
            for i, channel in [(0,0),(1,2)]:
                rect = fitz.Rect(doc[i].get_image_info()[0]['bbox'])
                self.assertAlmostEqual(rect.width / rect.height, 2 if i == 0 else .5, places=4)
                pix = doc[i].get_pixmap()
                self.assertGreater(pix.pixel(pix.width//2, pix.height//2)[channel], 240)

    def test_transparency_white_background_and_exif_orientation(self):
        with fitz.open(stream=converter.images_to_pdf([('alpha.png', image((255,0,0,0)))], 'image'), filetype='pdf') as doc:
            self.assertAlmostEqual(doc[0].rect.width, 57.6, places=3)
            self.assertEqual(doc[0].get_pixmap().pixel(10,10), (255,255,255))
        exif = Image.Exif(); exif[274] = 6
        with fitz.open(stream=converter.images_to_pdf([('rotate.jpg', image(size=(120,60), fmt='JPEG', exif=exif))]), filetype='pdf') as doc:
            self.assertGreater(doc[0].rect.height, doc[0].rect.width)
            rect = fitz.Rect(doc[0].get_image_info()[0]['bbox'])
            self.assertAlmostEqual(rect.width/rect.height, .5, places=4)

    def test_invalid_inputs_and_resource_limits(self):
        for data in [b'bad', pdf(password='secret')]:
            with self.assertRaises(ValueError): converter.pdf_to_images(data)
        for fmt, dpi in [('gif',150), ('png',0), ('png',151)]:
            with self.assertRaises(ValueError): converter.pdf_to_images(pdf(),fmt,dpi)
        for files, paper in [([], 'a4'), ([('bad.png',b'bad')], 'a4'), ([('gif.gif',image(fmt='GIF'))], 'a4'), ([('a.png',image())]*101,'a4'), ([('a.png',image())],'bad')]:
            with self.assertRaises(ValueError): converter.images_to_pdf(files,paper)
        with patch.object(converter, 'MAX_PIXELS', 100):
            with self.assertRaises(ValueError): converter.pdf_to_images(pdf())
            with self.assertRaises(ValueError): converter.images_to_pdf([('a.png',image())])

    def test_http_pages_downloads_and_validation(self):
        client = app.test_client()
        for url in ['/pdf-to-images', '/images-to-pdf']:
            result = client.get(url)
            self.assertEqual(result.status_code,200)
            self.assertIn(b'/static/images.js',result.data)
        result = client.post('/api/pdf-to-images', data={'pdf':(io.BytesIO(pdf()),'sample.pdf'),'format':'jpg','dpi':'72'})
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.mimetype,'application/zip')
        with zipfile.ZipFile(io.BytesIO(result.data)) as archive: self.assertEqual(len(archive.namelist()),2)
        data = MultiDict([('images',(io.BytesIO(image()),'red.png')),('images',(io.BytesIO(image('blue')),'blue.png'))])
        result = client.post('/api/images-to-pdf',data=data)
        self.assertEqual(result.status_code,200)
        self.assertEqual(result.mimetype,'application/pdf')
        with fitz.open(stream=result.data,filetype='pdf') as doc: self.assertEqual(len(doc),2)
        for endpoint in ['/api/pdf-to-images','/api/images-to-pdf']:
            self.assertEqual(client.post(endpoint).status_code,400)
        result = client.post('/api/pdf-to-images',data={'pdf':(io.BytesIO(pdf()),'x.pdf'),'dpi':'oops'})
        self.assertEqual(result.status_code,400)
        result = client.post('/api/images-to-pdf',data={'images':(io.BytesIO(b'bad'),'bad.png')})
        self.assertEqual(result.status_code,400)
        self.assertEqual(client.post('/api/images-to-pdf',headers={'Origin':'https://example.org'}).status_code,403)


if __name__ == '__main__': unittest.main()
