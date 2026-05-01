# Building astrotrails

This guide covers every distribution target: **PyPI**, **Debian/Ubuntu
`.deb`**, **Linux `.AppImage`**, **Windows `.exe`**, and **Docker**.  All
build scripts live under `packaging/`; the commands below assume the
repository root as the working directory.

---

## Table of contents

1. [Build prerequisites](#build-prerequisites)
2. [PyPI: sdist and wheel](#pypi-sdist-and-wheel)
3. [Linux: `.deb` with `fpm`](#linux-deb-with-fpm)
4. [Linux: `.AppImage` with `python-appimage`](#linux-appimage-with-python-appimage)
5. [Windows: `.exe` with PyInstaller](#windows-exe-with-pyinstaller)
6. [Docker: CLI-only image](#docker-cli-only-image)
7. [Automating releases with GitHub Actions](#automating-releases-with-github-actions)

---

## Build prerequisites

All targets need a recent Python (≥ 3.9).  Each target has a couple of extra
tools listed in its own section.

```bash
python -m venv .venv
source .venv/bin/activate                # Linux/macOS
# .venv\Scripts\activate                 # Windows PowerShell
pip install --upgrade pip
pip install -e ".[gui,dev]"
pytest                                   # sanity-check the tree
```

Bump the version in `astrotrails/_version.py` and record changes in
`CHANGELOG.md` before cutting a release.

---

## PyPI: sdist and wheel

### Build

```bash
python -m build
```

That produces `dist/astrotrails-<ver>.tar.gz` and
`dist/astrotrails-<ver>-py3-none-any.whl`.

### Local verification

```bash
pip install --force-reinstall dist/astrotrails-*.whl
astrotrails --version
astrotrails-gui &        # optional, only if PyQt6 is installed
```

### Upload

TestPyPI first:

```bash
python -m twine upload --repository testpypi dist/*
pip install -i https://test.pypi.org/simple/ astrotrails
```

Then the real index:

```bash
python -m twine upload dist/*
```

Configure credentials once in `~/.pypirc` or use an API token via the
`TWINE_USERNAME=__token__` + `TWINE_PASSWORD=<token>` environment variables.
The GitHub Actions release workflow (below) uses the latter.

---

## Linux: `.deb` with `fpm`

[`fpm`](https://fpm.readthedocs.io) is the pragmatic path: one command
produces a working `.deb` from a pip-installed tree.  It supports RPM, APK,
and more if you need them later.

### Prerequisites

```bash
sudo apt install ruby ruby-dev build-essential
sudo gem install --no-document fpm
```

### Build

```bash
packaging/debian/build-deb.sh
```

The resulting file lands at `packaging/debian/astrotrails_<ver>_amd64.deb`.

### Install / uninstall

```bash
sudo apt install ./packaging/debian/astrotrails_*_amd64.deb
astrotrails --version
sudo apt remove astrotrails
```

The `.deb` declares `python3 (>= 3.9)`, `python3-pip`, `ffmpeg`, and
`python3-pyqt6` as runtime dependencies.  pip deps that are not packaged by
Debian (`imageio-ffmpeg`, recent `numpy`/`Pillow`) are vendored into
`/opt/astrotrails` by the build script so the `.deb` works on a stock
Debian/Ubuntu system without further `pip install`s.

### Desktop integration

The build script installs `astrotrails.desktop` under
`/usr/share/applications` so the GUI shows up in the system menu, and a
64×64 PNG icon under `/usr/share/icons/hicolor/64x64/apps/`.

---

## Linux: `.AppImage` with `python-appimage`

[`python-appimage`](https://github.com/niess/python-appimage) bundles a
relocatable Python, a pip-installed copy of your package, and its
dependencies into a single `.AppImage` that runs on any glibc ≥ 2.28 system.

### Prerequisites

```bash
pip install --user python-appimage
# on minimal systems you may also need FUSE for running .AppImages:
sudo apt install libfuse2
```

### Build

```bash
packaging/appimage/build-appimage.sh
```

Output: `packaging/appimage/astrotrails-<ver>-x86_64.AppImage`.

### Run

```bash
chmod +x astrotrails-*.AppImage
./astrotrails-*.AppImage            # launches the GUI
./astrotrails-*.AppImage --cli /path/to/jpegs
```

The wrapper script inside the AppImage inspects its first argument: if it
starts with `--cli`, control is routed to `astrotrails.cli:main`; otherwise
to `astrotrails.gui:main`.

---

## Windows: `.exe` with PyInstaller

### Prerequisites (on a Windows build host)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -e ".[gui,dev]"
pip install pyinstaller
```

### Build

```powershell
pyinstaller packaging\windows\astrotrails.spec --clean
```

Output: `dist\astrotrails-<ver>-win64.exe` — a single-file executable that
launches the GUI by default.  The bundled ffmpeg from `imageio-ffmpeg` is
included, so end-users do **not** need to install ffmpeg separately.

The spec produces two entry points:

- `dist\astrotrails-<ver>-win64.exe` — GUI launcher (no console window).
- `dist\astrotrails-<ver>-win64-cli.exe` — CLI (keeps a console window).

### Optional: Inno Setup installer

If you want a proper Windows installer (Start Menu shortcut, uninstall
entry), run Inno Setup on `packaging/windows/astrotrails.iss` after the
PyInstaller build.  Pre-install Inno Setup 6 and place the resulting
`AstrotrailsSetup.exe` next to the loose `.exe` files.

---

## Docker: CLI-only image

The Docker image ships only the CLI — running a PyQt6 GUI inside a container
needs X11 forwarding and is brittle.  Use the AppImage or native `.deb`
instead if you want the GUI in a Linux container-like setup.

### Build

```bash
docker build -t astrotrails:$(python -c 'import astrotrails; print(astrotrails.__version__)') \
             -f packaging/docker/Dockerfile .
```

### Run

```bash
docker run --rm -v "$PWD/input:/work/input" -v "$PWD/output:/work/output" \
           astrotrails:latest /work/input -o /work/output --mode comet
```

### Publish to GHCR

```bash
docker tag astrotrails:$VER ghcr.io/theogatsios/astrotrails:$VER
docker tag astrotrails:$VER ghcr.io/theogatsios/astrotrails:latest
docker push ghcr.io/theogatsios/astrotrails:$VER
docker push ghcr.io/theogatsios/astrotrails:latest
```

The GitHub Actions release workflow publishes these tags automatically on
`git push --tags`.

---

## Automating releases with GitHub Actions

Two workflows ship in `.github/workflows/`:

- **`ci.yml`** — runs `pytest` and `ruff` on Linux/macOS/Windows across
  Python 3.9–3.13 on every push and pull request.
- **`release.yml`** — triggered by pushing a tag of the form `v*`, it
  builds the PyPI wheel + sdist, the Linux `.deb`, the `.AppImage`, the
  Windows `.exe`, and the Docker image, then attaches them to a GitHub
  Release and publishes to PyPI + GHCR.

To cut a release:

```bash
# 1. bump astrotrails/_version.py, update CHANGELOG.md, commit
git commit -am "release 2026.4.21"

# 2. tag and push
git tag v2026.4.21
git push origin main --tags
```

The `release.yml` workflow takes over from there.  Populate the following
repository secrets:

| Secret              | Purpose                         |
|---------------------|---------------------------------|
| `PYPI_API_TOKEN`    | `twine upload` to PyPI          |
| `GITHUB_TOKEN`      | Provided automatically; used for GHCR and Release upload |
