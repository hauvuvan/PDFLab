"""Local-only watermark recipes. Never stores user PDF documents."""
import base64
import json
import os
import uuid
import threading
from pathlib import Path
from watermark import options, prepare_watermark

LOCK = threading.RLock()


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('Mẫu không hợp lệ.')
    name = data.get('name', '')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError('Tên mẫu cần từ 1 đến 80 ký tự.')
    values = data.get('options')
    if not isinstance(values, dict) or any(not isinstance(v, (str, int, float)) for v in values.values()):
        raise ValueError('Cấu hình mẫu không hợp lệ.')
    opts = options(values)
    encoded = data.get('image', '')
    if not isinstance(encoded, str) or len(encoded) > 21 * 1024 * 1024:
        raise ValueError('Ảnh mẫu quá lớn.')
    raw = b''
    if opts['kind'] == 'image':
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            raise ValueError('Dữ liệu ảnh mẫu không hợp lệ.')
        if not raw or len(raw) > 15 * 1024 * 1024:
            raise ValueError('Mẫu ảnh cần kèm logo tối đa 15 MB.')
    prepare_watermark(raw, opts)
    return {'name': name.strip(), 'options': opts, 'image': encoded if opts['kind'] == 'image' else ''}


def read(path):
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(data, list) or len(data) > 30:
            raise ValueError()
        seen = set()
        for row in data:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or row['id'] in seen:
                raise ValueError()
            if not isinstance(row.get('name'), str) or not isinstance(row.get('options'), dict) or not isinstance(row.get('image'), str):
                raise ValueError()
            # Validate shape and options without decoding every logo on each list request.
            if not 1 <= len(row['name'].strip()) <= 80:
                raise ValueError()
            options(row['options'])
            if len(row['image']) > 21 * 1024 * 1024:
                raise ValueError()
            if row['options'].get('kind', 'image') == 'image':
                raw = base64.b64decode(row['image'], validate=True)
                if not raw or len(raw) > 15 * 1024 * 1024:
                    raise ValueError()
            seen.add(row['id'])
        return data
    except (ValueError, OSError):
        raise ValueError('Không đọc được kho mẫu. Hãy sao lưu và kiểm tra file data/presets.json; không tự ghi đè.')


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    if len(serialized.encode('utf-8')) > 64 * 1024 * 1024:
        raise ValueError('Kho mẫu vượt 64 MB. Hãy xóa bớt mẫu ảnh lớn.')
    temp = path.with_suffix('.tmp')
    try:
        temp.write_text(serialized, encoding='utf-8')
        temp.chmod(0o600)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def upsert(path, data):
    with LOCK:
        return _upsert(path, data)


def _upsert(path, data):
    item = validate(data)
    current = read(path)
    item_id = data.get('id')
    existing = next((i for i, row in enumerate(current) if row['id'] == item_id), None)
    if item_id and existing is None:
        raise ValueError('Mẫu cần cập nhật không còn tồn tại.')
    item['id'] = item_id or uuid.uuid4().hex
    if existing is not None:
        current[existing] = item
    else:
        if len(current) >= 30:
            raise ValueError('Tối đa 30 mẫu. Hãy xóa mẫu không dùng.')
        current.append(item)
    save(path, current)
    return item
