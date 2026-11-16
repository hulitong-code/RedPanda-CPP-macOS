#!/bin/bash
# Build the pinned MI bridge against the local Homebrew LLDB and LLVM.
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
source_dir=${1:-"$root/build/lldb-mi-src"}
revision=66d422a572e06a3a904ce9a128f23125c62805e3
if [[ ! -d "$source_dir/.git" ]]; then
    git clone https://github.com/lldb-tools/lldb-mi.git "$source_dir"
    git -C "$source_dir" checkout "$revision"
fi
[[ $(git -C "$source_dir" rev-parse HEAD) == "$revision" ]]
patch="$root/packages/macos/patches/lldb-mi-terminal-launch.patch"
if git -C "$source_dir" apply --check "$patch"; then
    git -C "$source_dir" apply "$patch"
else
    git -C "$source_dir" apply --reverse --check "$patch"
fi
cmake -S "$source_dir" -B "$source_dir/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH='/opt/homebrew/opt/llvm;/opt/homebrew/opt/lldb'
cmake --build "$source_dir/build" --parallel "${PANDA_BUILD_JOBS:-4}"
