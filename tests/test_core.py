# SPDX-License-Identifier: GPL-3.0-or-later
"""Tests for the core stacking engine."""
from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import pytest

from astrotrails.core import (
    StackMode,
    StackParams,
    list_images,
    load_dark_frame,
    save_image,
    stack,
    stack_frames,
)


def test_list_images_sorts_and_filters(tmp_path: Path, synth_frames: list[Path]) -> None:
    # drop a non-image to verify it's skipped
    (tmp_path / "readme.txt").write_text("ignore me")
    (tmp_path / "cover.PNG").write_bytes(synth_frames[0].read_bytes())  # wrong casing
    found = list_images(tmp_path)
    assert len(found) >= 3
    assert all(p.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff"} for p in found)
    assert found == sorted(found)


def test_max_stack_preserves_bright_pixels(synth_frames: list[Path]) -> None:
    result = stack(synth_frames, StackParams(mode=StackMode.MAX))
    # each frame's bright pixel should survive the stack
    for r, c in [(10, 10), (30, 30), (50, 50)]:
        assert result[r, c].mean() > 100, f"lost pixel at ({r},{c})"
    # background should stay near zero
    assert result[0, 0].max() < 20


def test_comet_mode_fades_old_contributions(synth_frames: list[Path]) -> None:
    out_max = stack(synth_frames, StackParams(mode=StackMode.MAX))
    out_comet = stack(synth_frames, StackParams(mode=StackMode.COMET, comet_length=2))
    # oldest bright pixel should be much dimmer in comet mode
    old_max = int(out_max[10, 10].mean())
    old_comet = int(out_comet[10, 10].mean())
    assert old_comet < old_max - 30, (old_max, old_comet)
    # newest bright pixel should be roughly preserved
    new_max = int(out_max[50, 50].mean())
    new_comet = int(out_comet[50, 50].mean())
    assert abs(new_comet - new_max) < 20


def test_dark_frame_subtracts_without_underflow(
    synth_frames: list[Path], synth_dark_frame: Path
) -> None:
    dark = load_dark_frame(synth_dark_frame)
    out = stack(synth_frames, StackParams(dark_frame=dark))
    # Result stays uint8 and non-negative everywhere
    assert out.dtype == np.uint8
    assert out.min() >= 0


def test_stack_frames_yields_monotonic_max(synth_frames: list[Path]) -> None:
    previous: np.ndarray | None = None
    for frame in stack_frames(synth_frames, StackParams(mode=StackMode.MAX)):
        if previous is not None:
            # classic lighten stack is monotonically non-decreasing per pixel
            assert np.all(frame >= previous)
        previous = frame.copy()


def test_cancel_event_stops_stacking(synth_frames: list[Path]) -> None:
    event = threading.Event()
    event.set()  # pre-cancel
    with pytest.raises(RuntimeError, match="cancelled"):
        list(stack_frames(synth_frames, cancel=event))


def test_save_image_roundtrip(synth_frames: list[Path], tmp_path: Path) -> None:
    out = stack(synth_frames, StackParams())
    target = tmp_path / "stacked.jpg"
    save_image(out, target, exif_source=synth_frames[0])
    assert target.is_file()
    assert target.stat().st_size > 0


def test_empty_input_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        stack([], StackParams())


def test_invalid_stack_params() -> None:
    with pytest.raises(ValueError):
        StackParams(comet_length=1)
    with pytest.raises(ValueError):
        StackParams(workers=0)
