# Private-use self-contained macOS package

This packaging workflow copies the owner's locally installed Apple SDK and developer tools, plus GNU GCC 15, the patched LLDB-MI bridge, LLDB/LLVM and their dynamic dependencies. It is intended for the owner's controlled Apple computers under the applicable Apple software terms. Do not publish this private-use payload as a public GitHub release. A public distributable requires a separate toolchain/SDK licensing and source-compliance review.

The current artifact targets Apple Silicon and macOS 26 or later. It uses ad-hoc signatures and is not notarized. Gatekeeper approval and developer debugging authorization are separate actions performed by the owner. The installer never disables Gatekeeper or removes quarantine attributes.

`stage.py APP LLDB_MI` stages and relocates the toolchain in a generated application bundle. It replaces only generated toolchain directories inside APP. Apple debugserver retains its original signature and entitlements. The bridge wrapper selects that debugserver explicitly. GCC wrappers select the bundled SDK, assembler and linker, and embed the bundled runtime library search path in generated programs. Those programs depend on this installation's GCC runtime; moving the IDE requires rebuilding them.

`Installer.m` builds with the system Clang and Cocoa framework. It copies the payload to `~/Applications/RedPandaIDE.app`, moves recognized older applications in the current home and `/Applications` to Trash, backs up settings and replaces compiler profiles with the packaged profiles. Existing editor preferences remain intact. Hidden folders, Library, other users, symlinked directories and inaccessible directories are outside its scan. Cleanup failure stops installation and attempts to restore applications already moved. Installation is refused while Red Panda C++ is running.

The command-line `--test-install PAYLOAD TEST_HOME` exercises the same copy, settings and cleanup logic in an isolated directory, using TEST_HOME/Trash instead of the real Trash. It does not launch the application or change system authorization.

Optional Git integration still requires a Git installation. This package supplies the C/C++ editing, compiling, running, project make, formatting and debugging toolchain; it does not add NASM, SDCC or third-party libraries.

Build procedure (from the repository root, with build dependencies installed):

```sh
cmake --build build/macos --parallel 4
cmake --install build/macos --prefix build/private-stage
packages/macos/deploy-qt.sh build/private-stage/RedPandaIDE.app
python3 packages/macos/standalone/stage.py build/private-stage/RedPandaIDE.app /path/to/patched/lldb-mi
python3 packages/macos/standalone/assemble.py build/private-stage/RedPandaIDE.app downloads
```

Use a clean generated staging directory so obsolete Qt plugins are not retained.
`assemble.py` refuses to overwrite an existing DMG. Verify the image with
`hdiutil verify`, mount read-only, then verify the installer and nested payload
with `codesign --verify --deep --strict`. Keep a SHA-256 checksum alongside it.

The bundled Python runtime is selected through `LLDB_PYTHON_LIBRARY`,
`PYTHONHOME` and `PYTHONPATH`; its external site-packages link is replaced by an
empty directory. `PYTHONDONTWRITEBYTECODE` prevents debugger use from changing
sealed application resources. Test that compilation and debugging work under a
sandbox denying reads from `/opt/homebrew`, `/Library/Developer` and
`/Applications/Xcode.app`, including after moving the app to a path with spaces.
This is an isolation test on the build Mac, not a substitute for testing on a
second clean Mac or verifying compatibility with older macOS versions.
