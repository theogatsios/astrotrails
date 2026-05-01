# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end smoke test of the CLI."""
from __future__ import annotations

from pathlib import Path

from astrotrails.cli import main


def test_cli_produces_outputs(synth_frames: list[Path], tmp_path: Path) -> None:
    input_dir = synth_frames[0].parent
    out_dir = tmp_path / "out"
    rc = main([
        str(input_dir),
        "-o", str(out_dir),
        "--fps", "10",
        "--quiet",
    ])
    assert rc == 0
    assert (out_dir / "Stacked.jpg").is_file()
    assert (out_dir / "timelapse.mp4").is_file()


def test_cli_rejects_empty_input(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    rc = main([str(empty), "--quiet"])
    assert rc != 0
