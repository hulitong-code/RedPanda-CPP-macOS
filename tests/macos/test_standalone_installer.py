#!/usr/bin/env python3
"""Exercise native installation using a tiny payload and an isolated home."""
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile

installer = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='panda-installer-test-') as tmp:
    base = Path(tmp)
    home = base / 'home'
    payload = base / 'payload/RedPandaIDE.app'
    def app(path, executable='RedPandaIDE'):
        (path / 'Contents/Resources').mkdir(parents=True)
        (path / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': executable}))
    app(payload)
    (payload / 'Contents/Resources/standalone.ini').write_text('[Environment]\nlanguage=zh_CN\n[CompilerSets]\ncount=2\ndefaultIndex=1\n[CompilerSet_0]\nName=Bundled GCC\n')
    old = home / 'Downloads/Old.app'
    app(old)
    unrelated = home / 'Applications/Other.app'
    app(unrelated, 'Other')
    config = home / 'Library/Application Support/Red Panda C++/redpandacpp.ini'
    config.parent.mkdir(parents=True)
    config.write_text('[Editor]\nfont_size=19\n[CompilerSets]\ncount=7\n[CompilerSet_0]\nName=Old GCC\n[Environment]\nlanguage=zh_CN\n')
    subprocess.run([installer, '--test-install', payload, home], check=True)
    assert not old.exists()
    assert unrelated.exists()
    assert (home / 'Applications/RedPandaIDE.app').exists()
    text = config.read_text()
    assert 'font_size=19' in text and 'Bundled GCC' in text and 'Old GCC' not in text
    assert len(list(config.parent.glob('*.backup-*'))) == 1
    records = json.loads((config.parent / 'last-install-moved-apps.json').read_text())
    assert len(records) == 1 and Path(records[0]['to']).exists()
    # A second install replaces only the recognized installed app.
    subprocess.run([installer, '--test-install', payload, home], check=True)
    assert unrelated.exists()
    # An unrelated app at the destination must survive a refused installation.
    (home / 'Applications/RedPandaIDE.app/Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleExecutable': 'Unrelated'}))
    result = subprocess.run([installer, '--test-install', payload, home], capture_output=True)
    assert result.returncode != 0
    assert plistlib.loads((home / 'Applications/RedPandaIDE.app/Contents/Info.plist').read_bytes())['CFBundleExecutable'] == 'Unrelated'
    print('PASS: native install, recoverable cleanup, preference backup/migration, reinstall, unrelated-app protection')
