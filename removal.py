"""Explicit image-object removal and visible-coordinate region redaction."""
import base64
import json
import math
import re
import fitz
from watermark import open_pdf, selected_pages


def strip_images(stream, names):
    """Tokenize content so apparent operators in strings/comments stay untouched."""
    tokens = []
    i = 0
    delimiters = b'()<>[]{}/%\x00\t\n\f\r '
    while i < len(stream):
        start = i
        c = stream[i]
        if c in b'\x00\t\n\f\r ':
            i += 1
            continue
        if c == 37:  # comment
            while i < len(stream) and stream[i] not in b'\r\n':
                i += 1
            continue
        if c == 40:  # nested literal string, with escaped parentheses
            i += 1
            depth = 1
            while i < len(stream) and depth:
                if stream[i] == 92:
                    i += 2
                    continue
                if stream[i] == 40:
                    depth += 1
                elif stream[i] == 41:
                    depth -= 1
                i += 1
            tokens.append((start, i, 'string'))
            continue
        if c == 60 and stream[i:i+2] != b'<<':
            i = stream.find(b'>', i+1)
            i = len(stream) if i < 0 else i+1
            tokens.append((start, i, 'string'))
            continue
        if c == 47:
            i += 1
            while i < len(stream) and stream[i] not in delimiters:
                i += 1
            kind = 'name'
        elif c in b'<>[]{}':
            i += 1
            kind = 'delimiter'
        else:
            i += 1
            while i < len(stream) and stream[i] not in delimiters:
                i += 1
            kind = 'operator'
        tokens.append((start, i, kind))
    spans = []
    for previous, current in zip(tokens, tokens[1:]):
        a, b, kind = previous
        x, y, op = current
        if kind == 'name' and op == 'operator' and stream[x:y] == b'Do' and stream[a+1:b].decode('ascii', errors='replace') in names:
            spans.append((a, y))
    for a, b in reversed(spans):
        stream = stream[:a] + b' ' + stream[b:]
    return stream, len(spans)


def settings(form):
    try:
        regions = json.loads(form.get('regions', '[]'))
        images = json.loads(form.get('images', '[]'))
        if not isinstance(regions, list) or len(regions) > 30:
            raise ValueError()
        for r in regions:
            if len(r) != 4 or any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or not 0 <= v <= 1 for v in r) or r[2] <= r[0] or r[3] <= r[1]:
                raise ValueError()
        if not isinstance(images, list) or len(images) > 100 or any(not isinstance(x, str) or len(x) != 32 or any(c not in '0123456789abcdef' for c in x) for x in images):
            raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('Vùng xoá hoặc danh sách ảnh không hợp lệ.')
    pages = form.get('pages', 'all')
    if pages not in ('all', 'odd', 'even', 'custom'):
        raise ValueError('Phạm vi trang không hợp lệ.')
    return dict(regions=regions, images=images, pages=pages, page_range=form.get('page_range', ''))


def inspect(data, number):
    with open_pdf(data) as doc:
        if not 1 <= number <= len(doc):
            raise ValueError(f'Số trang phải từ 1 đến {len(doc)}.')
        page = doc[number-1]
        candidates = []
        seen = set()
        has_inline = any(not i['xref'] for i in page.get_image_info(xrefs=True))
        direct = set() if has_inline else {i[0] for i in page.get_images(full=True) if i[9] == 0 and re.fullmatch(r'[A-Za-z0-9_.-]+', i[7])}
        for image in page.get_image_info(hashes=True, xrefs=True):
            digest = image['digest'].hex()
            if image['xref'] not in direct or digest in seen:
                continue
            seen.add(digest)
            rect = fitz.Rect(image['bbox']) * page.rotation_matrix
            candidates.append(dict(id=digest, rect=[rect.x0/page.rect.width, rect.y0/page.rect.height, rect.x1/page.rect.width, rect.y1/page.rect.height], width=image['width'], height=image['height']))
        zoom = min(1.5, 1400/max(page.rect.width, page.rect.height))
        png = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png')
        return dict(pages=len(doc), image=base64.b64encode(png).decode(), candidates=candidates)


def apply(doc, opts):
    chosen = selected_pages(opts, len(doc))
    removed = 0
    for index in chosen:
        page = doc[index]
        info = page.get_image_info(hashes=True, xrefs=True)
        if opts['images'] and any(not i['xref'] for i in info) and any(i['digest'].hex() in opts['images'] for i in info):
            raise ValueError('Trang có ảnh inline; hãy bỏ lựa chọn ảnh và dùng khoanh vùng trên trang này.')
        # Clean into an isolated content stream, then remove only direct image Do
        # operators. Resource data can be shared across pages without being changed.
        page.clean_contents()
        direct = {i[0]: i[7] for i in page.get_images(full=True)
                  if i[9] == 0 and re.fullmatch(r'[A-Za-z0-9_.-]+', i[7])}
        names = {direct[i['xref']] for i in page.get_image_info(hashes=True, xrefs=True)
                 if i['xref'] in direct and i['digest'].hex() in opts['images']}
        if names:
            stream = b'\n'.join(doc.xref_stream(x) for x in page.get_contents())
            stream, count = strip_images(stream, names)
            removed += count
            xref = doc.get_new_xref()
            doc.update_object(xref, '<<>>')
            doc.update_stream(xref, stream)
            page.set_contents(xref)
        for region in opts['regions']:
            bounds = page.rect
            visible = fitz.Rect(region[0]*bounds.width, region[1]*bounds.height, region[2]*bounds.width, region[3]*bounds.height)
            page.add_redact_annot(visible * page.derotation_matrix, fill=(1,1,1), cross_out=False)
        if opts['regions']:
            page.apply_redactions(images=2, graphics=1, text=0)
    return removed


def process(data, opts, number=None):
    with open_pdf(data) as doc:
        if not opts['regions'] and not opts['images']:
            raise ValueError('Hãy chọn ảnh có sẵn hoặc khoanh ít nhất một vùng cần xoá.')
        if number is not None and not 1 <= number <= len(doc):
            raise ValueError(f'Số trang phải từ 1 đến {len(doc)}.')
        removed = apply(doc, opts)
        if number is not None:
            page = doc[number-1]
            zoom = min(1.5, 1400/max(page.rect.width, page.rect.height))
            return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False).tobytes('png'), removed
        return doc.tobytes(garbage=4, deflate=True), removed
