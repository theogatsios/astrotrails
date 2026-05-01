# SPDX-License-Identifier: GPL-3.0-or-later
"""ffmpeg wrapper: pipe raw RGB frames to an encoder via stdin.

No temporary frame files are written.  ffmpeg is located by:

1. ``$ASTROTRAILS_FFMPEG`` if set (explicit override).
2. The first ``ffmpeg`` executable found on ``PATH``.
3. The binary bundled with ``imageio-ffmpeg`` (installed as a dependency).
"""
from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
from pathlib import Path

import numpy as np


class FFmpegNotFound(RuntimeError):
    """Raised when no usable ffmpeg binary can be located."""


def find_ffmpeg() -> str:
    """Locate an ffmpeg binary.  See module docstring for resolution order."""
    override = os.environ.get("ASTROTRAILS_FFMPEG")
    if override and Path(override).is_file() and os.access(override, os.X_OK):
        return override

    system = shutil.which("ffmpeg")
    if system:
        return system

    try:
        import imageio_ffmpeg  # type: ignore[import-not-found]
    except ImportError as e:
        raise FFmpegNotFound(
            "ffmpeg not found on PATH and imageio-ffmpeg is not installed. "
            "Install ffmpeg system-wide or `pip install imageio-ffmpeg`."
        ) from e

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as e:  # noqa: BLE001 — imageio-ffmpeg raises various types
        raise FFmpegNotFound(f"imageio-ffmpeg failed to provide a binary: {e}") from e


class FFmpegPipeWriter:
    """Context manager that pipes uint8 RGB frames to ffmpeg via stdin.

    Example::

        with FFmpegPipeWriter("out.mp4", width=1920, height=1080, fps=25) as w:
            for frame in frames:
                w.write_frame(frame)
    """

    def __init__(
        self,
        output_path: Path | str,
        width: int,
        height: int,
        fps: int = 25,
        crf: int = 18,
        preset: str = "medium",
        codec: str = "libx264",
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.output_path = Path(output_path)
        self.width = width
        self.height = height
        self.fps = fps
        self.crf = crf
        self.preset = preset
        self.codec = codec
        self._proc: subprocess.Popen[bytes] | None = None
        self._stderr_tail: list[str] = []

    # ------------------------------------------------------------------ context
    def __enter__(self) -> FFmpegPipeWriter:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd: list[str] = [
            find_ffmpeg(),
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{self.width}x{self.height}",
            "-r", str(self.fps),
            "-i", "-",
            "-c:v", self.codec,
            "-preset", self.preset,
            "-crf", str(self.crf),
            "-pix_fmt", "yuv420p",
            # libx264 requires even dimensions; pad if necessary.
            "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
            str(self.output_path),
        ]
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        return self

    # ------------------------------------------------------------------ write
    def write_frame(self, frame: np.ndarray) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise RuntimeError("writer not entered")
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8, copy=False)
        if frame.shape != (self.height, self.width, 3):
            raise ValueError(
                f"frame shape {frame.shape} != ({self.height},{self.width},3)"
            )
        try:
            self._proc.stdin.write(frame.tobytes())
        except BrokenPipeError as e:
            # ffmpeg died — surface whatever it told us.
            stderr = self._drain_stderr()
            raise RuntimeError(f"ffmpeg closed its pipe: {stderr}") from e

    # ------------------------------------------------------------------ exit
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if self._proc is None:
            return False
        assert self._proc.stdin is not None
        with contextlib.suppress(BrokenPipeError):
            self._proc.stdin.close()
        rc = self._proc.wait()
        stderr = self._drain_stderr()
        self._close_stderr()
        if exc_type is None and rc != 0:
            raise RuntimeError(f"ffmpeg exited with code {rc}:\n{stderr}")
        return False  # don't suppress any in-flight exception

    def _drain_stderr(self) -> str:
        if self._proc is None or self._proc.stderr is None:
            return ""
        try:
            data = self._proc.stderr.read()
        except Exception:
            return ""
        return data.decode("utf-8", errors="replace") if data else ""

    def _close_stderr(self) -> None:
        if self._proc is not None and self._proc.stderr is not None:
            with contextlib.suppress(Exception):
                self._proc.stderr.close()
