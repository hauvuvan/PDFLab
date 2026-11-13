"""Build a local launcher bundle. Installation is a separate, explicit step."""
import os
from pathlib import Path
import plistlib
import shlex
import sys
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build(destination):
    app = Path(destination) / 'PDFLabs.app'
    if app.exists():
        raise FileExistsError('PDFLabs.app đã tồn tại ở đích; không ghi đè tự động.')
    executable = app / 'Contents/MacOS/PDFLabs'
    executable.parent.mkdir(parents=True)
    python = ROOT / '.venv/bin/python'
    command = shlex.quote(str(python)) + ' ' + shlex.quote(str(ROOT / 'scripts/launch_pdflabs.py'))
    wrapper = app / 'Contents/Resources/launch.sh'
    wrapper.parent.mkdir(parents=True)
    wrapper.write_text('#!/bin/zsh\n' + 'result=$(' + command + ' 2>&1)\n' +
                          'if [ $? -ne 0 ]; then\n  /usr/bin/osascript - "$result" <<\'APPLESCRIPT\'\n' +
                          'on run argv\n display alert "PDFLabs" message (item 1 of argv) as critical\nend run\nAPPLESCRIPT\nfi\n')
    wrapper.chmod(0o755)
    # Launch Services requires a native executable on current macOS.
    source = r'''#include <mach-o/dyld.h>
#include <libgen.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <unistd.h>
int main(void) {
  char binary[PATH_MAX], script[PATH_MAX]; uint32_t size=sizeof(binary);
  if (_NSGetExecutablePath(binary, &size) != 0) return 1;
  if (snprintf(script, sizeof(script), "%s/../Resources/launch.sh", dirname(binary)) >= sizeof(script)) return 1;
  execl("/bin/zsh", "zsh", script, (char *)0);
  return 1;
}
'''
    with tempfile.TemporaryDirectory(prefix='pdflabs-build-') as temporary:
        cfile = Path(temporary) / 'launcher.c'
        cfile.write_text(source)
        subprocess.run(['/usr/bin/clang', str(cfile), '-o', str(executable)], check=True)
    executable.chmod(0o755)
    with (app / 'Contents/Info.plist').open('wb') as stream:
        plistlib.dump({'CFBundleName': 'PDFLabs', 'CFBundleDisplayName': 'PDFLabs',
                      'CFBundleIdentifier': 'local.pdflabs.launcher', 'CFBundleVersion': '1',
                      'CFBundleShortVersionString': '1.0', 'CFBundlePackageType': 'APPL',
                      'CFBundleExecutable': 'PDFLabs', 'LSUIElement': True,
                      'NSHighResolutionCapable': True}, stream)
    print(app)
    return app


if __name__ == '__main__':
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'output/macos')
