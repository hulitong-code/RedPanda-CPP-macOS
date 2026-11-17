# Breakpoint target regression

Run these checks in the installed IDE, not only through the LLDB-MI bridge.
Use the bundled GCC Debug profile and a source line containing executable code.

1. Open a project and place a breakpoint in one of its source files.
2. Open an unrelated standalone C++ file and place a breakpoint after a local
   variable has been initialized. Keep the project open.
3. Restart the IDE with the standalone tab selected. Before switching tabs,
   set the standalone breakpoint again if it was not persisted, and verify the
   breakpoint table lists it. Start debugging:
   it must stop on the standalone breakpoint and show the local variable.
   The debug console must not attempt to insert the unrelated project breakpoint.
4. Continue to normal exit, then debug a project source. It must stop at the
   project breakpoint, with project watches selected.
5. Switch back to the standalone file and repeat debugging. It must still stop.
6. With a standalone file selected, open a project without switching to a project
   source. Verify the breakpoint table still matches the visible standalone file.

Also run the gutter-click Qt test, all CTest suites, and the bundled MI container
smoke test. A passing MI-only test does not cover selection of IDE breakpoint sets.
