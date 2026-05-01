# SPDX-License-Identifier: GPL-3.0-or-later
"""Stacking engine.

Provides max-value stacking and "comet" fade-tail stacking with optional
dark-frame subtraction.  Frames are decoded on a background thread pool so
the main thread can keep feeding ``numpy.maximum`` without blocking on I/O.
"""
from __future__ import annotations

import enum
import threading
from collections import deque
from collections.abc import Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from PIL import Image

# Formats Pillow handles natively that make sense for startrails input.
SUPPORTED_EXTS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".tif", ".tiff", ".png"}
)

ProgressFn = Callable[[int, int], None]
"""Progress callback: ``progress(current, total)``."""


class StackMode(str, enum.Enum):
    """Available stacking algorithms."""

    MAX = "max"        # classic lighten: per-pixel max over all frames
    COMET = "comet"    # fade tail: older frames decay, newer frames dominate


@dataclass
class StackParams:
    """Bundle of parameters for a stacking run."""

    mode: StackMode = StackMode.MAX
    comet_length: int = 50             # number of frames until a contribution fades
    dark_frame: np.ndarray | None = None  # uint8 HxWx3 to subtract from every input
    workers: int = 4                   # image-decode thread pool size
    prefetch: int = 6                  # in-flight decode futures

    def __post_init__(self) -> None:
        if self.comet_length < 2:
            raise ValueError("comet_length must be >= 2")
        if self.workers < 1:
            raise ValueError("workers must be >= 1")
        if self.prefetch < 1:
            raise ValueError("prefetch must be >= 1")


def list_images(directory: Path | str) -> list[Path]:
    """Return a case-insensitive, naturally sorted list of supported images."""
    d = Path(directory)
    if not d.is_dir():
        raise NotADirectoryError(d)
    return sorted(p for p in d.iterdir() if p.suffix.lower() in SUPPORTED_EXTS)


def _load_rgb_uint8(path: Path, expected_shape: tuple[int, int, int] | None) -> np.ndarray:
    """Decode an image to a uint8 HxWx3 array, scaling 16-bit TIFFs if needed."""
    with Image.open(path) as img:
        if img.mode in ("I;16", "I;16B", "I;16L"):
            # 16-bit single channel — rescale to 8-bit then broadcast to RGB
            arr = (np.asarray(img, dtype=np.uint32) >> 8).astype(np.uint8)
            frame = np.stack([arr, arr, arr], axis=-1)
        else:
            frame = np.asarray(img.convert("RGB"), dtype=np.uint8)
    if expected_shape is not None and frame.shape != expected_shape:
        raise ValueError(
            f"{path.name}: shape {frame.shape} differs from expected {expected_shape}"
        )
    return frame


def load_dark_frame(path: Path | str, expected_shape: tuple[int, int, int] | None = None) -> np.ndarray:
    """Load a single dark frame image, returned as uint8 HxWx3."""
    return _load_rgb_uint8(Path(path), expected_shape)


def _subtract_dark(frame: np.ndarray, dark: np.ndarray) -> np.ndarray:
    """Clip-subtract a dark frame from ``frame`` without underflow."""
    # np.subtract with dtype uint8 would wrap; use int16 intermediate then clip.
    diff = frame.astype(np.int16) - dark.astype(np.int16)
    np.clip(diff, 0, 255, out=diff)
    return diff.astype(np.uint8)


def _prefetch(
    paths: Iterable[Path],
    expected_shape: tuple[int, int, int],
    executor: ThreadPoolExecutor,
    prefetch_size: int,
    cancel: threading.Event | None,
) -> Iterator[np.ndarray]:
    """Yield decoded frames in submission order, keeping ``prefetch_size`` in flight."""
    path_iter = iter(paths)
    buffer: deque[Future[np.ndarray]] = deque()

    def submit_next() -> bool:
        try:
            p = next(path_iter)
        except StopIteration:
            return False
        buffer.append(executor.submit(_load_rgb_uint8, p, expected_shape))
        return True

    for _ in range(prefetch_size):
        if not submit_next():
            break

    while buffer:
        if cancel is not None and cancel.is_set():
            for fut in buffer:
                fut.cancel()
            raise RuntimeError("cancelled")
        yield buffer.popleft().result()
        submit_next()


def _init_stack(first_path: Path) -> tuple[np.ndarray, tuple[int, int, int]]:
    """Inspect the first image to size the accumulator."""
    with Image.open(first_path) as im:
        w, h = im.size
    shape = (h, w, 3)
    return np.zeros(shape, dtype=np.uint8), shape


def stack_frames(
    image_paths: list[Path],
    params: StackParams | None = None,
    progress: ProgressFn | None = None,
    cancel: threading.Event | None = None,
) -> Iterator[np.ndarray]:
    """Yield the progressive stack after each input frame.

    For ``StackMode.MAX`` this is the classic lighten composite; for
    ``StackMode.COMET`` the accumulator is faded before each new frame is
    merged, producing the comet-tail effect seen in modern startrail tools.

    The yielded array is reused across iterations for efficiency — if you need
    to keep frames around, copy with ``arr.copy()``.
    """
    if not image_paths:
        raise ValueError("no images provided")
    p = params or StackParams()
    stack_buf, shape = _init_stack(image_paths[0])

    if p.dark_frame is not None and p.dark_frame.shape != shape:
        raise ValueError(
            f"dark frame shape {p.dark_frame.shape} does not match images {shape}"
        )

    # Fade factor chosen so a frame's contribution drops to ~1/e across
    # ``comet_length`` frames.  Works well visually for typical 100–500 frame
    # sequences.
    fade = 1.0 - 1.0 / float(p.comet_length) if p.mode is StackMode.COMET else 1.0

    total = len(image_paths)
    with ThreadPoolExecutor(max_workers=p.workers) as executor:
        frames = _prefetch(image_paths, shape, executor, p.prefetch, cancel)
        for i, frame in enumerate(frames):
            if p.dark_frame is not None:
                frame = _subtract_dark(frame, p.dark_frame)
            if p.mode is StackMode.COMET and i > 0:
                # Fade the tail before merging — in-place to avoid allocation.
                np.multiply(stack_buf, fade, out=stack_buf, casting="unsafe")
            np.maximum(stack_buf, frame, out=stack_buf)
            if progress is not None:
                progress(i + 1, total)
            yield stack_buf


def stack(
    image_paths: list[Path],
    params: StackParams | None = None,
    progress: ProgressFn | None = None,
    cancel: threading.Event | None = None,
) -> np.ndarray:
    """Return the final stacked image (the last frame from :func:`stack_frames`)."""
    final: np.ndarray | None = None
    for frame in stack_frames(image_paths, params=params, progress=progress, cancel=cancel):
        final = frame
    assert final is not None  # guaranteed by the ValueError above when empty
    return final.copy()  # decouple caller from the reused buffer


def save_image(
    stacked: np.ndarray,
    output_path: Path | str,
    quality: int = 95,
    exif_source: Path | str | None = None,
) -> None:
    """Save a stacked array, optionally copying EXIF from a source image."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(stacked, mode="RGB")
    save_kwargs: dict[str, object] = {}
    if exif_source is not None:
        try:
            with Image.open(exif_source) as src:
                exif = src.info.get("exif")
                if exif:
                    save_kwargs["exif"] = exif
        except Exception:
            # EXIF passthrough is best-effort; never fail the stack over it.
            pass
    suffix = out.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        save_kwargs.setdefault("quality", quality)
        save_kwargs.setdefault("optimize", True)
        img.save(out, "JPEG", **save_kwargs)
    elif suffix in (".tif", ".tiff"):
        img.save(out, "TIFF", **save_kwargs)
    elif suffix == ".png":
        img.save(out, "PNG", **save_kwargs)
    else:
        # Let Pillow pick the format from the extension.
        img.save(out, **save_kwargs)
