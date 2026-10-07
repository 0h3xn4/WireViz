#!/bin/sh
# Install Harness tool for the current user (no administrator rights), or system-wide with --system.
# Usage: ./install.sh [--prefix DIR] [--system]
set -eu
here=$(cd "$(dirname "$0")" && pwd)
mode=user
prefix=""
while [ $# -gt 0 ]; do
  case "$1" in
    --system) mode=system ;;
    --prefix) shift; prefix="$1" ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ -z "$prefix" ]; then
  if [ "$mode" = system ]; then prefix=/opt/harness-tool; else prefix="${HOME}/.local/opt/harness-tool"; fi
fi
if [ "$mode" = system ]; then
  bindir=/usr/local/bin; appdir=/usr/share/applications; icondir=/usr/share/icons/hicolor/scalable/apps
else
  base="${XDG_DATA_HOME:-$HOME/.local/share}"
  bindir="${HOME}/.local/bin"; appdir="$base/applications"; icondir="$base/icons/hicolor/scalable/apps"
fi
# --prefix with an explicit test root keeps links inside it
if [ -n "${HARNESS_INSTALL_ROOT:-}" ]; then
  bindir="$HARNESS_INSTALL_ROOT/bin"; appdir="$HARNESS_INSTALL_ROOT/share/applications"; icondir="$HARNESS_INSTALL_ROOT/share/icons"
fi
mkdir -p "$prefix" "$bindir" "$appdir" "$icondir"
for item in harness-tool _internal cli; do
  [ -e "$here/$item" ] && { rm -rf "${prefix:?}/$item"; cp -a "$here/$item" "$prefix/$item"; }
done
ln -sf "$prefix/harness-tool" "$bindir/harness-tool"
ln -sf "$prefix/cli/harness" "$bindir/harness"
sed "s|@EXEC@|$prefix/harness-tool|; s|@ICON@|harness-tool|" "$here/harness-tool.desktop.in" > "$appdir/harness-tool.desktop"
cp "$here/harness-tool.svg" "$icondir/harness-tool.svg"
echo "Installed to $prefix. Start it from the application menu or run: harness-tool"
case ":$PATH:" in *":$bindir:"*) ;; *) echo "Note: $bindir is not on your PATH." ;; esac
