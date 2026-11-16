#!/bin/bash
# Stage a local Apple Silicon build using the installed Homebrew toolchains.
set -euo pipefail
app=${1:?Usage: stage-local-tools.sh APP_BUNDLE LLDB_MI}
bridge=${2:?Specify the patched lldb-mi executable}
bin="$app/Contents/MacOS"
mkdir -p "$bin/gcc/bin" "$bin/lldb/bin"
for tool in gcc g++; do
    target="$bin/gcc/bin/$tool"
    if [[ -L "$target" ]]; then rm "$target"; fi
    printf '#!/bin/sh\nexec /opt/homebrew/opt/gcc@15/bin/%s-15 "$@"\n' "$tool" > "$target"
    chmod +x "$target"
done
# This bridge links against Homebrew LLDB and LLVM. This is not a standalone bundle.
cp "$bridge" "$bin/lldb/bin/lldb-mi"
if [[ -L "$bin/lldb/bin/lldb-server" ]]; then rm "$bin/lldb/bin/lldb-server"; fi
install -m 755 /opt/homebrew/bin/astyle "$bin/astyle"
