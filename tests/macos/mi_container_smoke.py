#!/usr/bin/env python3
"""Verify bundled LLDB's synthetic containers through the IDE's MI protocol."""
import argparse
import os
from pathlib import Path
import re
import selectors
import signal
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('debugger')
parser.add_argument('program')
args = parser.parse_args()
source = Path(__file__).with_name('containers_debug.cpp')
markers = {marker: next(i for i, line in enumerate(source.read_text().splitlines(), 1)
                        if '// ' + marker in line)
           for marker in ('CHECK_INITIAL', 'CHECK_GROWN', 'CHECK_EMPTY')}
process = subprocess.Popen([args.debugger], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)
transcript = bytearray()
sequence = 0

def command(cmd, stopped=False):
    global sequence
    sequence += 1
    token = str(sequence)
    process.stdin.write((token + cmd + '\n').encode())
    process.stdin.flush()
    expected = b'*stopped' if stopped else (token + '^done').encode()
    received = bytearray()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        for key, _ in selector.select(0.2):
            chunk = os.read(key.fd, 65536)
            if not chunk:
                raise RuntimeError('Debugger exited: ' + received.decode(errors='replace'))
            received.extend(chunk)
            transcript.extend(chunk)
            if b'^error' in received:
                raise RuntimeError(received.decode(errors='replace'))
            if expected in received and b'\n' in received[received.index(expected):]:
                return received.decode(errors='replace')
    raise TimeoutError(received.decode(errors='replace'))

def children(name, count, values=()):
    result = command('-var-list-children --all-values ' + name)
    assert re.search(r'\^done,numchild="' + str(count) + r'"', result), result
    for index, value in enumerate(values):
        pattern = r'exp="\[' + str(index) + r'\]"[^}]*value="' + re.escape(value) + r'"'
        assert re.search(pattern, result), result
    return result

try:
    command('-gdb-set mi-async on')
    command('-enable-pretty-printing')
    command('-file-exec-and-symbols "' + str(Path(args.program).resolve()) + '"')
    for line in markers.values():
        command(f'-break-insert containers_debug.cpp:{line}')
    result = command('-exec-run', stopped=True)
    assert 'reason="breakpoint-hit"' in result, result
    result = command('-stack-list-variables --all-values')
    for name, size in [('numbers', 3), ('empty', 0), ('words', 2), ('flags', 3),
                       ('matrix', 2), ('linked', 2), ('mapping', 2), ('unique', 3)]:
        assert f'name="{name}",value="size={size}"' in result, result
    assert 'name="answer",value="42"' in result, result
    for name, size in [('numbers', 3), ('empty', 0), ('words', 2), ('flags', 3), ('matrix', 2)]:
        result = command(f'-var-create watch_{name} * {name}')
        assert f'numchild="{size}"' in result, result
    children('watch_numbers', 3, ['10', '20', '12'])
    children('watch_empty', 0)
    children('watch_words', 2, [r'\"red\"', r'\"panda\"'])
    children('watch_flags', 3, ['true', 'false', 'true'])
    children('watch_matrix', 2, ['size=2', 'size=2'])
    children('watch_matrix.[0]', 2, ['1', '2'])
    children('watch_matrix.[1]', 2, ['3', '4'])
    command('-exec-continue', stopped=True)
    command('-var-update --all-values watch_numbers')
    result = command('-stack-list-variables --all-values')
    assert 'name="numbers",value="size=4"' in result, result
    children('watch_numbers', 4, ['10', '20', '12', '7'])
    command('-exec-continue', stopped=True)
    command('-var-update --all-values watch_numbers')
    result = command('-stack-list-variables --all-values')
    assert 'name="numbers",value="size=0"' in result, result
    children('watch_numbers', 0)
    result = command('-exec-continue', stopped=True)
    assert 'reason="exited-normally"' in result, result
    print('PASS: int/string/bool/nested/empty vectors, child values, watch growth/clear, list/map/set summaries')
finally:
    Path(args.program + '.containers.mi.log').write_bytes(transcript)
    if b'reason="exited-normally"' not in transcript:
        for pid in re.findall(rb'=thread-group-started,[^\n]*pid="(\d+)"', transcript):
            try:
                os.kill(int(pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
    process.kill()
    process.wait()
    selector.close()
