#!/bin/sh
# Run inside the 22.04 build image with the source mounted at /src: installs the pinned
# dependencies, runs the whole release checklist and leaves the packages in dist/.
set -eu
cd /src
python3.11 -m venv /tmp/venv
. /tmp/venv/bin/activate
pip install -e ".[gui,dev]"
export QT_QPA_PLATFORM=offscreen
python -m tools.release_check
ls -l dist/*.deb dist/*.tar.gz
