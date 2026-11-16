#!/usr/bin/env python3
"""Sign the payload, create a native installer and package a local-only DMG."""
from pathlib import Path
import hashlib
import os
import plistlib
import shutil
import subprocess as sp
import sys
import tempfile

app = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
root = Path(__file__).resolve().parents[3]
work = root / 'build/dmg/image'
if work.exists(): shutil.rmtree(work)
work.mkdir(parents=True)
output.mkdir(parents=True, exist_ok=True)

def run(*args): sp.run([str(x) for x in args], check=True)
contents = app / 'Contents'
# A freshly linked executable still points at the build Mac until Qt deployment.
main_dependencies = sp.check_output(['otool', '-L', str(contents / 'MacOS/RedPandaIDE')], text=True)
if '/opt/homebrew/' in main_dependencies:
    raise RuntimeError('Main executable still depends on Homebrew; deploy Qt before packaging')
plugin = contents / 'Resources/Toolchain/SharedLibs/liblldbPluginScriptInterpreterPython.dylib'
if not plugin.is_file():
    raise RuntimeError('Missing LLDB Python plugin discovery entry; container displays would be incorrect')
# Compiler discovery runs with only the compiler directory in PATH inside the IDE.
run(sys.executable, root / 'tests/macos/compiler_discovery_smoke.py',
    contents / 'MacOS/gcc/bin/gcc')
# Exercise the actual completion model against this payload's standard library.
widget_test = root / 'build/macos/RedPandaIDE/test-widgets'
if not widget_test.is_file():
    raise RuntimeError('Build test-widgets before assembling the standalone DMG')
test_env = dict(os.environ, QT_QPA_PLATFORM='offscreen',
                REDPANDA_TEST_GCC=str(contents / 'MacOS/gcc/bin/gcc'))
sp.run([str(widget_test), 'test_code_completion_bundled_gcc'], env=test_env, check=True)
# Exercise synthetic children as well as scalar variables before shipping a DMG.
with tempfile.TemporaryDirectory(prefix='redpanda-dmg-containers-') as directory:
    program = Path(directory) / 'containers_debug'
    run(contents / 'MacOS/gcc/bin/g++', '-std=c++17', '-g', '-O0',
        root / 'tests/macos/containers_debug.cpp', '-o', program)
    run(sys.executable, root / 'tests/macos/mi_container_smoke.py',
        contents / 'MacOS/lldb/bin/lldb-mi', program)

for p in list((contents / 'PlugIns').rglob('*.dylib')) + list((contents / 'Frameworks').glob('*.dylib')) + list((contents / 'Frameworks').glob('*.framework')) + [p for p in (contents / 'MacOS').iterdir() if p.is_file() and not p.is_symlink()]:
    run('codesign', '--force', '--sign', '-', p)
info = contents / 'Info.plist'
values = plistlib.loads(info.read_bytes())
values['LSMinimumSystemVersion'] = '26.0'
info.write_bytes(plistlib.dumps(values))
run('codesign', '--force', '--sign', '-', app)
run('codesign', '--verify', '--deep', '--strict', app)
installer = work / 'Install Red Panda C++.app'
resources = installer / 'Contents/Resources'
(resources.parent / 'MacOS').mkdir(parents=True)
resources.mkdir()
run('/usr/bin/clang', '-fobjc-arc', '-framework', 'Cocoa', '-mmacosx-version-min=26.0', root / 'packages/macos/standalone/Installer.m', '-o', installer / 'Contents/MacOS/Installer')
plist = {'CFBundleExecutable':'Installer', 'CFBundleIdentifier':'net.redpanda-cpp.PrivateInstaller', 'CFBundleName':'Red Panda C++ Installer', 'CFBundleDisplayName':'安装 Red Panda C++', 'CFBundlePackageType':'APPL', 'CFBundleVersion':'1.0.3', 'CFBundleShortVersionString':'1.0.3', 'LSMinimumSystemVersion':'26.0', 'NSHighResolutionCapable':True}
icons = list((contents / 'Resources').glob('*.icns'))
if icons:
    shutil.copy2(icons[0], resources / 'Installer.icns')
    plist['CFBundleIconFile'] = 'Installer.icns'
(installer / 'Contents/Info.plist').write_bytes(plistlib.dumps(plist))
run('ditto', app, resources / 'RedPandaIDE.app')
run('codesign', '--force', '--sign', '-', installer)
run('codesign', '--verify', '--deep', '--strict', installer)
readme = '''Red Panda C++ — Private-use Apple Silicon package

Requirements: Apple Silicon (M1 or later), macOS 26 or later.
No Homebrew or Xcode Command Line Tools installation is required for the
bundled C/C++ compile/run/debug workflow. Optional Git integration requires Git.

1. Open “Install Red Panda C++.app” and click 安装 / 更新.
2. If blocked, use System Settings > Privacy & Security > Open Anyway.
3. Save your work and quit an old Red Panda C++ before installation.
4. After installation click 打开 Red Panda C++.
5. If debugging authorization is disabled, open Enable Debugging.command.
   It runs Apple's DevToolsSecurity with sudo and requires the owner's password.
   This persistently enables developer debugging authorization. It is separate
   from Gatekeeper approval; neither the installer nor app disables Gatekeeper.

Installed location: ~/Applications/RedPandaIDE.app
Defaults: Chinese UI, One Dark, red breakpoints, GCC 15 Debug.
Existing preferences are backed up and preserved; compiler profiles are replaced
with the bundled profiles. Older recognized applications in the current home
and /Applications move to Trash. Hidden/Library folders, other users, symlinked
and inaccessible directories are not scanned. Cleanup errors stop installation.

Includes GCC 15.2 with bits/stdc++.h and libstdc++, LLDB-MI/LLDB/LLVM/Python,
Qt, AStyle, make, the locally licensed macOS SDK and Apple developer tools.
Generated C++ programs use the installed GCC runtime; rebuild after moving the IDE.

PRIVATE USE ONLY: contains locally licensed Apple SDK/developer tools.
Use only on Apple computers owned or controlled by the licensee under Apple's
applicable terms: https://www.apple.com/legal/sla/docs/xcode.pdf
Do not upload this payload to a public GitHub release or redistribute it as a
public installer. It is ad-hoc signed, not Developer ID signed or notarized.
The bundled Apple debugserver retains its original Apple signature.

Source: https://github.com/hulitong-code/RedPanda-CPP-macOS
Packaging source changes remain in the local project until explicitly published.
'''
(work / 'READ ME.txt').write_text(readme)
(output / 'READ ME.txt').write_text(readme)
command = work / 'Enable Debugging.command'
command.write_text('''#!/bin/sh
set -eu
printf '此操作会持久启用 macOS 开发者调试授权。需要本机管理员密码。\\n'
if /usr/sbin/DevToolsSecurity -status | /usr/bin/grep -q 'enabled'; then
    printf '开发者调试授权已启用，无需修改。\\n'
else
    sudo /usr/sbin/DevToolsSecurity -enable
fi
printf '完成。按回车关闭。\\n'
read answer
''')
command.chmod(0o755)
examples = work / 'Examples'
examples.mkdir()
for name in ('mi_input.cpp', 'bits_debug.cpp'):
    shutil.copy2(root / 'tests/macos' / name, examples / name)
dmg = output / 'RedPanda-CPP-AppleSilicon-Private-20261116-r4.dmg'
if dmg.exists(): raise RuntimeError(f'Refusing to overwrite {dmg}')
run('hdiutil', 'create', '-volname', 'Red Panda C++ Installer', '-srcfolder', work, '-format', 'UDZO', '-ov', dmg)
digest = hashlib.file_digest(dmg.open('rb'), 'sha256').hexdigest()
(dmg.with_suffix('.dmg.sha256')).write_text(f'{digest}  {dmg.name}\n')
print(f'Created {dmg} ({dmg.stat().st_size:,} bytes)')
