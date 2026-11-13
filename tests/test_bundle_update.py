"""Verify a bundle update preserves the installed app until replacement is ready."""
import importlib.util
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('build_macos_app', Path(__file__).parents[1] / 'scripts/build_macos_app.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BundleUpdateTests(unittest.TestCase):
    def old_app(self, root, identifier='local.pdflabs.launcher'):
        app = Path(root) / 'PDFLabs.app'
        (app / 'Contents').mkdir(parents=True)
        (app / 'old-version').write_text('old app remains usable')
        with (app / 'Contents/Info.plist').open('wb') as stream:
            plistlib.dump({'CFBundleIdentifier': identifier}, stream)
        return app

    @staticmethod
    def fake_compile(command, **kwargs):
        output = Path(command[command.index('-o') + 1])
        output.write_bytes(b'new launcher executable')
        return subprocess.CompletedProcess(command, 0)

    def test_update_replaces_only_installed_bundle_after_success(self):
        with tempfile.TemporaryDirectory() as root:
            old = self.old_app(root)
            with patch.object(builder.subprocess, 'run', side_effect=self.fake_compile):
                result = builder.build(root)
            self.assertEqual(result, old)
            self.assertFalse((old / 'old-version').exists())
            self.assertEqual((old / 'Contents/MacOS/PDFLabs').read_bytes(), b'new launcher executable')
            self.assertEqual(sorted(p.name for p in Path(root).iterdir()), ['PDFLabs.app'])
            with (old / 'Contents/Info.plist').open('rb') as stream:
                self.assertEqual(plistlib.load(stream)['CFBundleIdentifier'], 'local.pdflabs.launcher')

    def test_compile_failure_keeps_old_bundle_and_cleans_staging(self):
        with tempfile.TemporaryDirectory() as root:
            old = self.old_app(root)
            with patch.object(builder.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'clang')):
                with self.assertRaises(subprocess.CalledProcessError):
                    builder.build(root)
            self.assertEqual((old / 'old-version').read_text(), 'old app remains usable')
            self.assertEqual(sorted(p.name for p in Path(root).iterdir()), ['PDFLabs.app'])

    def test_install_rename_failure_restores_old_bundle(self):
        with tempfile.TemporaryDirectory() as root:
            old = self.old_app(root)
            rename = Path.rename
            def fail_replacement(path, target):
                if path.name == 'PDFLabs.app' and path.parent.name.startswith('.pdflabs-update-'):
                    raise OSError('simulated install failure')
                return rename(path, target)
            with patch.object(builder.subprocess, 'run', side_effect=self.fake_compile), patch.object(Path, 'rename', fail_replacement):
                with self.assertRaises(OSError):
                    builder.build(root)
            self.assertEqual((old / 'old-version').read_text(), 'old app remains usable')
            self.assertEqual(sorted(p.name for p in Path(root).iterdir()), ['PDFLabs.app'])

    def test_unrelated_bundle_is_never_replaced(self):
        with tempfile.TemporaryDirectory() as root:
            old = self.old_app(root, 'other.owner.app')
            with patch.object(builder.subprocess, 'run') as compile_call:
                with self.assertRaises((ValueError, FileExistsError)):
                    builder.build(root)
                compile_call.assert_not_called()
            self.assertEqual((old / 'old-version').read_text(), 'old app remains usable')


if __name__ == '__main__':
    unittest.main()
