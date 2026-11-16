#!/usr/bin/env python3
"""Build a relocatable, private-use toolchain from this Mac's licensed tools."""
import os
from pathlib import Path
import shutil
import subprocess as sp
import sys

app = Path(sys.argv[1]).resolve()
mac = app / 'Contents/MacOS'
origins = {}
clt = Path('/Library/Developer/CommandLineTools')

def copy(src, dst):
    src, dst = Path(src), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
        for p in ([] if dst == mac / 'SDK' else dst.rglob('*')):
            if p.is_file() and not p.is_symlink():
                origins[p] = (src / p.relative_to(dst)).resolve()
    else:
        shutil.copy2(src, dst)
        origins[dst] = src.resolve()

for name in ('gcc', 'SDK', 'apple', 'lldb', 'make', 'SharedLibs', 'python', 'python-lldb'):
    target = mac / name
    if target.is_symlink(): target.unlink()
    elif target.exists(): shutil.rmtree(target)
resources = app / 'Contents/Resources/Toolchain'
if resources.exists(): shutil.rmtree(resources)
if (mac / 'astyle').exists(): (mac / 'astyle').unlink()
copy('/opt/homebrew/opt/gcc@15', mac / 'gcc')
copy(clt / 'SDKs/MacOSX.sdk', mac / 'SDK')
for name in ('clang', 'ld', 'dsymutil', 'ar', 'ranlib', 'make', 'nm', 'strip'):
    copy(clt / 'usr/bin' / name, mac / 'apple/bin' / name)
copy(clt / 'usr/lib/clang', mac / 'apple/lib/clang')
copy(clt / 'Library/PrivateFrameworks/LLDB.framework/Resources/debugserver', mac / 'lldb/bin/debugserver')
copy(sys.argv[2], mac / 'lldb/bin/lldb-mi.real')
copy('/opt/homebrew/bin/astyle', mac / 'astyle')
copy('/opt/homebrew/opt/python@3.15/Frameworks/Python.framework/Versions/3.15', mac / 'python')
(mac / 'python/lib/python3.15/site-packages').unlink()
(mac / 'python/lib/python3.15/site-packages').mkdir()
copy('/opt/homebrew/opt/lldb/lib/python3.15/site-packages', mac / 'python-lldb')
copy('/opt/homebrew/opt/lldb/lib/liblldbPluginScriptInterpreterPython.23.1.dylib', mac / 'SharedLibs/liblldbPluginScriptInterpreterPython.23.1.dylib')
for name in ('darwin-debug', 'lldb-argdumper'):
    copy('/opt/homebrew/opt/lldb/bin/' + name, mac / 'lldb/bin' / name)
native = mac / 'python-lldb/lldb/native/_lldb.abi3.so'
native.unlink()
native.symlink_to('../../../SharedLibs/liblldbPluginScriptInterpreterPython.23.1.dylib')
argdumper = mac / 'python-lldb/lldb/lldb-argdumper'
argdumper.unlink()
argdumper.symlink_to('../../lldb/bin/lldb-argdumper')

def script(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink(): path.unlink()
    path.write_text('#!/bin/sh\nset -eu\n' + content)
    path.chmod(0o755)

script(mac / 'apple/bin/as', 'dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\nexec "$dir/clang" -x assembler -c "$@"\n')
for name in ('gcc', 'g++'):
    script(mac / 'gcc/bin' / name, '''dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$dir/../.." && pwd)
export SDKROOT="$root/SDK"
export PATH="$root/apple/bin:/usr/bin:/bin:/usr/sbin:/sbin"
exec "$dir/NAME-15" -B"$root/apple/bin/" -isysroot "$root/SDK" -Wl,-rpath,"$root/gcc/lib/gcc/15" "$@"
'''.replace('NAME', name))
script(mac / 'lldb/bin/lldb-mi', '''dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root=$(CDPATH= cd -- "$dir/../.." && pwd)
export LLDB_DEBUGSERVER_PATH="$dir/debugserver"
export LLDB_ARGDUMPER_PATH="$dir/lldb-argdumper"
export LLDB_PYTHON_LIBRARY="$root/python/Python"
export PYTHONHOME="$root/python"
export PYTHONPATH="$root/python-lldb"
export PYTHONDONTWRITEBYTECODE=1
exec "$dir/lldb-mi.real" "$@"
''')
script(mac / 'make/bin/make', 'dir=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)\nexport PATH="$dir/gcc/bin:$dir/apple/bin:/usr/bin:/bin:/usr/sbin:/sbin"\nexec "$dir/apple/bin/make" "$@"\n')

magic = {b'\xcf\xfa\xed\xfe', b'\xce\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf'}
def macho(path):
    if path.suffix in ('.o', '.a') or path.is_symlink() or not path.is_file(): return False
    if any(p.is_symlink() for p in path.parents): return False
    with path.open('rb') as f: return f.read(4) in magic

def out(*args): return sp.check_output(args, text=True)

def rpaths(p):
    lines = out('/usr/bin/otool', '-l', str(p)).splitlines()
    return [lines[i+2].strip().split(' (offset')[0][5:] for i,l in enumerate(lines) if l.strip() == 'cmd LC_RPATH']

def expand(s, origin):
    return Path(s.replace('@loader_path', str(origin.parent)).replace('@executable_path', str(origin.parent)))

mapping = {src: dst for dst,src in origins.items() if macho(dst)}
queue = list(mapping.values())
shared = mac / 'SharedLibs'
shared.mkdir(exist_ok=True)
seen = set()
while queue:
    p = queue.pop(0)
    if p in seen: continue
    seen.add(p)
    origin = origins.get(p, p)
    p.unlink()
    shutil.copy2(origin, p)
    ids = set(line.strip() for line in out('/usr/bin/otool', '-D', str(p)).splitlines()[1:])
    deps = [line.strip().split(' (compatibility')[0] for line in out('/usr/bin/otool', '-L', str(p)).splitlines() if ' (compatibility' in line]
    deps = list(dict.fromkeys(deps))
    for dep in deps:
        if dep in ids: continue
        if dep.startswith(('/usr/lib/', '/System/Library/')): continue
        if dep.startswith('@rpath/'):
            candidates = [expand(r, origin) / dep[7:] for r in rpaths(origin)]
            candidates += [clt / 'usr/lib' / dep[7:]]
            source = next((q.resolve() for q in candidates if q.exists()), None)
        else:
            source = expand(dep, origin).resolve()
        if source == origin: continue
        if source is None or not source.exists(): raise RuntimeError(f'Unresolved {p}: {dep}')
        target = mapping.get(source)
        if target is None:
            target = shared / source.name
            if target.exists() and origins.get(target) != source:
                raise RuntimeError(f'Library collision: {source}')
            copy(source, target)
            mapping[source] = target
            queue.append(target)
        if p.parent == mac / 'apple/bin' and dep.startswith('@rpath/'):
            link = mac / 'apple/lib' / dep[7:]
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.exists(): link.symlink_to(os.path.relpath(target, link.parent))
            continue
        new = '@loader_path/' + os.path.relpath(target, p.parent)
        if dep != new:
            p.chmod(p.stat().st_mode | 0o200)
            sp.run(['install_name_tool', '-change', dep, new, str(p)], check=True, capture_output=True)
    # Runtime libraries linked into user executables use a relocatable install name.
    if p.suffix == '.dylib':
        sp.run(['install_name_tool', '-id', '@rpath/' + p.name, str(p)], check=True, capture_output=True)
    for r in set(rpaths(p)):
        if r.startswith(('/opt/homebrew', '/Library/Developer')):
            sp.run(['install_name_tool', '-delete_rpath', r, str(p)], check=True, capture_output=True)
    # Keep the Apple-signed debugserver and its restricted entitlements unchanged.
    if p.name != 'debugserver':
        sp.run(['codesign', '--force', '--sign', '-', str(p)], check=True, capture_output=True)
print(f'Staged and relocated {len(seen)} Mach-O toolchain files', flush=True)

# Toolchain data belongs in Resources; public tool paths remain compatible.
resources = app / 'Contents/Resources/Toolchain'
resources.mkdir(exist_ok=True)
for name in ('gcc', 'apple', 'SDK', 'lldb', 'make', 'SharedLibs', 'python', 'python-lldb'):
    shutil.move(mac / name, resources / name)
    (mac / name).symlink_to('../Resources/Toolchain/' + name)

# Generate portable compiler profiles while preserving the standard first-run defaults.
root = Path(__file__).resolve().parents[3]
settings = app / 'Contents/Resources/standalone.ini'
if settings.exists(): settings.unlink()
sp.run([sys.executable, root / 'packages/macos/seed-settings.py', '--output', settings], check=True)
text = settings.read_text()
environment = text.index('[Environment]')
profiles = text.index('[CompilerSet_0]')
compiler = text[:environment] + text[profiles:]
compiler = compiler.replace('debug_server=', 'make=%*APP_LIBEXEC_DIR*%/make/bin/make\ndebug_server=')
compiler = compiler.replace('gcc/bin, /usr/bin', 'gcc/bin, %*APP_LIBEXEC_DIR*%/apple/bin, /usr/bin')
settings.write_text(text[environment:profiles] + compiler)
