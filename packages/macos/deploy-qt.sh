#!/bin/bash
# Deploy only the native widgets plugins this IDE needs, avoiding unrelated Qt modules.
set -euo pipefail
app=${1:?Usage: deploy-qt.sh APP_BUNDLE}
qt_prefix=$(/opt/homebrew/bin/brew --prefix qtbase)
svg_prefix=$(/opt/homebrew/bin/brew --prefix qtsvg)
args=("$app" -no-plugins -no-codesign -libpath=/opt/homebrew/lib
    "-executable=$app/Contents/MacOS/redpanda-git-askpass")
copy_plugin() {
    source=$1
    relative=$2
    mkdir -p "$app/Contents/PlugIns/$(dirname "$relative")"
    cp "$source" "$app/Contents/PlugIns/$relative"
    args+=("-executable=$app/Contents/PlugIns/$relative")
}
for relative in platforms/libqcocoa.dylib styles/libqmacstyle.dylib \
    imageformats/libqgif.dylib imageformats/libqico.dylib imageformats/libqjpeg.dylib \
    tls/libqsecuretransportbackend.dylib; do
    copy_plugin "$qt_prefix/share/qt/plugins/$relative" "$relative"
done
for relative in imageformats/libqsvg.dylib iconengines/libqsvgicon.dylib; do
    copy_plugin "$svg_prefix/share/qt/plugins/$relative" "$relative"
done
"$qt_prefix/bin/macdeployqt" "${args[@]}"
mkdir -p "$app/Contents/Resources"
printf '[Paths]\nPlugins = PlugIns\n' > "$app/Contents/Resources/qt.conf"
