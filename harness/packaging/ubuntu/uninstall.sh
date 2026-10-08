#!/bin/sh
# Remove what install.sh installed. Usage: ./uninstall.sh [--prefix DIR] [--system]
set -eu
mode=user
prefix=""
while [ $# -gt 0 ]; do
  case "$1" in
    --system) mode=system ;;
    --prefix) [ $# -ge 2 ] || { echo "--prefix needs a folder" >&2; exit 2; }; shift; prefix="$1" ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ -z "$prefix" ]; then
  if [ "$mode" = system ]; then prefix=/usr/local/lib/harness-tool; else prefix="${HOME}/.local/opt/harness-tool"; fi
fi
case "$prefix" in /*) ;; *) prefix="$(pwd)/$prefix" ;; esac
prefix=$(printf '%s' "$prefix" | sed 's://*:/:g; s:/$::')
if [ "$mode" = system ]; then
  bindir=/usr/local/bin; appdir=/usr/share/applications; icondir=/usr/share/icons/hicolor/scalable/apps
else
  base="${XDG_DATA_HOME:-$HOME/.local/share}"
  bindir="${HOME}/.local/bin"; appdir="$base/applications"; icondir="$base/icons/hicolor/scalable/apps"
fi
if [ -n "${HARNESS_INSTALL_ROOT:-}" ]; then
  bindir="$HARNESS_INSTALL_ROOT/bin"; appdir="$HARNESS_INSTALL_ROOT/share/applications"; icondir="$HARNESS_INSTALL_ROOT/share/icons"
fi
removed=0
# remove a link only if it points into this install; never delete a program that is not ours
for pair in "harness-tool:$prefix/harness-tool" "harness:$prefix/cli/harness"; do
  name=${pair%%:*}; target=${pair#*:}
  if [ -L "$bindir/$name" ] && [ "$(readlink "$bindir/$name")" = "$target" ]; then
    rm -f "$bindir/$name"; removed=1
  fi
done
for f in "$appdir/harness-tool.desktop" "$icondir/harness-tool.svg"; do
  [ -e "$f" ] && { rm -f "$f"; removed=1; }
done
# only what the installer put in the folder; anything else the user keeps there stays
if [ -n "$prefix" ] && [ "$prefix" != "/" ]; then
  for item in harness-tool _internal cli LICENSES; do
    [ -e "$prefix/$item" ] && { rm -rf "${prefix:?}/$item"; removed=1; }
  done
  rmdir "$prefix" 2>/dev/null || true
fi
if [ "$removed" = 1 ]; then
  echo "Removed. Your projects are not touched."
else
  echo "Nothing to remove: Harness Design Studio is not installed there (looked in $prefix)."
fi
