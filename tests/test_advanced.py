"""Independent acceptance tests for advanced watermark controls and local presets."""
import base64
import io
import json
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
from PIL import Image, ImageChops
from werkzeug.datastructures import MultiDict

from app import app
from watermark import options, prepare_watermark, process, preview
from test_watermark import logo_bytes, pdf_bytes


def render(raw, page=0):
    with fitz.open(stream=raw, filetype='pdf') as doc:
        p = doc[page].get_pixmap(alpha=False)
        return Image.frombytes('RGB', (p.width, p.height), p.samples)


def stamp(values=None, source=None):
    opts = options(values or {})
    image, size = prepare_watermark(logo_bytes(), opts)
    return process(source or pdf_bytes(1), image, size, opts)[0]


class AdvancedEngineTests(unittest.TestCase):
    def test_nine_positions_and_offsets(self):
        for anchor in ['top-left','top','top-right','center-left','center','center-right','bottom-left','bottom','bottom-right']:
            with self.subTest(anchor=anchor):
                output = stamp({'position':anchor, 'width':20, 'height':10})
                with fitz.open(stream=output, filetype='pdf') as doc:
                    rect = doc[0].get_links()[0]['from']
                    expected_x = 20 if anchor.endswith('-left') else 300 if anchor.endswith('-right') else 160
                    expected_y = 20 if anchor.startswith('top') else 464 if anchor.startswith('bottom') else 242
                    self.assertAlmostEqual(rect.x0, expected_x, delta=.01)
                    self.assertAlmostEqual(rect.y0, expected_y, delta=.01)
        output = stamp({'position':'center', 'width':20, 'offset_x':10, 'offset_y':-10})
        with fitz.open(stream=output, filetype='pdf') as doc:
            rect = doc[0].get_links()[0]['from']
            self.assertAlmostEqual(rect.x0, 200, delta=.01)
            self.assertAlmostEqual(rect.y0, 192, delta=.01)

    def test_custom_page_selection_preserves_others_and_preview(self):
        source = pdf_bytes(5)
        for mode, page_range, expected in [('all','', {0,1,2,3,4}),('odd','',{0,2,4}),('even','',{1,3}),('custom','1, 3-4, 3',{0,2,3})]:
            with self.subTest(mode=mode):
                opts = options({'pages':mode, 'page_range':page_range})
                image, size = prepare_watermark(logo_bytes(), opts)
                output, _ = process(source, image, size, opts)
                with fitz.open(stream=output, filetype='pdf') as doc:
                    for index,p in enumerate(doc):
                        self.assertEqual(bool(p.get_images()), index in expected)
                        self.assertEqual(bool(p.get_links()), index in expected)
                for number in (1,2):
                    actual, _ = preview(source,image,size,opts,number)
                    with fitz.open(stream=output,filetype='pdf') as doc:
                        p=doc[number-1];expected_png=p.get_pixmap(matrix=fitz.Matrix(1.4,1.4),alpha=False).tobytes('png')
                    difference=ImageChops.difference(Image.open(io.BytesIO(actual)), Image.open(io.BytesIO(expected_png)))
                    self.assertTrue(all(maximum <= 1 for minimum,maximum in difference.getextrema()))

    def test_empty_or_invalid_page_selection_rejected(self):
        for value in ('', '0', '3-1', '1,,2', '-1', '1.5', '1-2-3'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                options({'pages':'custom', 'page_range':value})
        for values in ({'pages':'even'}, {'pages':'custom','page_range':'2'}):
            opts=options(values); image,size=prepare_watermark(logo_bytes(),opts)
            with self.assertRaises(ValueError):process(pdf_bytes(1),image,size,opts)

    def test_text_vietnamese_fonts_color_alpha_angle(self):
        for font in ('sans','serif','mono'):
            opts=options({'kind':'text','text':'TÀI LIỆU ÔN THI\nĐặng Thị Hồng','font':font,'bold':'true','color':'#e02040','opacity':50,'angle':-25})
            image,size=prepare_watermark(b'',opts)
            with Image.open(io.BytesIO(image)) as im:
                self.assertGreater(size[0],size[1])
                self.assertGreater(im.getbbox()[2],0)
                self.assertLessEqual(im.getchannel('A').getextrema()[1],128)
                colors=[rgb for rgb in im.getdata() if rgb[3]>100]
                self.assertTrue(colors)
                self.assertTrue(all(rgb[:3]==(224,32,64) for rgb in colors))
            output,_=process(pdf_bytes(1),image,size,opts)
            self.assertGreater(ImageChops.difference(render(output),render(pdf_bytes(1))).getbbox()[2],0)

    def test_image_tint_preserves_alpha_and_zero_opacity(self):
        opts=options({'tint':'true','color':'#00ff00','opacity':100})
        image,_=prepare_watermark(logo_bytes(),opts)
        with Image.open(io.BytesIO(image)) as im:
            self.assertEqual(im.getpixel((10,10)),(0,255,0,255))
        source=pdf_bytes(1)
        zero=stamp({'opacity':0},source)
        difference=ImageChops.difference(render(zero),render(source))
        self.assertTrue(all(maximum <= 1 for minimum,maximum in difference.getextrema()))
        with fitz.open(stream=zero,filetype='pdf') as doc:
            self.assertEqual(doc[0].get_links(),[])
            self.assertEqual(doc[0].get_images(),[])

    def test_angle_expands_watermark_and_keeps_orientation(self):
        for angle in (-180,-90,-25,25,90,180):
            with self.subTest(angle=angle):
                image,size=prepare_watermark(logo_bytes(),options({'angle':angle}))
                self.assertTrue(Image.open(io.BytesIO(image)).getbbox())
                if abs(angle)==90:self.assertEqual(size,(40,200))
                if abs(angle)==180:self.assertEqual(size,(200,40))

    def test_tile_spacing_changes_count_and_clips_links(self):
        counts=[]
        for spacing in (5,40):
            output=stamp({'layout':'tile','width':10,'height':5,'spacing_x':spacing,'spacing_y':spacing,'angle':-30},pdf_bytes(1,90,True))
            with fitz.open(stream=output,filetype='pdf') as doc:
                links=doc[0].get_links();counts.append(len(links))
                for link in links:
                    self.assertTrue(doc[0].rect.contains(link['from']))
        self.assertGreater(counts[0],counts[1])
        self.assertGreater(counts[1],1)

    def test_dense_tile_remains_bounded_and_positive_offset_covers_page(self):
        raw=io.BytesIO()
        Image.new('RGBA',(1,10000),(255,0,0,255)).save(raw,'PNG')
        opts=options({'layout':'tile','width':5,'height':1,'spacing_x':5,'spacing_y':5,'offset_x':45,'offset_y':45})
        image,size=prepare_watermark(raw.getvalue(),opts)
        output,_=process(pdf_bytes(1),image,size,opts)
        with fitz.open(stream=output,filetype='pdf') as doc:
            links=doc[0].get_links()
            self.assertLessEqual(len(links),450)
            self.assertGreater(len(links),100)
            self.assertLess(min(link['from'].y0 for link in links),50)
            self.assertLess(min(link['from'].x0 for link in links),40)
            self.assertGreater(max(link['from'].y1 for link in links),450)
            self.assertGreater(max(link['from'].x1 for link in links),360)

    def test_layer_above_below_opaque_page(self):
        with fitz.open() as doc:
            page=doc.new_page(width=400,height=500)
            page.draw_rect(page.rect,fill=(1,1,1),color=(1,1,1))
            source=doc.tobytes()
        above=render(stamp({'layer':'above'},source))
        below=render(stamp({'layer':'below'},source))
        self.assertIsNotNone(ImageChops.difference(above,render(source)).getbbox())
        self.assertIsNone(ImageChops.difference(below,render(source)).getbbox())

    def test_extended_validation(self):
        for values in ({'angle':'nan'},{'angle':181},{'offset_x':46},{'opacity':-1},{'spacing_x':0},{'color':'red'},{'kind':'text','text':''},{'kind':'text','text':'x'*301},{'kind':'text','text':'\n'.join(['a']*6)},{'font':'other'},{'layer':'other'}):
            with self.subTest(values=values),self.assertRaises(ValueError):options(values)


class PresetApiTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.old=app.config['PRESETS_PATH']
        self.path=Path(self.directory.name)/'presets.json'
        app.config['PRESETS_PATH']=self.path
        self.client=app.test_client()
    def tearDown(self):
        app.config['PRESETS_PATH']=self.old
        self.directory.cleanup()
    def recipe(self):
        return {'name':'Logo ôn thi','options':{'kind':'image','angle':-25,'pages':'custom','page_range':'1-3'},'image':base64.b64encode(logo_bytes()).decode()}
    def test_image_roundtrip_update_and_delete(self):
        self.assertEqual(self.client.get('/api/presets').json,{'presets':[]})
        saved=self.client.post('/api/presets',json=self.recipe())
        self.assertEqual(saved.status_code,200)
        item=saved.json['preset'];self.assertEqual(item['image'],self.recipe()['image'])
        self.assertEqual(item['options']['angle'],-25)
        self.assertEqual(self.client.get('/api/presets').json['presets'],[item])
        self.assertEqual(json.loads(self.path.read_text()),[item])
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
        item['name']='Đã đổi';updated=self.client.post('/api/presets',json=item)
        self.assertEqual(updated.status_code,200)
        self.assertEqual(len(self.client.get('/api/presets').json['presets']),1)
        self.assertEqual(self.client.delete('/api/presets/'+item['id']).status_code,200)
        self.assertEqual(self.client.delete('/api/presets/'+item['id']).status_code,404)
    def test_duplicate_names_have_separate_ids_and_limit_30(self):
        ids=[]
        for index in range(30):
            response=self.client.post('/api/presets',json=self.recipe())
            self.assertEqual(response.status_code,200)
            ids.append(response.json['preset']['id'])
        self.assertEqual(len(set(ids)),30)
        self.assertEqual(self.client.post('/api/presets',json=self.recipe()).status_code,400)
        self.assertEqual(len(self.client.get('/api/presets').json['presets']),30)

    def test_text_recipe_no_logo(self):
        response=self.client.post('/api/presets',json={'name':'Chữ','options':{'kind':'text','text':'TÀI LIỆU ÔN THI','layout':'tile','color':'#20aa33','opacity':25}})
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['preset']['image'],'')
    def test_invalid_recipe_and_missing_id_do_not_write(self):
        for data in ({}, {'name':'x','options':{'kind':'image'},'image':'not base64'}, {'name':'x','options':{'kind':'text','text':'x'},'id':'missing'}):
            with self.subTest(data=data):
                self.assertEqual(self.client.post('/api/presets',json=data).status_code,400)
                self.assertFalse(self.path.exists())
    def test_corrupt_store_not_overwritten(self):
        self.path.write_text('broken json')
        self.assertEqual(self.client.get('/api/presets').status_code,400)
        self.assertEqual(self.client.post('/api/presets',json=self.recipe()).status_code,400)
        self.assertEqual(self.path.read_text(),'broken json')
    def test_wrong_shape_store_not_overwritten(self):
        for content in ('[{}]', '[1]', '[{"id":"x"}]'):
            with self.subTest(content=content):
                self.path.write_text(content)
                self.assertEqual(self.client.get('/api/presets').status_code,400)
                self.assertEqual(self.client.post('/api/presets',json=self.recipe()).status_code,400)
                self.assertEqual(self.client.delete('/api/presets/x').status_code,400)
                self.assertEqual(self.path.read_text(),content)

    def test_cross_origin_delete_rejected(self):
        self.assertEqual(self.client.delete('/api/presets/any',headers={'Origin':'https://other.example'}).status_code,403)
    def test_text_api_without_image(self):
        data=MultiDict([('kind','text'),('text','TÀI LIỆU ÔN THI'),('pdfs',(io.BytesIO(pdf_bytes(2)),'example.pdf'))])
        response=self.client.post('/api/process',data=data,content_type='multipart/form-data')
        self.assertEqual(response.status_code,200)


if __name__=='__main__':unittest.main()
