#!/usr/bin/env python3
"""Create first-install settings without replacing existing user preferences."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, default=Path.home() / 'Library/Application Support/Red Panda C++/redpandacpp.ini')
args = parser.parse_args()
if args.output.exists():
    print('Existing settings preserved:', args.output)
    raise SystemExit(0)
gcc = '/opt/homebrew/opt/gcc@15/bin/gcc-15'
version = subprocess.check_output([gcc, '-dumpfullversion'], text=True).strip()
triple = subprocess.check_output([gcc, '-dumpmachine'], text=True).strip()
settings = '''[CompilerSets]
count=2
defaultIndex=1
defaultIndexTimestamp=0

[Environment]
language=zh_CN
theme=one_dark
icon_set=contrast
use_custom_icon_set=false
use_custom_terminal=true
terminal_path=/System/Applications/Utilities/Terminal.app/Contents/MacOS/Terminal
terminal_arguments_pattern=$term $tmpfile

[Editor]
color_scheme=One Dark

[Debugger]
use_gdb_server=false
'''
for index, mode in enumerate(('Release', 'Debug')):
    extra = '-std=c++17 -O2 -DNDEBUG' if mode == 'Release' else '-std=c++17 -g -O0'
    settings += f'''
[CompilerSet_{index}]
Name=GCC {version} Apple Silicon {mode}
CompilerType=0
Version={version}
Target=aarch64
DumpMachine={triple}
Bins=%*APP_LIBEXEC_DIR*%/gcc/bin, /usr/bin
C=@Invalid()
Cpp=@Invalid()
Libs=@Invalid()
ccompiler=%*APP_LIBEXEC_DIR*%/gcc/bin/gcc
cppcompiler=%*APP_LIBEXEC_DIR*%/gcc/bin/g++
debugger=%*APP_LIBEXEC_DIR*%/lldb/bin/lldb-mi
debug_server=
StaticLink=false
AddCharset=true
ExecCharset=UTF-8
PersistInAutoFind=true
useCustomCompileParams=true
customCompileParams={extra}
useCustomLinkParams=false
preprocessingSuffix=p
compilationProperSuffix=s
assemblingSuffix=o
executableSuffix=
cc_cmd_opt_use_pipe=on
'''
    if mode == 'Debug':
        settings += 'cc_cmd_opt_debug_info=on\ncc_cmd_opt_warning_all=on\n'
args.output.parent.mkdir(parents=True, exist_ok=True)
# Exclusive creation also protects against a concurrent first launch.
with args.output.open('x', encoding='utf-8') as output:
    output.write(settings)
print('Created Chinese / One Dark / GCC settings:', args.output)
