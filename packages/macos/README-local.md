For installation on another Mac, use [the installer guide](../../docs/INSTALL_APPLE_SILICON.md).

# Apple Silicon local build

This development build targets the current Apple Silicon Mac. It includes Qt,
AStyle, consolepauser, Git integration, Lua support, native project templates,
and a patched LLDB-MI bridge. It uses the installed Homebrew GCC 15, LLDB and LLVM;
it is **not a standalone redistributable toolchain bundle**.

## Build

Install Xcode Command Line Tools and Homebrew dependencies (`cmake`, `ninja`,
`qt`, `astyle`, `gcc@15`, `llvm`, `lldb`). Build from the repository root:

```sh
cmake -S . -B build/macos -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_PREFIX_PATH=/opt/homebrew -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DLUA_ADDON=ON -DVCS=ON
cmake --build build/macos --parallel 6
packages/macos/build-lldb-mi.sh
cmake --install build/macos --prefix "$PWD/build/macos-pkg"
macdeployqt build/macos-pkg/RedPandaIDE.app -libpath=/opt/homebrew/lib \
  -executable=build/macos-pkg/RedPandaIDE.app/Contents/MacOS/redpanda-git-askpass
packages/macos/stage-local-tools.sh build/macos-pkg/RedPandaIDE.app \
  build/lldb-mi-src/build/src/lldb-mi
codesign --force --deep --sign - build/macos-pkg/RedPandaIDE.app
codesign --verify --deep --strict build/macos-pkg/RedPandaIDE.app
```

The bridge patch retains LLDB's target listener and launch settings while
connecting stdin/stdout/stderr to the terminal. On macOS the IDE launches LLDB
locally; `lldb-server gdbserver` is unsupported on Apple platforms.

## Validation

```sh
QT_QPA_PLATFORM=offscreen ctest --test-dir build/macos --output-on-failure
/opt/homebrew/opt/gcc/bin/g++-15 -std=c++17 -g -O0 \
  tests/macos/mi_input.cpp -o /tmp/redpanda-mi-input
python3 tests/macos/mi_smoke.py build/lldb-mi-src/build/src/lldb-mi \
  /tmp/redpanda-mi-input
```

Use the GCC Debug compiler profile for `<bits/stdc++.h>`. The spelling uses a
forward slash. Apple Clang's default libc++ does not provide this GNU header.
Local debugging requires macOS developer debugging authorization. Enable it
only with the machine owner's approval (`sudo DevToolsSecurity -enable`).

## Verified behavior and platform boundaries

- All five Qt test suites pass on this machine. In the final run, the widget
  Ctrl-hover test failed once during UI interaction and passed on rerun.
- The bundled MI bridge passes breakpoint, terminal input, file input, locals,
  watch expression, call stack, single-step and normal-exit checks.
- The owner verified GUI debugging with `std::cin`: entering `21` stopped at
  line 7 and displayed `answer = 42`; ordinary Run printed `answer: 42` and exit 0.
- UI testing opened `tests/macos/bits_debug.cpp` in the Documents workspace,
  compiled it through GCC, stopped at `main`, and stepped through vector/string
  initialization and sorting, displayed `values = size=3`, `label = "panda"`,
  and `total = 6`, then continued to completion. A prior command-line-only launch hang in that
  directory was not reproduced in this IDE workflow.
- A two-source-file project compiled and linked through the IDE with the
  selected GCC toolchain; its executable printed `42` and exited successfully.
- Darwin Release profiles disable fully static linking, which fails because
  the platform does not provide `crt0.o`.
- Qt deployment and the extracted ZIP pass ad-hoc signature verification.

The optional `REDPANDA_DEBUG_INPUT_FILE` environment variable is set only on the
LLDB-MI process by the IDE when input redirection is enabled. The bundled bridge
opens that file for stdin and keeps stdout/stderr attached to the terminal.

Windows-only Win32 GUI projects, Windows resource compilation and PE output are
not native macOS features. This is a custom development build based on upstream
3.6 alpha, not an official stable release or a claim of complete Windows parity.
