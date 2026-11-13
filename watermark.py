"""Watermark engine shared by preview and batch export."""
import io
import math
import re
from urllib.parse import urlsplit
import pymupdf as fitz
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


def options(values):
    values = {key: str(value) for key, value in values.items()}
    result = {}
    for key, default, low, high in [('width', 50, 5, 95), ('height', 10, 1, 80), ('opacity', 100, 0, 100), ('margin', 20, 0, 150), ('angle', 0, -180, 180), ('offset_x', 0, -45, 45), ('offset_y', 0, -45, 45), ('spacing_x', 20, 5, 100), ('spacing_y', 15, 5, 100)]:
        try:
            value = float(values.get(key, default))
        except (ValueError, TypeError):
            raise ValueError('Thông số kích thước phải là số.')
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key} phải nằm trong khoảng {low}–{high}.')
        result[key] = value
    result['position'] = values.get('position', 'bottom')
    if result['position'] not in ('top', 'center', 'bottom', 'top-left', 'top-right', 'center-left', 'center-right', 'bottom-left', 'bottom-right'):
        raise ValueError('Vị trí watermark không hợp lệ.')
    for key, default, allowed in [('kind', 'image', ('image', 'text')), ('layout', 'single', ('single', 'tile')), ('layer', 'above', ('above', 'below')), ('font', 'sans', ('sans', 'serif', 'mono')), ('bold', 'false', ('true', 'false')), ('tint', 'false', ('true', 'false')), ('pages', 'all', ('all', 'odd', 'even', 'custom'))]:
        result[key] = values.get(key, default)
        if result[key] not in allowed:
            raise ValueError(f'Tùy chọn {key} không hợp lệ.')
    result['color'] = values.get('color', '#808080')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', result['color']):
        raise ValueError('Màu phải có dạng #RRGGBB.')
    result['text'] = values.get('text', '').strip()
    if len(result['text']) > 300 or len(result['text'].splitlines()) > 5:
        raise ValueError('Watermark chữ tối đa 300 ký tự và 5 dòng.')
    if result['kind'] == 'text' and not result['text']:
        raise ValueError('Vui lòng nhập nội dung watermark.')
    result['page_range'] = values.get('page_range', '').strip()
    if result['pages'] == 'custom':
        parse_range(result['page_range'])
    result['link'] = values.get('link', 'https://tailieuonthi.org/').strip()
    if result['link']:
        parsed = urlsplit(result['link'])
        if parsed.scheme not in ('http', 'https') or not parsed.netloc or any(ord(c) < 32 for c in result['link']):
            raise ValueError('Liên kết phải bắt đầu bằng http:// hoặc https:// và có tên miền.')
    prefix = values.get('prefix', '[tailieuonthi.org]').strip()
    result['prefix'] = re.sub(r'[/\\\x00-\x1f:*?"<>|]', '_', prefix)[:80]
    return result


def image_bytes(data, opacity):
    try:
        with Image.open(io.BytesIO(data)) as source:
            if source.format not in ('PNG', 'JPEG', 'WEBP'):
                raise ValueError('Chọn ảnh PNG, JPG hoặc WebP.')
            if source.width * source.height > 25000000:
                raise ValueError('Ảnh quá lớn, tối đa 25 triệu điểm ảnh.')
            img = source.convert('RGBA')
            img.putalpha(img.getchannel('A').point(lambda a: round(a * opacity / 100)))
            stream = io.BytesIO()
            img.save(stream, format='PNG')
            return stream.getvalue(), img.size
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ValueError('Ảnh quá lớn.')
    except (OSError, SyntaxError):
        raise ValueError('Không đọc được ảnh watermark.')



FONT_NAMES = {'sans': 'Arial', 'serif': 'Times New Roman', 'mono': 'Courier New'}


def parse_range(value):
    if not value or len(value) > 300:
        raise ValueError('Nhập trang dạng 1-3, 5, 8-10 (tối đa 300 ký tự).')
    ranges = []
    for part in value.split(','):
        match = re.fullmatch(r'\s*(\d{1,6})(?:\s*-\s*(\d{1,6}))?\s*', part)
        if not match:
            raise ValueError('Khoảng trang không hợp lệ; ví dụ: 1-3, 5, 8-10.')
        start, end = int(match[1]), int(match[2] or match[1])
        if start < 1 or end < start:
            raise ValueError('Khoảng trang phải tăng dần và bắt đầu từ 1.')
        ranges.append((start, end))
    return ranges


def selected_pages(opts, count):
    if opts['pages'] == 'all':
        return set(range(count))
    if opts['pages'] == 'odd':
        return set(range(0, count, 2))
    if opts['pages'] == 'even':
        selected = set(range(1, count, 2))
    else:
        ranges = parse_range(opts['page_range'])
        if any(end > count for start, end in ranges):
            raise ValueError(f'Khoảng trang vượt quá tài liệu {count} trang.')
        selected = {i - 1 for start, end in ranges for i in range(start, end + 1)}
    if not selected:
        raise ValueError('Không có trang phù hợp để thêm watermark.')
    return selected


def text_image(opts):
    name = FONT_NAMES[opts['font']] + (' Bold' if opts['bold'] == 'true' else '')
    candidates = [Path('/System/Library/Fonts/Supplemental') / (name + '.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if opts['bold'] == 'true' else 'DejaVuSans.ttf')]
    path = next((p for p in candidates if p.is_file()), None)
    if path is None:
        raise ValueError('Thiếu font chữ Unicode. Cần cài Arial hoặc DejaVu Sans để dùng watermark chữ.')
    font = ImageFont.truetype(str(path), 160)
    text = opts['text']
    box = ImageDraw.Draw(Image.new('RGBA', (1, 1))).multiline_textbbox((0, 0), text, font=font, spacing=24, align='center')
    width, height = math.ceil(box[2] - box[0] + 20), math.ceil(box[3] - box[1] + 20)
    img = Image.new('RGBA', (width, height))
    ImageDraw.Draw(img).multiline_text((10 - box[0], 10 - box[1]), text, font=font, spacing=24, align='center', fill=opts['color'])
    if width > 2400:
        img = img.resize((2400, max(1, round(height * 2400 / width))), Image.Resampling.LANCZOS)
    return img


def prepare_watermark(raw, opts):
    if opts['kind'] == 'text':
        img = text_image(opts)
    else:
        normalized, _ = image_bytes(raw, 100)
        img = Image.open(io.BytesIO(normalized)).convert('RGBA')
        if opts['tint'] == 'true':
            alpha = img.getchannel('A')
            img = Image.new('RGBA', img.size, opts['color'])
            img.putalpha(alpha)
    # Positive angle is counter-clockwise, matching the slanted reference.
    if opts['angle']:
        # Bound rotated pixel allocation even for large uploaded images.
        img.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
        img = img.rotate(opts['angle'], resample=Image.Resampling.BICUBIC, expand=True)
    if opts['kind'] == 'text' or opts['tint'] == 'true':
        alpha = img.getchannel('A')
        img = Image.new('RGBA', img.size, opts['color'])
        img.putalpha(alpha)
    # Apply opacity after resampling: bicubic interpolation can overshoot alpha.
    img.putalpha(img.getchannel('A').point(lambda a: round(a * opts['opacity'] / 100)))
    stream = io.BytesIO()
    img.save(stream, format='PNG')
    return stream.getvalue(), img.size

def open_pdf(data):
    try:
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception:
        raise ValueError('Không đọc được PDF hoặc file bị hỏng.')
    if not doc.is_pdf or doc.needs_pass:
        doc.close()
        raise ValueError('PDF có mật khẩu hoặc không đúng định dạng; hãy mở khóa trước.')
    if not len(doc):
        doc.close()
        raise ValueError('PDF không có trang.')
    if doc.get_sigflags() > 0:
        doc.close()
        raise ValueError('PDF có chữ ký số; cần dùng bản chưa ký để tránh làm mất hiệu lực chữ ký.')
    return doc


def apply_page(page, image, size, opts):
    if opts['opacity'] == 0:
        return
    # Insertion uses unrotated coordinates; translate from the visible page.
    bounds = page.rect
    margin = min(opts['margin'], bounds.width * .2, bounds.height * .2)
    width = min(bounds.width * opts['width'] / 100, bounds.width - 2 * margin)
    height = min(bounds.height * opts['height'] / 100, bounds.height - 2 * margin)
    scale = min(width / size[0], height / size[1])
    width, height = size[0] * scale, size[1] * scale
    # Nine anchors and optional offsets, clamped so a single stamp stays visible.
    position = opts['position']
    x = margin if position.endswith('-left') else bounds.width - margin - width if position.endswith('-right') else (bounds.width - width) / 2
    y = margin if position.startswith('top') else bounds.height - margin - height if position.startswith('bottom') else (bounds.height - height) / 2
    x = max(0, min(bounds.width - width, x + bounds.width * opts['offset_x'] / 100))
    y = max(0, min(bounds.height - height, y + bounds.height * opts['offset_y'] / 100))
    rects = [fitz.Rect(x, y, x + width, y + height)]
    if opts['layout'] == 'tile':
        dx = width + bounds.width * opts['spacing_x'] / 100
        dy = height + bounds.height * opts['spacing_y'] / 100
        rects = []
        row = 0
        cy = (bounds.height * opts['offset_y'] / 100 - height / 2) % dy - dy
        while cy < bounds.height:
            cx = (bounds.width * opts['offset_x'] / 100 - width / 2 + (dx / 2 if row % 2 else 0)) % dx - dx
            while cx < bounds.width:
                rect = fitz.Rect(cx, cy, cx + width, cy + height)
                if not (rect & bounds).is_empty:
                    rects.append(rect)
                cx += dx
            row += 1
            cy += dy
    # Insertion must use unrotated coordinates. Reset avoids crop-offset bugs.
    derotation, rotation = page.derotation_matrix, page.rotation
    page.set_rotation(0)
    xref = 0
    try:
        for visible_rect in rects:
            rect = visible_rect * derotation
            xref = page.insert_image(rect, stream=image, xref=xref, rotate=rotation, overlay=opts['layer'] == 'above')
            if opts['link']:
                clipped = visible_rect & bounds
                page.insert_link({'kind': fitz.LINK_URI, 'from': clipped * derotation, 'uri': opts['link']})
    finally:
        page.set_rotation(rotation)


def process(data, image, size, opts, progress=None):
    with open_pdf(data) as doc:
        chosen = selected_pages(opts, len(doc))
        if progress:
            progress(0, len(doc))
        for index, page in enumerate(doc):
            if index in chosen:
                apply_page(page, image, size, opts)
            if progress:
                progress(index + 1, len(doc))
        return doc.tobytes(garbage=3, deflate=True), len(doc)


def preview(data, image, size, opts, number=1):
    with open_pdf(data) as doc:
        if number < 1 or number > len(doc):
            raise ValueError(f'Số trang phải từ 1 đến {len(doc)}.')
        page = doc[number - 1]
        if number - 1 in selected_pages(opts, len(doc)):
            apply_page(page, image, size, opts)
        zoom = min(1.4, 1400 / max(page.rect.width, page.rect.height))
        return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png'), len(doc)
