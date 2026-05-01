# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared pytest fixtures."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image


def _write_jpeg(path: Path, arr: np.ndarray) -> None:
    Image.fromarray(arr, mode="RGB").save(path, "JPEG", quality=95)


@pytest.fixture
def synth_frames(tmp_path: Path) -> list[Path]:
    """Three 64×64 frames with a single bright pixel each, in known positions."""
    positions = [(10, 10), (30, 30), (50, 50)]
    paths: list[Path] = []
    for i, (r, c) in enumerate(positions):
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        arr[r, c] = [250, 240, 230]
        p = tmp_path / f"frame_{i:03d}.jpg"
        _write_jpeg(p, arr)
        paths.append(p)
    return paths


@pytest.fixture
def synth_dark_frame(tmp_path: Path) -> Path:
    """Uniform dark frame for subtraction tests."""
    arr = np.full((64, 64, 3), 5, dtype=np.uint8)
    p = tmp_path / "dark.jpg"
    _write_jpeg(p, arr)
    return p
