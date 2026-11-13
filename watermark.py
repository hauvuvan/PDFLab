"""Watermark engine shared by preview and batch export."""
import io
import math
import re
from urllib.parse import urlsplit
import pymupdf as fitz
from PIL import Image


def options(values):
    result = {}
    for key, default, low, high in [('width', 50, 5, 95), ('height', 10, 1, 80), ('opacity', 100, 1, 100), ('margin', 20, 0, 150)]:
        try:
            value = float(values.get(key, default))
        except (ValueError, TypeError):
            raise ValueError('Thông số kích thước phải là số.')
        if not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'{key} phải nằm trong khoảng {low}–{high}.')
        result[key] = value
    result['position'] = values.get('position', 'bottom')
    if result['position'] not in ('top', 'center', 'bottom'):
        raise ValueError('Vị trí watermark không hợp lệ.')
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
    # Insertion uses unrotated coordinates; translate from the visible page.
    bounds = page.rect
    margin = min(opts['margin'], bounds.width * .2, bounds.height * .2)
    width = min(bounds.width * opts['width'] / 100, bounds.width - 2 * margin)
    height = min(bounds.height * opts['height'] / 100, bounds.height - 2 * margin)
    scale = min(width / size[0], height / size[1])
    width, height = size[0] * scale, size[1] * scale
    x = (bounds.width - width) / 2
    y = {'top': margin, 'center': (bounds.height - height) / 2, 'bottom': bounds.height - margin - height}[opts['position']]
    rect = fitz.Rect(x, y, x + width, y + height) * page.derotation_matrix
    rotation = page.rotation
    # Reset temporarily: rotated cropped pages otherwise lose crop offsets on insertion.
    page.set_rotation(0)
    try:
        page.insert_image(rect, stream=image, rotate=rotation, overlay=True)
        if opts['link']:
            page.insert_link({'kind': fitz.LINK_URI, 'from': rect, 'uri': opts['link']})
    finally:
        page.set_rotation(rotation)


def process(data, image, size, opts, progress=None):
    with open_pdf(data) as doc:
        if progress:
            progress(0, len(doc))
        for index, page in enumerate(doc, 1):
            apply_page(page, image, size, opts)
            if progress:
                progress(index, len(doc))
        return doc.tobytes(garbage=3, deflate=True), len(doc)


def preview(data, image, size, opts, number=1):
    with open_pdf(data) as doc:
        if number < 1 or number > len(doc):
            raise ValueError(f'Số trang phải từ 1 đến {len(doc)}.')
        page = doc[number - 1]
        apply_page(page, image, size, opts)
        zoom = min(1.4, 1400 / max(page.rect.width, page.rect.height))
        return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png'), len(doc)
