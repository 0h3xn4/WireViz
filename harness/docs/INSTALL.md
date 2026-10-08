# Install

The tool runs on **Ubuntu 24.04 or newer** (64-bit, x86). It needs no network, no administrator account for the per-user install, and no other software to be installed first (Python and Qt are inside the package).

Pick **one** of the three ways. If you are unsure, use A.

| | You are | Way |
| --- | --- | --- |
| **A** | an engineer who wants to use the tool | install the `.deb` package |
| **B** | the same, without administrator rights | unpack the `.tar.gz` and run `install.sh` |
| **C** | a developer or you want the newest source | run it from source |

## Get the package

You need one file, either `harness-design-studio_<version>_amd64.deb` (way A) or `harness-design-studio-<version>-linux-<arch>.tar.gz` (way B). Your tool administrator provides it, or you take it from the build artifacts of the project's CI run (the artifact is called `harness-design-studio-ubuntu-24.04`). You can also build it yourself (way C, last section).

Copy the file to the machine. It never needs to reach the network.

## A. The `.deb` package (recommended)

```
sudo apt install ./harness-design-studio_<version>_amd64.deb
```

(Use `./` in front of the name; without it `apt` looks in its online lists.) This installs the program into `/opt/harness-design-studio` and puts two commands on your path:

- `harness-design-studio`: the app (also in the application menu as **Harness Design Studio**).
- `harness`: the command line tool.

Check it:

```
harness --version
```

```
harness 0.1.0rc5
```

Remove it later with `sudo apt remove harness-design-studio`. Upgrade by installing the newer `.deb` the same way.

## B. The `.tar.gz` without administrator rights

```
tar xzf harness-design-studio-<version>-linux-<arch>.tar.gz
cd harness-design-studio
./install.sh
```

This installs for **your user only**, into `~/.local/opt/harness-design-studio`, and adds links in `~/.local/bin` and an entry in your application menu.

If `install.sh` ends with a note that `~/.local/bin` is not on your PATH, the commands `harness-design-studio` and `harness` are not found yet. Fix it once:

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
. ~/.bashrc
```

(or log out and in). Until then you can start the app from the application menu or `~/.local/bin/harness-design-studio`.

Other options of `install.sh`: `sudo ./install.sh --system` installs for everyone into `/usr/local/lib/harness-design-studio`; `--prefix FOLDER` chooses the folder. Remove with `./uninstall.sh` (or `sudo ./uninstall.sh --system`); it removes only what the installer put there.

Run `install.sh` from the **unpacked package**. Run from the source tree it refuses, because the built program is missing there.

## Check that it works

```
harness --version          # prints the version
harness-design-studio --selftest    # opens the editor offscreen, makes a project, generates, exports, and prints "selftest ok"
```

Then start **Harness Design Studio** from the application menu. The first start opens a sample project and a short tour.

## If the app does not start

The app needs a few system libraries that every normal Ubuntu desktop has. On a minimal install (a container, a server image) add them:

```
sudo apt install libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 libxcb-cursor0
```

The `.deb` asks `apt` for these itself. More help: [`FAQ.md`](FAQ.md).

## C. Run from source (developers)

You need Python 3.12 or newer (Ubuntu 24.04 has it) and the Qt libraries above.

```
sudo apt install python3-venv git libegl1 libgl1 libxkbcommon0 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 libxcb-cursor0
git clone <the repository> && cd <the repository>/harness
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[gui,dev]"
```

Run the app with `harness-gui`, the command line tool with `harness`. Run the tests with `pytest` (they run offscreen). **Without network:** build a wheelhouse once on a connected machine with `python -m tools.vendor`, copy it over and install with `pip install --no-index --find-links wheelhouse -e ".[gui,dev]"`.

Build the packages yourself:

```
python -m tools.build_installer      # dist/harness-design-studio/ and the .tar.gz
python -m tools.build_deb            # dist/harness-design-studio_<version>_amd64.deb
dist/harness-design-studio/harness-design-studio --selftest
```

The release procedure and the clean-machine check are in [`RELEASE.md`](RELEASE.md).

## Where things are stored

| What | Where |
| --- | --- |
| Your projects | wherever you saved them (a folder per project) |
| App settings (theme, scale, last project) | `~/.config/HarnessDesigner/HarnessDesigner.ini` (no design data) |
| Autosave of an open project | `<project>/.harness-recovery/` (offered for restore after a crash; ignored by Git) |

Next: [`GETTING_STARTED.md`](GETTING_STARTED.md).
