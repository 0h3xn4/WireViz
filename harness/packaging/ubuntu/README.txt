Harness Design Studio: Ubuntu package
============================
Per-user install (no administrator rights):   ./install.sh
System-wide install:                          sudo ./install.sh --system   (into /usr/local/lib/harness-tool)
Remove:                                       ./uninstall.sh   (or: sudo ./uninstall.sh --system)

Needs these system libraries (already present on a normal Ubuntu desktop):
  libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 libxcb-cursor0
  Install with: sudo apt install libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 libxcb-cursor0

The tool never uses the network. The user guide opens with F1 inside the app.
Check the package: ./harness-tool --selftest
