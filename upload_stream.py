"""Disk-backed multipart streams that do not hold one open descriptor per file."""
import io
import os
import tempfile
from pathlib import Path


class DiskUpload(io.IOBase):
    def __init__(self):
        super().__init__()
        fd, name = tempfile.mkstemp(prefix='pdflabs-upload-')
        os.close(fd)
        self.path = Path(name)
        self.position = 0

    def _open(self):
        if self.closed:
            raise ValueError('I/O operation on closed upload')
        return self.path.open('r+b')

    def write(self, data):
        with self._open() as stream:
            stream.seek(self.position)
            count = stream.write(data)
            self.position = stream.tell()
            return count

    def read(self, size=-1):
        with self._open() as stream:
            stream.seek(self.position)
            data = stream.read(size)
            self.position = stream.tell()
            return data

    def seek(self, offset, whence=0):
        with self._open() as stream:
            stream.seek(self.position)
            self.position = stream.seek(offset, whence)
            return self.position

    def tell(self):
        return self.position

    def close(self):
        try:
            if hasattr(self, 'path'):
                self.path.unlink(missing_ok=True)
        finally:
            super().close()
