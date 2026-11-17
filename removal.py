"""Explicit image-object removal and visible-coordinate region redaction."""
import base64
import io
import json
import math
from pathlib import Path
import re
import zipfile
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


def remove_object_images(doc, page, targets):
    """Clone form/resources per selected page before modifying nested streams."""
    count = 0
    def dictionary(kind, value):
        if kind == 'xref':
            return doc.xref_object(int(value.split()[0]))
        if kind == 'dict':
            return value
        raise ValueError('Nhóm ảnh có cấu trúc tài nguyên chưa hỗ trợ; hãy khoanh vùng.')
    def clone(owner, stream, active):
        nonlocal count
        if owner in active or len(active) > 30:
            raise ValueError('Nhóm ảnh lồng quá sâu hoặc có vòng lặp; hãy khoanh vùng.')
        active = active | {owner}
        kind, value = doc.xref_get_key(owner, 'Resources')
        if kind == 'null' and owner == page.xref:
            parent = owner
            visited = set()
            while kind == 'null':
                if parent in visited:
                    raise ValueError('Cấu trúc trang có vòng lặp.')
                visited.add(parent)
                p_kind, p_value = doc.xref_get_key(parent, 'Parent')
                if p_kind != 'xref':
                    break
                parent = int(p_value.split()[0])
                kind, value = doc.xref_get_key(parent, 'Resources')
        if kind == 'null':
            raise ValueError('Nhóm ảnh không có tài nguyên riêng; hãy dùng khoanh vùng.')
        resource = doc.get_new_xref()
        doc.update_object(resource, dictionary(kind, value))
        kind, value = doc.xref_get_key(resource, 'XObject')
        if kind == 'null':
            return stream
        objects = doc.get_new_xref()
        doc.update_object(objects, dictionary(kind, value))
        doc.xref_set_key(resource, 'XObject', f'{objects} 0 R')
        doc.xref_set_key(owner, 'Resources', f'{resource} 0 R')
        names = set()
        for name in doc.xref_get_keys(objects):
            kind, value = doc.xref_get_key(objects, name)
            if kind != 'xref':
                continue
            ref = int(value.split()[0])
            if ref in targets:
                if not re.fullmatch(r'[A-Za-z0-9_.-]+', name):
                    raise ValueError('Tên đối tượng ảnh chưa hỗ trợ; hãy khoanh vùng.')
                names.add(name)
            elif doc.xref_get_key(ref, 'Subtype')[1] == '/Form':
                if ref in active:
                    raise ValueError('Nhóm ảnh có vòng lặp; hãy khoanh vùng.')
                duplicate = doc.get_new_xref()
                doc.update_object(duplicate, doc.xref_object(ref))
                # Carry original ancestors through recursion to detect shared cycles.
                content = clone(duplicate, doc.xref_stream(ref), active | {ref})
                doc.update_stream(duplicate, content)
                doc.xref_set_key(objects, name, f'{duplicate} 0 R')
        stream, removed = strip_images(stream, names)
        count += removed
        return stream
    original = b'\n'.join(doc.xref_stream(x) for x in page.get_contents())
    result = clone(page.xref, original, set())
    new = doc.get_new_xref()
    doc.update_object(new, '<<>>')
    doc.update_stream(new, result)
    page.set_contents(new)
    return count


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
        direct = set() if has_inline else {i[0] for i in page.get_images(full=True) if re.fullmatch(r'[A-Za-z0-9_.-]+', i[7])}
        for image in page.get_image_info(hashes=True, xrefs=True):
            digest = image['digest'].hex()
            if image['xref'] not in direct or digest in seen:
                continue
            seen.add(digest)
            rect = (fitz.Rect(image['bbox']) * page.rotation_matrix) & page.rect
            if rect.is_empty:
                continue
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
        targets = {i['xref'] for i in info if i['xref'] and i['digest'].hex() in opts['images']}
        if targets:
            removed += remove_object_images(doc, page, targets)
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


def batch_process(files, opts):
    if not opts['regions'] and not opts['images']:
        raise ValueError('Hãy chọn ảnh có sẵn hoặc khoanh ít nhất một vùng cần xoá.')
    if not files:
        raise ValueError('Vui lòng chọn ít nhất một file PDF.')
    bio = io.BytesIO()
    reports = []
    used = set()
    with zipfile.ZipFile(bio, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in files:
            if not name.lower().endswith('.pdf'):
                reports.append(dict(file=name, status='error', error='File không có định dạng PDF.'))
                continue
            try:
                with open_pdf(data) as doc:
                    count = apply(doc, opts)
                    output_bytes = doc.tobytes(garbage=4, deflate=True)
                    pages = len(doc)
                stem = Path(name).stem
                desired = f'{stem}_da_xoa_watermark.pdf'
                candidate, index = desired, 2
                while candidate.casefold() in used:
                    candidate = f'{stem}_da_xoa_watermark ({index}).pdf'
                    index += 1
                used.add(candidate.casefold())
                archive.writestr(candidate, output_bytes)
                reports.append(dict(file=name, output=candidate, status='ok', pages=pages, removed_images=count))
            except Exception as exc:
                reports.append(dict(file=name, status='error', error=str(exc) if isinstance(exc, ValueError) else 'Không xử lý được file PDF này.'))
        archive.writestr('bao-cao.json', json.dumps(reports, ensure_ascii=False, indent=2))
    bio.seek(0)
    return bio.getvalue(), reports

