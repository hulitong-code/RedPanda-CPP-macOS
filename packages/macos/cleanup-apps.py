#!/usr/bin/env python3
"""Move other Red Panda application bundles to Trash, preserving user data."""
import argparse
import datetime
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys


def is_panda(path):
    try:
        with (path / 'Contents/Info.plist').open('rb') as stream:
            info = plistlib.load(stream)
        return (info.get('CFBundleExecutable', '').casefold() == 'redpandaide'
                or info.get('CFBundleIdentifier') == 'net.redpanda-cpp.RedPandaIDE')
    except (OSError, ValueError, plistlib.InvalidFileException):
        return False


def discover(roots):
    found = set()
    for root in roots:
        if not root.exists():
            continue
        for folder, dirs, _ in os.walk(root, followlinks=False):
            current = Path(folder)
            # Do not inspect Trash, hidden caches or other applications' internals.
            dirs[:] = [name for name in dirs if not name.startswith('.')
                       and not (current / name).is_symlink()
                       and not (current == Path.home() and name == 'Library')]
            for name in list(dirs):
                child = current / name
                if name.lower().endswith('.app'):
                    dirs.remove(name)
                    if is_panda(child):
                        found.add(child.absolute())
    return sorted(found)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--destination', type=Path)
    parser.add_argument('--protect', type=Path, action='append', default=[])
    parser.add_argument('--search-root', type=Path, action='append')
    parser.add_argument('--trash-root', type=Path, default=Path.home() / '.Trash')
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--check', action='store_true', help='Fail if another application remains; do not move anything')
    args = parser.parse_args()
    protected = {path.resolve() for path in args.protect}
    roots = args.search_root or [Path('/Applications'), Path.home()]
    candidates = {path.resolve(): path for path in discover(roots)}
    if args.destination:
        destination = args.destination.resolve()
        if destination in protected:
            parser.error('The install destination cannot be the protected staging application.')
        if args.destination.exists():
            if args.destination.is_symlink() or not is_panda(args.destination):
                parser.error('Refusing to replace a destination that is not a Red Panda application.')
            candidates.setdefault(destination, args.destination.absolute())
    apps = sorted(path for resolved, path in candidates.items() if resolved not in protected)
    if args.check:
        for app in apps:
            print('Unexpected remaining application:', app)
        return 1 if apps else 0
    moved = []
    if apps:
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        trash = args.trash_root / f'RedPanda-previous-versions-{stamp}-{os.getpid()}'
        trash.mkdir(parents=True, exist_ok=False)
        registry = Path('/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister')
        for index, app in enumerate(apps, 1):
            destination = trash / f'{index}-{app.name}'
            try:
                shutil.move(str(app), str(destination))
            except OSError as exc:
                print(f'Cannot remove old application {app}: {exc}. Resolve permissions and rerun; installation stopped.', file=sys.stderr)
                return 1
            moved.append({'from': str(app), 'canonical_from': str(app.resolve()), 'to': str(destination)})
            # Write after every move so an interrupted operation remains recoverable.
            (trash / 'moved-applications.json').write_text(json.dumps(moved, indent=2))
            if args.manifest:
                args.manifest.write_text(json.dumps(moved, indent=2))
            if registry.exists():
                subprocess.run([str(registry), '-u', str(app)], capture_output=True)
            print('Moved previous version to Trash:', app)
    if args.manifest:
        args.manifest.write_text(json.dumps(moved, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
