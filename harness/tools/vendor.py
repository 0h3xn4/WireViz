"""Download every pinned wheel into a local folder for offline installs (run on a connected host).

Install later without network:  pip install --no-index --find-links wheelhouse harness-tool[gui]
"""

import subprocess
import sys
from pathlib import Path


def main(dest: str = "wheelhouse", extras: str = "gui,dev") -> int:
    Path(dest).mkdir(exist_ok=True)
    cmd = [sys.executable, "-m", "pip", "download", "--dest", dest, f".[{extras}]"]
    return subprocess.run(cmd, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]))
