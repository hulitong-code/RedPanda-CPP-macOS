#!/usr/bin/env python3
"""Exercise app replacement and settings preservation in disposable directories."""
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / 'packages/macos/cleanup-apps.py'
SEED = ROOT / 'packages/macos/seed-settings.py'


def bundle(path, executable='RedPandaIDE'):
    (path / 'Contents').mkdir(parents=True)
    with (path / 'Contents/Info.plist').open('wb') as file:
        plistlib.dump({'CFBundleExecutable': executable}, file)


class InstallCleanup(unittest.TestCase):
    def test_replacement_and_migration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            scan = root / 'apps'
            old = scan / 'Old.app'
            stage = scan / 'Stage.app'
            other = scan / 'Other.app'
            for path, name in ((old, 'RedPandaIDE'), (stage, 'RedPandaIDE'), (other, 'Other')):
                bundle(path, name)
            manifest = root / 'moved.json'
            cmd = ['python3', str(CLEAN), '--search-root', str(scan), '--trash-root', str(root / '.Trash'),
                   '--protect', str(stage), '--manifest', str(manifest)]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertFalse(old.exists())
            self.assertTrue(stage.exists())
            self.assertTrue(other.exists())
            moves = json.loads(manifest.read_text())
            self.assertEqual(len(moves), 1)
            self.assertTrue(Path(moves[0]['to']).exists())
            ini = root / 'preferences.ini'
            ini.write_text('[Environment]\nlanguage=zh_CN\n[CompilerSet_0]\n'
                           f'cppcompiler={old}/Contents/MacOS/gcc/bin/g++\nC=/opt/custom/include\n')
            subprocess.run(['python3', str(SEED), '--output', str(ini), '--app', str(stage),
                            '--moved-manifest', str(manifest)], check=True, capture_output=True)
            text = ini.read_text()
            self.assertIn('language=zh_CN', text)
            self.assertIn('C=/opt/custom/include', text)
            self.assertIn(str(stage) + '/Contents/MacOS/gcc/bin/g++', text)
            self.assertEqual(len(list(root.glob('*.before-relocation-*'))), 1)

    def test_unrelated_destination_rejected_before_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old, unrelated = root / 'Old.app', root / 'Other.app'
            bundle(old)
            bundle(unrelated, 'Other')
            result = subprocess.run(['python3', str(CLEAN), '--search-root', str(root),
                                     '--destination', str(unrelated), '--trash-root', str(root / '.Trash')],
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(old.exists())
            self.assertTrue(unrelated.exists())


if __name__ == '__main__':
    unittest.main()
