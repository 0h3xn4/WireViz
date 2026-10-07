"""PyInstaller entry point; `--selftest` creates the window offscreen and exits (used by CI)."""

import os
import sys

from harness_tool.gui.app import create_window, main

if __name__ == "__main__":
    if "--selftest" in sys.argv:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        win = create_window()
        win.show()
        print("selftest ok")
        raise SystemExit(0)
    raise SystemExit(main())
