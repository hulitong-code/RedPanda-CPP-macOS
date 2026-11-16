# Apple Silicon macOS — Download & Install

**[⬇ Download the current macOS source ZIP](https://github.com/hulitong-code/RedPanda-CPP-macOS/archive/refs/heads/master.zip)** · **[Installation guide / Agent instructions](docs/INSTALL_APPLE_SILICON.md)**

> **Public download: source code, not a ready-to-run DMG.** Build and install with
> `packages/macos/install.sh`; Homebrew and Apple Command Line Tools are required.
> The current `master` includes the gutter breakpoint fix. The standalone packaging
> scripts also include the LLDB container-display fix and acceptance tests.
>
> **Standalone DMG status:** the r4 DMG is a local private-use package containing
> locally licensed Apple SDK/developer tools. It has **not been uploaded** as a
> public release, so there is currently **no public DMG download link**.
> **Why no public DMG?** This image bundles Apple SDK/developer tools whose
> redistribution is restricted by [Apple's license, section 2.7](https://www.apple.com/legal/sla/docs/xcode.pdf).
> Providing it by email does not waive those restrictions.
>
> **Need an installation package?** Email the maintainer at
> [hulitong1023@163.com](mailto:hulitong1023@163.com) to ask about available packages
> and installation help. Any package provided must comply with its components'
> redistribution licenses; this is not an offer to distribute the private r4 image.
>
> See [download options and requirements](docs/INSTALL_APPLE_SILICON.md#download-options).

Native GCC/LLDB debugging, `<bits/stdc++.h>`, Chinese UI, One Dark and red breakpoints.
This is an unofficial macOS fork; the upstream project is described below.

---

# RedPanda C++

Red Panda C++ (Old name: Red Panda Dev-C++ 7) is an fast ,lightweight, open source, and cross platform C/C++/GNU Assembly IDE.

Simplified Chinese Website: [http://royqh.net/redpandacpp](http://royqh.net/redpandacpp)

English Website: [https://sourceforge.net/projects/redpanda-cpp](https://sourceforge.net/projects/redpanda-cpp)

[Donate to this project](https://ko-fi.com/royqh1979)

**New Features (Compared with Red Panda Dev-C++ 6):**

* Cross Platform (Windows/Linux/MacOS)
* Problem Set (run and test program against predefined input / expected output data)
* Competitive Companion support ( It's an chrome/firefox extension that can fetch problems from OJ websites)
* Edit/compile/run/debug Assembly language programs ( GNU Assember / NASM ).
* Find symbol occurrences
* Memory View for debugging
* TODO View
* Support SDCC Compiler

**UI Improvements:**

* Full high-dpi support, including fonts and icons
* Better dark theme support
* Better editor color scheme support
* Redesigned Find/Replace in Files UI
* Redesigned bookmark UI

**Editing Improvements:**

* Enhanced auto indent
* Enhanced code completion
* Better code folding support

**Debugging Improvements:**

* Use gdb/mi interface
* Enhanced watch
* gdbserver mode

**Code Intellisense Improvements:**

* Better support identifiers for complex expressions
* Support UTF-8 identifiers
* Support C++ 14 using type alias
* Support C-Style enum variable definitions
* Support MACRO with arguments
* Support C++ lambdas

And many other improvements and bug fixes. See NEWS.md for full information.

## Acknowledgement

[Lua](https://www.lua.org/) 5.4.6 ([source mirror](https://github.com/lua/lua/tree/v5.4.6)) is used as add-on runtime.
