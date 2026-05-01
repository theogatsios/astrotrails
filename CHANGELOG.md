# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to calendar versioning (`YYYY.M.D`).

## [2026.4.22]

### Fixed

- **Cancel button now actually works.**  Previously, the `QPushButton#danger`
  CSS rules took precedence over the generic `QPushButton:disabled` rule due
  to selector specificity, leaving the disabled Cancel button looking
  identical to its enabled state.  Hover did nothing, clicks did nothing.
  Added an explicit `QPushButton#danger:disabled` rule so the disabled
  state is visibly greyed out, and the click flow works as designed.
- **Pillow 12+ compatibility.**  Dropped the deprecated `mode="RGB"` keyword
  in `Image.fromarray()` calls (Pillow infers it from `dtype`+`shape` for
  uint8 HxWx3 arrays).  Without this, tests fail on Pillow ≥ 12.
- Tightened the pytest warning filter from blanket `error` to
  `error::ResourceWarning` plus an ignore for Pillow's own deprecations,
  so CI remains strict about real fd/resource leaks but isn't held hostage
  by upstream API churn.

### Changed

- **Window title** is now `Astrotrails` (capital A) — display only; the
  package name, CLI command, and import path stay lowercase.
- **Checkboxes** now show a teal ✓ checkmark on a transparent background
  when checked, replacing the previous solid-teal fill.  The glyph ships
  as a real `assets/check.svg` file inside the package; QSS resolves it by
  absolute path at runtime since Qt's stylesheet engine doesn't accept
  inline `data:` URIs.
- **GUI layout:** preview panel moved above the log panel, and the
  preview's "PREVIEW" group-box header is gone — the image area now sits
  flush with a single subtle border.  Placeholder text reworded from
  "(the stacked image will appear here)" to "Generated image will appear
  here".

---



### License

- **Relicensed from MIT to GPL-3.0-or-later.**  Every source file now carries
  an SPDX identifier and a GPL notice; the full licence text is bundled as
  `LICENSE.txt`.

### Added

- **Comet mode** (`StackMode.COMET`) with a configurable `comet_length`
  parameter.  Older contributions fade so star trails tail away like the
  head of a comet.
- **Dark-frame subtraction** (`--dark-frame` on the CLI, dedicated picker in
  the GUI) using an int16 intermediate to prevent uint8 underflow.
- **Parallel image decoding** with a bounded prefetch queue
  (`StackParams.workers`, `StackParams.prefetch`).
- **TIFF and PNG input support**, including 16-bit TIFFs (rescaled to 8-bit).
- **EXIF passthrough** from the first input image to the saved output.
- **PyQt6 desktop GUI** in the "Awesome dark" style, with working cancel,
  live progress bar, log view, and in-app result preview.
- `python -m astrotrails` now works as an alternate CLI entry point.
- Optional install extras: `[gui]` for the PyQt6 GUI, `[dev]` for
  development tooling.
- Cross-platform distribution: `.deb`, `.AppImage`, Windows `.exe`, Docker.
- `pytest` test suite covering stacking, ffmpeg pipe, and CLI.
- GitHub Actions CI across Python 3.9–3.13 on Linux, macOS, Windows.

### Changed

- **CLI redesigned around `argparse`.**  Positional mode-number argument
  (`1`/`2`/`3`/`4`) is gone.  Composable flags `--no-image`, `--no-video`,
  `--mode`, etc. replace it.
- **ffmpeg invocation rewritten.**  Frames are piped to ffmpeg over stdin;
  the old `StackingSBS/` scratch directory and its N intermediate JPEGs are
  gone entirely.  `subprocess.run` with a list of arguments replaces the old
  `os.system` call, closing a shell-injection hole.
- **ffmpeg dependency fixed.**  The misnamed `ffmpeg` PyPI package (a stub
  that does not include the binary) is replaced with `imageio-ffmpeg`,
  which bundles a cross-platform ffmpeg executable.  A system ffmpeg on
  `PATH` is preferred when present.
- Accumulator is now `uint8` throughout, roughly 4× less memory than the
  previous `float64` buffer.
- Switched to `pathlib`; `os.chdir` calls eliminated.
- GUI ported from customtkinter/ttkthemes to PyQt6 with a proper
  `QThread` worker (no more Tk-from-worker-thread races or `global`
  variables).

### Fixed

- GUI "Video" mode no longer silently picks between two branches depending
  on whether a leftover `StackingSBS/` directory exists.
- GUI no longer writes outputs to the *parent* of the selected directory.
- File-extension filter is now case-insensitive and accepts `.jpeg`/`.JPEG`
  in addition to `.jpg`/`.JPG`.
- Progress bar shows real progress instead of an indeterminate bounce.
- Errors from ffmpeg bubble up to the user instead of being hidden behind
  `>/dev/null 2>&1`.

### Removed

- Internal `StackingSBS/` directory and per-frame JPEG artefacts.
- Public functions `stacking`, `stackingSBS`, `timelapseVideo`, `manual`
  (superseded by `stack`, `stack_frames`, `FFmpegPipeWriter`).  Downstream
  users must migrate to the new API.
- `customtkinter` and `ttkthemes` dependencies.

---

## [2023.10.13]

Last release on the MIT licence.  Functional baseline: lighten stacking,
step-by-step JPEG output, `os.system("ffmpeg ...")` video generation,
customtkinter/ttkthemes GUI.

## [2023.9.13], [2023.9.4], [0.1.3]

Early releases.  See git history.
