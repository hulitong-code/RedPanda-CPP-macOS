# Apple Silicon macOS — Download & Install

**[⬇ Download the current macOS source ZIP](https://github.com/hulitong-code/RedPanda-CPP-macOS/archive/refs/heads/master.zip)** · **[Installation guide / Agent instructions](docs/INSTALL_APPLE_SILICON.md)**

> **Public download: source code, not a ready-to-run DMG.** Build and install with
> `packages/macos/install.sh`; Homebrew and Apple Command Line Tools are required.
> The current `master` includes the gutter breakpoint fix. The standalone packaging
> scripts also include the LLDB container-display fix and acceptance tests.
>
> **Standalone DMG status:** the r3 DMG is a local private-use package containing
> locally licensed Apple SDK/developer tools. It has **not been uploaded** as a
> public release, so there is currently **no public DMG download link**.
> **Why no public DMG?** This image bundles Apple SDK/developer tools whose
> redistribution is restricted by [Apple's license, section 2.7](https://www.apple.com/legal/sla/docs/xcode.pdf).
> Providing it by email does not waive those restrictions.
>
> **Need an installation package?** Email the maintainer at
> [hulitong1023@163.com](mailto:hulitong1023@163.com) to ask about available packages
> and installation help. Any package provided must comply with its components'
> redistribution licenses; this is not an offer to distribute the private r3 image.
>
> See [download options and requirements](docs/INSTALL_APPLE_SILICON.md#download-options).

Native GCC/LLDB debugging, `<bits/stdc++.h>`, Chinese UI, One Dark and red breakpoints.
This is an unofficial macOS fork; the upstream project is described below.

---

# RedPanda C++ 
小熊猫C++ (曾经用过的名称: 小熊猫Dev-C++ 7) 是一款快速、轻量、开源并且跨平台的C/C++/GNU的编译工具。(Assembly IDE).

简体中文网站: [http://royqh.net/redpandacpp](http://royqh.net/redpandacpp)

英文网站: [https://sourceforge.net/projects/redpanda-cpp](https://sourceforge.net/projects/redpanda-cpp)

[为这个项目捐款](https://ko-fi.com/royqh1979)

新特性 (相对于上一版本：Red Panda Dev-C++ 6):
* 跨平台 (Windows/Linux/MacOS)
* 编辑、管理和使用试题集来测试程序(根据预定义的输入运行程序，比较实际输出和预期结果）。
* 支持Competitive Companion(chrome/firefox浏览器的插件），从OJ网站上下载试题集。
* 编辑、编译、运行、调试汇编语言程序（GNU汇编器 / NASM）.
* 查找符号引用。
* 在调试时查看内存查看功能。
* TODO标签管理
* 支持SDCC编译器

交互界面改进：
* 完整的高dpi支持，包括对字体和图标的支持
* 更好的支持深色主题
* 更好的支持编辑器配色方案
* 重新设计的“在文件中查找/替换”UI
* 重新设计的书签交互界面

编辑器改进：
* 增强的自动缩进功能
* 增强的代码自动完成功能
* 更好的代码折叠支持功能

调试改进：
* 使用gdb/mi接口
* 增强型监测
* gdbserver模式

代码智能感知改进：
* 更好地支持复杂表达式的标识符
* 支持UTF-8标识符
* 使用类型别名支持C++14
* 支持C样式枚举变量定义
* 用参数支持MACRO
* 支持C++lambdas表达式

以及许多其他改进和错误修复。有关详细信息，请参阅NEWS.md。

## 致谢

[Lua](https://www.lua.org/) 5.4.6 ([源代码镜像](https://github.com/lua/lua/tree/v5.4.6)) 用作附加组件运行环境。
