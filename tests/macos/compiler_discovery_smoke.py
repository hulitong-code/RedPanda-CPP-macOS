#!/usr/bin/env python3
"""Check the compiler probes used by the IDE, including its restricted PATH."""
from pathlib import Path
import subprocess
import sys

compiler = Path(sys.argv[1]).absolute()
env = {'PATH': str(compiler.parent), 'LC_ALL': 'C', 'LANGUAGE': ''}

def probe(*args):
    result = subprocess.run([str(compiler), *args], cwd=compiler.parent,
                            env=env, capture_output=True, text=True, timeout=30)
    if result.returncode or 'command not found' in result.stderr:
        raise RuntimeError(result.stderr)
    return result.stdout + result.stderr

for language, header in [('c', 'stdio.h'), ('c++', 'vector')]:
    output = probe('-x' + language, '-E', '-v', '/dev/null')
    paths = output.split('#include <...> search starts here:', 1)[1].split('End of search list.', 1)[0]
    directories = [Path(line.strip()) for line in paths.splitlines() if line.strip()]
    assert any((path / header).is_file() for path in directories), (header, paths)
    if language == 'c++':
        assert any((path / 'bits/stdc++.h').is_file() for path in directories), paths
    defines = probe('-x' + language, '-std=c++17' if language == 'c++' else '-std=c17',
                    '-dM', '-E', '/dev/null')
    assert '#define __GNUC__ 15' in defines
    if language == 'c++':
        assert '#define __cplusplus 201703L' in defines
print('PASS: C/C++ headers and predefined macros discovered with compiler-only PATH')
