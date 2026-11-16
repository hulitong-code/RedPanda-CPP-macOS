# Install the Apple Silicon edition

This public fork contains the native macOS changes to Red Panda C++ 3.6 alpha.
Upstream: https://github.com/royqh1979/RedPanda-CPP (GPL-3.0-or-later).
The initial upstream snapshot is `5579eaf`; the LLDB-MI bridge is pinned to
`66d422a572e06a3a904ce9a128f23125c62805e3` with the patch in `packages/macos/patches`.

## Requirements

- Apple Silicon Mac, running a macOS release supported by Homebrew and Qt 6.
  Run from a native arm64 terminal, not Rosetta.
- Xcode Command Line Tools (`xcode-select --install`). Complete Apple's installer
  if prompted before continuing.
- Native Homebrew in `/opt/homebrew` (https://brew.sh).
- Internet access and sufficient disk space for Qt, LLVM, LLDB and GCC.

This is a source-build installer. It compiles on the target Mac to avoid carrying
binaries tied to the original machine's SDK and Homebrew library versions.
It is not a standalone binary release. Do not copy the original machine's ZIP to
an unrelated Mac and assume its linked LLDB/LLVM libraries are compatible.

## Installation

```sh
mkdir -p "$HOME/Developer"
git clone --branch macos-v1.0.0 --depth 1 \
  https://github.com/hulitong-code/RedPanda-CPP-macOS.git \
  "$HOME/Developer/RedPanda-CPP-macOS"
cd "$HOME/Developer/RedPanda-CPP-macOS"
packages/macos/install.sh
```

The script installs Homebrew dependencies, builds the IDE and patched LLDB-MI,
runs the five Qt test suites, deploys native Qt plugins, validates a real
`<bits/stdc++.h>` program, verifies the ad-hoc signature, and installs to
`~/Applications/RedPandaIDE.app`. Save work and quit existing IDE instances first.
An existing destination is renamed to a dated backup; existing user settings
are never replaced. The script does not ask for or store GitHub credentials.

For a fresh user profile, it configures Simplified Chinese, One Dark, the
Contrast icon set with solid red breakpoint dots, and GCC 15 Debug by default.
Compiler and debugger paths use the application's location, not an original
machine's absolute user path. If settings already exist, use Preferences >
Compiler > Compiler Set to rediscover compilers, then select GCC Debug.
Language and theme are under Preferences > Environment > Appearance; editor
colors are under Editor > Color. Restart after changing the language.

Optional flags:

```sh
packages/macos/install.sh --help
packages/macos/install.sh --skip-deps                 # dependencies already installed
packages/macos/install.sh --build-only               # build/verify without installing
packages/macos/install.sh --app "$HOME/Applications/RedPandaIDE.app"
```

`PANDA_BUILD_JOBS=2` reduces memory pressure. The default is 4.

## Debugging authorization and acceptance test

Check `/usr/sbin/DevToolsSecurity -status`. If it is disabled, ask the machine
owner before running `sudo /usr/sbin/DevToolsSecurity -enable`: it persistently
changes developer debugging authorization. Have the owner enter the password
locally; never request it in chat. The installer does not change this setting.

Compile and test the actual installed debugger:

```sh
app="$HOME/Applications/RedPandaIDE.app"
work=$(mktemp -d /tmp/redpanda-verify.XXXXXX)
"$app/Contents/MacOS/gcc/bin/g++" -std=c++17 -g -O0 \
  tests/macos/mi_input.cpp -o "$work/mi_input"
python3 tests/macos/mi_smoke.py "$app/Contents/MacOS/lldb/bin/lldb-mi" "$work/mi_input"
printf '21\n' > "$work/input.txt"
python3 tests/macos/mi_smoke.py "$app/Contents/MacOS/lldb/bin/lldb-mi" \
  "$work/mi_input" --input-file "$work/input.txt"
```

Then open the app and `tests/macos/mi_input.cpp`, set a breakpoint at line 7,
start Debug, enter `21` in Terminal, and check `answer = 42`. Check that Step Over
and Continue work and that ordinary Run exits with code 0. A multi-file project
should also compile using the selected GCC, not Apple's `g++` alias for Clang.
Use the forward slash spelling `<bits/stdc++.h>`.

## Maintenance and limitations

Homebrew updates that change the LLVM/LLDB library ABI can require rebuilding
the bridge and reinstalling. The script pins bridge source, not the entire
Homebrew package ecosystem; it fails on build/test errors rather than claiming
an incompatible installation succeeded. Qt widget tests can be affected by
concurrent mouse/keyboard activity; inspect and rerun a failing test before
changing code or ignoring a failure.

Windows-specific Win32 GUI projects, PE resources and Windows-only toolchains
are not native macOS capabilities. This is an unofficial development fork;
upstream licenses and attribution remain intact. No credential or personal
configuration belongs in this public repository.
