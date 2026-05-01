# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the ffmpeg wrapper."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from astrotrails.video import FFmpegPipeWriter, find_ffmpeg


def test_find_ffmpeg_returns_path() -> None:
    path = find_ffmpeg()
    assert Path(path).exists()


def test_pipe_writer_produces_video(tmp_path: Path) -> None:
    out = tmp_path / "test.mp4"
    w, h = 32, 32
    with FFmpegPipeWriter(out, w, h, fps=10) as writer:
        for i in range(5):
            frame = np.full((h, w, 3), i * 40, dtype=np.uint8)
            writer.write_frame(frame)
    assert out.is_file()
    assert out.stat().st_size > 0


def test_pipe_writer_rejects_bad_shape(tmp_path: Path) -> None:
    out = tmp_path / "bad.mp4"
    with pytest.raises(ValueError), FFmpegPipeWriter(out, 32, 32, fps=10) as writer:
        writer.write_frame(np.zeros((16, 16, 3), dtype=np.uint8))
