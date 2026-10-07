#!/bin/sh
# Remove what install.sh installed. Usage: ./uninstall.sh [--prefix DIR] [--system]
set -eu
mode=user
prefix=""
while [ $# -gt 0 ]; do
  case "$1" in
    --system) mode=system ;;
    --prefix) shift; prefix="$1" ;;
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
if [ -n "${HARNESS_INSTALL_ROOT:-}" ]; then
  bindir="$HARNESS_INSTALL_ROOT/bin"; appdir="$HARNESS_INSTALL_ROOT/share/applications"; icondir="$HARNESS_INSTALL_ROOT/share/icons"
fi
rm -f "$bindir/harness-tool" "$bindir/harness" "$appdir/harness-tool.desktop" "$icondir/harness-tool.svg"
rm -rf "${prefix:?}"
echo "Removed. Your projects are not touched."
