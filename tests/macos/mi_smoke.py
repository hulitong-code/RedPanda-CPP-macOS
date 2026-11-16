#!/usr/bin/env python3
"""Exercise LLDB-MI against a GCC binary, with a real terminal for stdin/stdout."""
import argparse
import os
from pathlib import Path
import pty
import re
import signal
import selectors
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('debugger')
parser.add_argument('program')
parser.add_argument('--line', type=int, default=7)
parser.add_argument('--input-file')
args = parser.parse_args()
master, slave = pty.openpty()
env = os.environ.copy()
env.pop("REDPANDA_DEBUG_INPUT_FILE", None)
if args.input_file:
    env["REDPANDA_DEBUG_INPUT_FILE"] = str(Path(args.input_file).resolve())
process = subprocess.Popen([args.debugger], env=env, stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=0)
selector = selectors.DefaultSelector()
selector.register(process.stdout, selectors.EVENT_READ)
selector.register(master, selectors.EVENT_READ)
transcript = bytearray()

def command(text, expected):
    process.stdin.write((text + '\n').encode())
    process.stdin.flush()
    received = bytearray()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        for key, _ in selector.select(0.2):
            chunk = os.read(key.fd, 65536)
            if not chunk:
                raise RuntimeError('Debugger exited unexpectedly')
            if key.fd == master:
                continue
            received.extend(chunk)
            transcript.extend(chunk)
            if b'^error' in received:
                raise RuntimeError(received.decode(errors='replace'))
            if expected in received:
                return bytes(received)
    raise TimeoutError(received.decode(errors='replace'))

try:
    command('10-gdb-set mi-async on', b'10^done')
    command('11-enable-pretty-printing', b'11^done')
    command('12-gdb-set width 0', b'12^done')
    command('13-gdb-set confirm off', b'13^done')
    command('1-file-exec-and-symbols "' + str(Path(args.program).resolve()) + '"', b'1^done')
    command('2-inferior-tty-set ' + os.ttyname(slave), b'2^done')
    command('3-break-insert main', b'3^done')
    command('4-exec-run', b'reason="breakpoint-hit"')
    command('5-break-insert mi_input.cpp:' + str(args.line), b'5^done')
    if not args.input_file:
        os.write(master, b'21\n')
    command('6-exec-continue', b'reason="breakpoint-hit"')
    values = command('7-stack-list-variables --all-values', b'7^done')
    assert b'name="answer",value="42"' in values, values
    frames = command('14-stack-list-frames', b'14^done')
    assert b'func="main"' in frames, frames
    watch = command('15-var-create watch_answer * answer', b'15^done')
    assert b'value="42"' in watch, watch
    command('16-var-delete watch_answer', b'16^done')
    command('8-exec-next', b'reason="end-stepping-range"')
    command('9-exec-continue', b'reason="exited-normally"')
    print('PASS: terminal input, breakpoints, variables, watches, stack, stepping, normal exit')
finally:
    Path(args.program + '.mi.log').write_bytes(transcript)
    active_pids = [] if b'reason="exited-normally"' in transcript else re.findall(
        rb'=thread-group-started,[^\n]*pid="(\d+)"', transcript)
    for pid in active_pids:
        try:
            os.kill(int(pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    os.close(master)
    os.close(slave)
