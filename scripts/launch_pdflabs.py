"""Open the local PDFLabs workspace without a Terminal window."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request
import signal
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_version import source_version, PROJECT_ID

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://127.0.0.1:8765'


def server_state():
    try:
        with urllib.request.urlopen(URL + '/health', timeout=1) as response:
            healthy = json.load(response).get('status') == 'ok'
        with urllib.request.urlopen(URL, timeout=1) as response:
            page = response.read(8192).decode('utf-8', errors='replace')
        return 'ready' if healthy and ('PDFLabs' in page or 'Paperdesk' in page) else 'occupied'
    except urllib.error.URLError as error:
        return 'stopped' if isinstance(error.reason, ConnectionRefusedError) else 'occupied'
    except (OSError, ValueError):
        return 'occupied'


def main():
    output = ROOT / 'output'
    output.mkdir(exist_ok=True)
    with (output / 'launcher.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = server_state()
        if state == 'ready':
            with urllib.request.urlopen(URL + '/health', timeout=2) as response:
                identity = json.load(response)
            if identity.get('source_version') != source_version():
                if identity.get('project_id') != PROJECT_ID or not isinstance(identity.get('pid'), int):
                    raise RuntimeError('Phiên cũ chưa hỗ trợ cập nhật. Đóng phiên app.py cũ rồi mở PDFLabs lại.')
                if identity.get('active_jobs') or identity.get('engine_busy'):
                    raise RuntimeError('Có bản cập nhật. Chờ xử lý tài liệu hoàn tất rồi mở PDFLabs lại.')
                os.kill(identity['pid'], signal.SIGTERM)
                for _ in range(100):
                    if server_state() == 'stopped':
                        state = 'stopped'
                        break
                    time.sleep(.1)
                else:
                    raise RuntimeError('Phiên cũ chưa dừng. Thử mở PDFLabs lại sau.')
        if state == 'occupied':
            raise RuntimeError('Cổng 8765 đang được ứng dụng khác sử dụng. Đóng ứng dụng đó rồi mở PDFLabs lại.')
        if state == 'stopped':
            python = ROOT / '.venv/bin/python'
            if not python.is_file():
                raise RuntimeError('Chạy start.command trong thư mục dự án một lần để cài thư viện, rồi mở PDFLabs lại.')
            with (output / 'launcher.log').open('ab') as log:
                process = subprocess.Popen([str(python), 'app.py'], cwd=ROOT,
                                           env={**os.environ, 'PORT': '8765'},
                                           stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                           start_new_session=True)
            for _ in range(100):
                if server_state() == 'ready':
                    break
                if process.poll() is not None:
                    raise RuntimeError('Không khởi động được PDFLabs. Xem output/launcher.log trong thư mục dự án.')
                time.sleep(.2)
            else:
                raise RuntimeError('PDFLabs chưa sẵn sàng. Xem output/launcher.log rồi thử mở lại.')
        subprocess.run(['open', URL], check=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
