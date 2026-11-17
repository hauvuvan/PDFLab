import io
import json
import os
import zipfile
from pathlib import Path
from flask import Request, Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge
from watermark import options, prepare_watermark, process, preview
import presets
import jobs
from upload_stream import DiskUpload
from runtime_version import SOURCE_VERSION, PROJECT_ID
import word_converter

class PDFRequest(Request):
    """Watermark batches spool to disk without a batch size or part-count cap."""
    @property
    def max_content_length(self):
        if self.path in ('/api/jobs', '/api/preview'):
            return None
        return super().max_content_length

    @property
    def max_form_parts(self):
        if self.path in ('/api/jobs', '/api/preview'):
            return None
        return super().max_form_parts

    def _get_file_stream(self, total_content_length, content_type, filename=None, content_length=None):
        if self.path in ('/api/jobs', '/api/preview'):
            return DiskUpload()
        return super()._get_file_stream(total_content_length, content_type, filename, content_length)


app = Flask(__name__)
app.request_class = PDFRequest
app.config.update(MAX_CONTENT_LENGTH=200 * 1024 * 1024, MAX_FORM_MEMORY_SIZE=1024 * 1024,
                  PRESETS_PATH=Path(__file__).parent / 'data' / 'presets.json')


@app.before_request
def local_only():
    if request.host.split(':')[0] not in ('127.0.0.1', 'localhost'):
        return jsonify(error='Công cụ chỉ phục vụ trên máy này.'), 403
    if request.method in ('POST', 'DELETE'):
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


@app.get('/remove-watermark')
def removal_editor():
    return render_template('removal.html')


@app.post('/api/removal/<action>')
def removal_action(action):
    import removal
    if action not in ('inspect', 'preview', 'export', 'batch'):
        return jsonify(error='Không tìm thấy thao tác.'), 404
    try:
        with jobs.ENGINE_LOCK:
            if action == 'batch':
                files = request.files.getlist('pdfs')
                if not files:
                    single = request.files.get('pdf')
                    if single:
                        files = [single]
                if not files:
                    raise ValueError('Vui lòng chọn ít nhất một file PDF.')
                data_list = []
                for f in files:
                    name = (f.filename or 'document.pdf').replace('\\', '/').split('/')[-1]
                    name = ''.join(c for c in name if ord(c) >= 32)[:180] or 'document.pdf'
                    data_list.append((name, f.read()))
                opts = removal.settings(request.form)
                zip_bytes, reports = removal.batch_process(data_list, opts)
                ok_count = sum(1 for r in reports if r['status'] == 'ok')
                response = send_file(io.BytesIO(zip_bytes), mimetype='application/zip',
                                     as_attachment=True, download_name='da-xoa-watermark-hang-loat.zip')
                response.headers['X-Success-Count'] = str(ok_count)
                response.headers['X-Total-Count'] = str(len(reports))
                return response

            pdf = request.files.get('pdf')
            if not pdf or not pdf.filename.lower().endswith('.pdf'):
                raise ValueError('Vui lòng chọn PDF.')
            data = pdf.read()
            try:
                number = int(request.form.get('page', '1'))
            except ValueError:
                raise ValueError('Số trang không hợp lệ.')
            if action == 'inspect':
                return jsonify(removal.inspect(data, number))
            opts = removal.settings(request.form)
            result, count = removal.process(data, opts, number if action == 'preview' else None)
            stem = Path(pdf.filename or 'tai-lieu.pdf').stem
            download_name = f'{stem}_da_xoa_watermark.pdf'
            response = send_file(io.BytesIO(result), mimetype='image/png' if action == 'preview' else 'application/pdf',
                                 as_attachment=action == 'export', download_name=download_name)
            response.headers['X-Removed-Images'] = str(count)
            return response
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.get('/pdf-to-images')
@app.get('/images-to-pdf')
def image_tools():
    return render_template('images.html', to_images=request.path == '/pdf-to-images')


@app.post('/api/pdf-to-images')
@app.post('/api/images-to-pdf')
def convert_images():
    import image_converter
    try:
        with jobs.ENGINE_LOCK:
            if request.path == '/api/pdf-to-images':
                pdf = request.files.get('pdf')
                if not pdf or not pdf.filename.lower().endswith('.pdf'):
                    raise ValueError('Vui lòng chọn một PDF.')
                try:
                    dpi = int(request.form.get('dpi', '150'))
                except ValueError:
                    raise ValueError('DPI không hợp lệ.')
                result = image_converter.pdf_to_images(pdf.read(), request.form.get('format', 'png'), dpi)
                mime, name = 'application/zip', 'pdf-sang-anh.zip'
            else:
                files = request.files.getlist('images')
                if not 1 <= len(files) <= 100:
                    raise ValueError('Chọn từ 1 đến 100 ảnh.')
                result = image_converter.images_to_pdf([(f.filename, f.read()) for f in files], request.form.get('paper', 'a4'))
                mime, name = 'application/pdf', 'anh-da-ghep.pdf'
        return send_file(io.BytesIO(result), mimetype=mime, as_attachment=True, download_name=name)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400


@app.get('/health')
def health():
    with jobs.LOCK:
        active = sum(job['state'] in ('queued', 'running') for job in jobs.JOBS.values())
    return jsonify(status='ok', version='1.2.0', app='PDFLabs', source_version=SOURCE_VERSION,
                   project_id=PROJECT_ID, pid=os.getpid(), active_jobs=active,
                   engine_busy=jobs.ENGINE_LOCK.locked())


def inputs():
    opts = options(request.form)
    raw = b''
    if opts['kind'] == 'image':
        image = request.files.get('watermark')
        if not image or not image.filename:
            raise ValueError('Vui lòng chọn ảnh watermark.')
        raw = image.read(15 * 1024 * 1024 + 1)
        if len(raw) > 15 * 1024 * 1024:
            raise ValueError('Ảnh watermark tối đa 15 MB.')
    data, size = prepare_watermark(raw, opts)
    return opts, data, size


@app.get('/api/presets')
def list_presets():
    try:
        return jsonify(presets=presets.read(Path(app.config['PRESETS_PATH'])))
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.post('/api/presets')
def save_preset():
    try:
        data = request.get_json(silent=True)
        item = presets.upsert(Path(app.config['PRESETS_PATH']), data)
        return jsonify(preset=item)
    except (ValueError, TypeError) as e:
        return jsonify(error=str(e)), 400
    except OSError:
        return jsonify(error='Không ghi được kho mẫu trên máy. Kiểm tra quyền thư mục data.'), 500


@app.delete('/api/presets/<preset_id>')
def delete_preset(preset_id):
    try:
        path = Path(app.config['PRESETS_PATH'])
        with presets.LOCK:
            current = presets.read(path)
            remaining = [row for row in current if row['id'] != preset_id]
            if len(current) == len(remaining):
                return jsonify(error='Không tìm thấy mẫu.'), 404
            presets.save(path, remaining)
        return jsonify(ok=True)
    except ValueError as e:
        return jsonify(error=str(e)), 400
    except OSError:
        return jsonify(error='Không ghi được kho mẫu.'), 500


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
        with jobs.ENGINE_LOCK:
            png, pages = preview(pdf.read(), image, size, opts, number)
        response = send_file(io.BytesIO(png), mimetype='image/png')
        response.headers['X-Page-Count'] = str(pages)
        return response
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.post('/api/jobs')
def create_job():
    try:
        opts, image, size = inputs()
        files = request.files.getlist('pdfs')
        if not files:
            raise ValueError('Chọn ít nhất một file PDF.')
        return jsonify(id=jobs.submit(files, image, size, opts, uploads=True)), 202
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except (OSError, RuntimeError):
        app.logger.exception('Could not stage or queue watermark batch')
        return jsonify(error='Không lưu hoặc khởi tạo được lượt xử lý. Kiểm tra dung lượng ổ đĩa và thử lại.'), 503


@app.get('/api/word/status')
def word_status():
    return jsonify(available=bool(word_converter.executable()))


@app.post('/api/word/jobs')
def create_word_job():
    files = request.files.getlist('documents')
    if not files or len(files) > 100:
        return jsonify(error='Chọn từ 1 đến 100 file Word mỗi lượt.'), 400
    if not word_converter.executable():
        return jsonify(error='Cần cài LibreOffice hoặc đặt LIBREOFFICE_PATH rồi khởi động lại công cụ.'), 503
    data = []
    for document in files:
        name = (document.filename or 'document.docx').replace('\\', '/').split('/')[-1]
        name = ''.join(c for c in name if ord(c) >= 32)[:180] or 'document.docx'
        data.append((name, document.read()))
    return jsonify(id=jobs.submit(data, None, None, {}, converter=word_converter.convert)), 202


@app.get('/api/jobs/<key>')
def job_status(key):
    job = jobs.snapshot(key)
    if not job:
        return jsonify(error='Không tìm thấy lượt chạy; ứng dụng có thể đã khởi động lại.'), 404
    return jsonify(job)


@app.get('/api/jobs/<key>/<kind>')
def job_download(key, kind):
    if len(key) != 32 or any(c not in '0123456789abcdef' for c in key) or kind not in ('log', 'result'):
        return jsonify(error='Không tìm thấy tài nguyên.'), 404
    folder = jobs.ROOT / key
    if not folder.is_dir():
        return jsonify(error='Kết quả đã hết hạn hoặc không tồn tại.'), 404
    job = jobs.snapshot(key)
    if kind == 'result' and (not job or job['state'] != 'completed' or not job['success']):
        return jsonify(error='Chưa có ZIP thành công để tải.'), 409
    path = folder / ('progress.jsonl' if kind == 'log' else 'result.zip')
    return send_file(path, as_attachment=True, download_name=f'{key}-tien-trinh.jsonl' if kind == 'log' else ('word-sang-pdf.zip' if job and job.get('tool') == 'word' else 'pdf-watermark.zip'))


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
                    with jobs.ENGINE_LOCK:
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
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 8765)), debug=False, threaded=True)
