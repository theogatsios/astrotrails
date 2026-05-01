# astrotrails

[![PyPI](https://img.shields.io/pypi/v/astrotrails.svg)](https://pypi.org/project/astrotrails/)
[![Python](https://img.shields.io/pypi/pyversions/astrotrails.svg)](https://pypi.org/project/astrotrails/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CI](https://github.com/theogatsios/astrotrails/actions/workflows/ci.yml/badge.svg)](https://github.com/theogatsios/astrotrails/actions)

Stack a directory of night-sky photographs into a startrails image and/or a
timelapse video.  Pure-Python, cross-platform, with both a command-line
interface and a PyQt6 desktop application.

![Demo](documentation/demo.gif)

---

## Features

- **Max-value stacking** (classic lighten composite).
- **Comet mode** with a configurable fade tail — older contributions decay,
  mimicking a star's forward motion.
- **Dark-frame subtraction** to suppress hot pixels and amp glow.
- **Timelapse video** written directly from memory — frames are piped to
  ffmpeg via stdin, no intermediate disk files.
- **Parallel image decoding** via a bounded prefetch thread pool.
- **EXIF passthrough** from the first input to the stacked output.
- **Inputs:** JPEG, TIFF (8- and 16-bit), PNG.
- **Outputs:** JPEG, TIFF, PNG for images; MP4 (H.264) for video.
- **Cross-platform installers:** PyPI wheel, `.deb`, `.AppImage`, Windows
  `.exe`, and a CLI-only Docker image.

## Install

### From PyPI

```bash
pip install astrotrails              # CLI only (no GUI dependencies)
pip install "astrotrails[gui]"       # CLI + PyQt6 desktop GUI
```

The PyPI package depends on `imageio-ffmpeg`, which bundles a working ffmpeg
binary for the three major desktop platforms.  If a system ffmpeg is on
`PATH`, astrotrails will prefer it automatically.

### From a binary release

Pre-built artefacts for each tagged release live on the
[GitHub Releases](https://github.com/theogatsios/astrotrails/releases) page:

| Platform          | Artefact                         |
|-------------------|----------------------------------|
| Linux (Debian/Ubuntu) | `astrotrails_<ver>_amd64.deb`   |
| Linux (any glibc) | `astrotrails-<ver>-x86_64.AppImage` |
| Windows 10/11     | `astrotrails-<ver>-win64.exe`    |
| Docker (CLI)      | `ghcr.io/theogatsios/astrotrails:<ver>` |

## Usage

### Command line

```bash
# classic lighten stack + 25 fps timelapse
astrotrails /path/to/jpegs

# comet mode with a 100-frame tail, video only, 30 fps
astrotrails /path/to/jpegs --mode comet --comet-length 100 --no-image --fps 30

# subtract a dark frame, write outputs to a separate directory
astrotrails /path/to/jpegs -o /tmp/out --dark-frame /path/to/dark.jpg
```

Full reference:

```
astrotrails [-h] [-o OUTPUT] [--mode {max,comet}] [--comet-length N]
            [--dark-frame PATH] [--image NAME] [--video NAME]
            [--fps N] [--crf N] [--no-image] [--no-video]
            [--workers N] [-q] [-V]
            INPUT
```

### Graphical interface

```bash
astrotrails-gui
```

Pick an input folder, optionally an output folder and a dark frame, choose
max or comet mode, click **Generate**.  A live progress bar and log keep you
informed; the stacked image is previewed in-app when the run finishes.

### Python API

```python
from pathlib import Path
from astrotrails import (
    StackMode, StackParams, list_images, stack, save_image,
    FFmpegPipeWriter,
)
from astrotrails.core import stack_frames
from PIL import Image

images = list_images("night_sky/")
params = StackParams(mode=StackMode.COMET, comet_length=80, workers=6)

with Image.open(images[0]) as im:
    w, h = im.size

with FFmpegPipeWriter("out.mp4", w, h, fps=30) as writer:
    last = None
    for frame in stack_frames(images, params):
        writer.write_frame(frame)
        last = frame

save_image(last, "stacked.jpg", exif_source=images[0])
```

## Building

See [BUILDING.md](BUILDING.md) for step-by-step instructions covering PyPI,
`.deb`, `.AppImage`, Windows `.exe`, and Docker.

## Development

```bash
git clone https://github.com/theogatsios/astrotrails.git
cd astrotrails
python -m venv .venv && source .venv/bin/activate
pip install -e ".[gui,dev]"
pytest
ruff check .
```

## Troubleshooting

- **"ffmpeg not found"** — either install ffmpeg system-wide or install the
  `imageio-ffmpeg` Python package (normally pulled in as a dependency).
- **GUI cannot start on a headless box** — PyQt6 needs a display server.
  On WSL or SSH sessions, use X11 forwarding or run the CLI instead.
- **Mismatched image sizes** — all input images must share the same
  resolution.  Resize or crop beforehand with your camera tether or a batch
  tool.

## License

Copyright © 2026 Theodoros Gatsios.  Licensed under the
**GNU General Public License v3.0 or later** — see [LICENSE.txt](LICENSE.txt).

This program is distributed in the hope that it will be useful, but **without
any warranty**; without even the implied warranty of merchantability or
fitness for a particular purpose.
