import io
import json
import os
import zipfile
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from watermark import options, image_bytes, process, preview

app = Flask(__name__)
app.config.update(MAX_CONTENT_LENGTH=200 * 1024 * 1024, MAX_FORM_MEMORY_SIZE=1024 * 1024)


@app.before_request
def local_only():
    if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
        return jsonify(error='Công cụ chỉ phục vụ trên máy này.'), 403
    if request.method == 'POST':
        origin = request.headers.get('Origin')
        if origin and origin != request.host_url.rstrip('/'):
            return jsonify(error='Yêu cầu không hợp lệ.'), 403


@app.after_request
def headers(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/health')
def health():
    return jsonify(status='ok', version='1.0.0')


def inputs():
    opts = options(request.form)
    image = request.files.get('watermark')
    if not image or not image.filename:
        raise ValueError('Vui lòng chọn ảnh watermark.')
    raw = image.read(15 * 1024 * 1024 + 1)
    if len(raw) > 15 * 1024 * 1024:
        raise ValueError('Ảnh watermark tối đa 15 MB.')
    data, size = image_bytes(raw, opts['opacity'])
    return opts, data, size


@app.post('/api/preview')
def make_preview():
    try:
        opts, image, size = inputs()
        pdf = request.files.get('pdf')
        if not pdf or not pdf.filename.lower().endswith('.pdf'):
            raise ValueError('Vui lòng chọn file PDF để xem trước.')
        try:
            number = int(request.form.get('page', '1'))
        except ValueError:
            raise ValueError('Số trang không hợp lệ.')
        png, pages = preview(pdf.read(), image, size, opts, number)
        response = send_file(io.BytesIO(png), mimetype='image/png')
        response.headers['X-Page-Count'] = str(pages)
        return response
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.post('/api/process')
def batch():
    try:
        opts, image, size = inputs()
        files = request.files.getlist('pdfs')
        if not files or len(files) > 100:
            raise ValueError('Chọn từ 1 đến 100 file PDF mỗi lượt.')
        reports, used = [], set()
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            for pdf in files:
                name = (pdf.filename or 'document.pdf').replace('\\', '/').split('/')[-1]
                name = ''.join(c for c in name if ord(c) >= 32)[:180]
                try:
                    if not name.lower().endswith('.pdf'):
                        raise ValueError('File không có phần mở rộng PDF.')
                    result, pages = process(pdf.read(), image, size, opts)
                    desired = opts['prefix'] + name
                    candidate, index = desired, 2
                    while candidate.casefold() in used:
                        candidate = f'{Path(desired).stem} ({index}).pdf'
                        index += 1
                    used.add(candidate.casefold())
                    archive.writestr(candidate, result)
                    reports.append(dict(file=name, output=candidate, status='ok', pages=pages))
                except Exception as exc:
                    message = str(exc) if isinstance(exc, ValueError) else 'Không xử lý được file PDF này.'
                    reports.append(dict(file=name, status='error', error=message))
            success = sum(r['status'] == 'ok' for r in reports)
            archive.writestr('bao-cao.json', json.dumps(reports, ensure_ascii=False, indent=2))
        if not success:
            return jsonify(error='Không có file nào xử lý thành công.', reports=reports), 400
        output.seek(0)
        response = send_file(output, mimetype='application/zip', as_attachment=True, download_name='pdf-watermark.zip')
        response.headers['X-Success-Count'] = str(success)
        response.headers['X-Failure-Count'] = str(len(reports) - success)
        summary = json.dumps(reports, ensure_ascii=True)
        response.headers['X-Reports'] = summary if len(summary) < 6000 else '[]'
        return response
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.errorhandler(RequestEntityTooLarge)
def too_large(error):
    return jsonify(error='Tổng dung lượng tải lên vượt 200 MB. Hãy chia thành nhiều lượt.'), 413


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 8765)), debug=False, threaded=False)
