"""Identity of the source loaded by a local PDFLabs process."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def source_version(root=ROOT):
    files = list(root.glob('*.py')) + [root / 'requirements.txt']
    for folder in ('templates', 'static'):
        files.extend(p for p in (root / folder).rglob('*') if p.is_file())
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


SOURCE_VERSION = source_version()
PROJECT_ID = hashlib.sha256(str(ROOT).encode()).hexdigest()
