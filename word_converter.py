"""Convert Word files locally using an isolated LibreOffice profile per file."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import fitz


def executable():
    configured = os.environ.get('LIBREOFFICE_PATH')
    candidates = [configured] if configured else [
        shutil.which('soffice'), shutil.which('libreoffice'),
        '/Applications/LibreOffice.app/Contents/MacOS/soffice',
    ]
    return next((str(p) for p in candidates if p and Path(p).is_file() and os.access(p, os.X_OK)), None)


def convert(raw, name):
    suffix = Path(name).suffix.lower()
    if suffix not in ('.doc', '.docx'):
        raise ValueError('Chỉ hỗ trợ file Word .doc hoặc .docx.')
    if not raw:
        raise ValueError('File Word rỗng.')
    binary = executable()
    if not binary:
        raise ValueError('Chưa tìm thấy LibreOffice. Cài LibreOffice rồi khởi động lại công cụ, hoặc đặt LIBREOFFICE_PATH.')
    with tempfile.TemporaryDirectory(prefix='paperdesk-word-') as directory:
        root = Path(directory)
        source = root / ('document' + suffix)
        source.write_bytes(raw)
        output = root / 'out'
        output.mkdir()
        try:
            completed = subprocess.run([
                binary, '-env:UserInstallation=' + (root / 'profile').as_uri(),
                '--headless', '--convert-to', 'pdf:writer_pdf_Export',
                '--outdir', str(output), str(source),
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, check=False)
        except subprocess.TimeoutExpired:
            raise ValueError('Chuyển đổi quá 120 giây. Hãy thử lại với tài liệu nhỏ hơn.')
        except OSError:
            raise ValueError('Không khởi chạy được LibreOffice. Kiểm tra cài đặt và LIBREOFFICE_PATH.')
        pdf = output / 'document.pdf'
        if completed.returncode or not pdf.is_file():
            raise ValueError('Không chuyển được file Word. Kiểm tra file hỏng, mật khẩu hoặc định dạng không hợp lệ.')
        result = pdf.read_bytes()
        try:
            with fitz.open(stream=result, filetype='pdf') as document:
                pages = len(document)
                if not pages:
                    raise ValueError('PDF kết quả không có trang.')
        except fitz.FileDataError:
            raise ValueError('Bộ chuyển đổi không tạo được PDF hợp lệ.')
        return result, pages
