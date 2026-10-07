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
    --prefix) [ $# -ge 2 ] || { echo "--prefix needs a folder" >&2; exit 2; }; shift; prefix="$1" ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ ! -x "$here/harness-tool" ] || [ ! -d "$here/_internal" ]; then
  echo "This folder ($here) has no built program, so there is nothing to install." >&2
  echo "Run install.sh from the unpacked harness-tool-<version>-linux-<arch>.tar.gz," >&2
  echo "or install the .deb. To build the package from source: python -m tools.build_installer" >&2
  echo "(it writes dist/harness-tool/ with this script inside)." >&2
  exit 1
fi
if [ -z "$prefix" ]; then
  # /opt/harness-tool belongs to the .deb; a local system install must not touch its files
  if [ "$mode" = system ]; then prefix=/usr/local/lib/harness-tool; else prefix="${HOME}/.local/opt/harness-tool"; fi
fi
case "$prefix" in /*) ;; *) prefix="$(pwd)/$prefix" ;; esac   # links and the launcher need an absolute path
prefix=$(printf '%s' "$prefix" | sed 's://*:/:g; s:/$::')
if [ "$prefix" = "$here" ] || [ "$prefix" = "" ]; then
  echo "The install folder must not be the folder the package was unpacked in." >&2
  exit 2
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
for name in harness-tool harness; do   # never replace a program the user put there themselves
  if [ -e "$bindir/$name" ] || [ -L "$bindir/$name" ]; then
    if [ ! -L "$bindir/$name" ]; then
      echo "$bindir/$name exists and is not a link made by this installer; not touching it." >&2
      exit 1
    fi
  fi
done
mkdir -p "$prefix" "$bindir" "$appdir" "$icondir"
for item in harness-tool _internal cli LICENSES; do
  [ -e "$here/$item" ] && { rm -rf "${prefix:?}/$item"; cp -a "$here/$item" "$prefix/$item"; }
done
ln -sf "$prefix/harness-tool" "$bindir/harness-tool"
ln -sf "$prefix/cli/harness" "$bindir/harness"
# the launcher line must survive spaces and special characters in the path (desktop entry quoting)
quoted=$(printf '%s' "$prefix/harness-tool" | sed 's/[\\"`$]/\\&/g; s/%/%%/g')
: > "$appdir/harness-tool.desktop"
while IFS= read -r line; do
  case "$line" in
    *@EXEC@*) line="${line%%@EXEC@*}\"$quoted\"${line#*@EXEC@}" ;;
  esac
  case "$line" in
    *@ICON@*) line="${line%%@ICON@*}harness-tool${line#*@ICON@}" ;;
  esac
  printf '%s\n' "$line" >> "$appdir/harness-tool.desktop"
done < "$here/harness-tool.desktop.in"
cp "$here/harness-tool.svg" "$icondir/harness-tool.svg"
echo "Installed to $prefix. Start it from the application menu or run: harness-tool"
case ":$PATH:" in
  *":$bindir:"*) ;;
  *)
    echo "Note: $bindir is not on your PATH, so the commands harness-tool and harness are not found yet."
    echo "  Run now:     $bindir/harness-tool"
    echo "  Fix for good: echo 'export PATH=\"$bindir:\$PATH\"' >> ~/.bashrc && . ~/.bashrc"
    echo "  (or log out and in again; Ubuntu adds ~/.local/bin at login when it exists)"
    ;;
esac
