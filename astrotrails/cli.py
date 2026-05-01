# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line interface for astrotrails."""
from __future__ import annotations

import argparse
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path

from PIL import Image
from tqdm import tqdm

from . import __version__
from .core import (
    StackMode,
    StackParams,
    list_images,
    load_dark_frame,
    save_image,
    stack_frames,
)
from .video import FFmpegNotFound, FFmpegPipeWriter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="astrotrails",
        description="Generate startrails images and timelapse videos from a "
                    "directory of night-sky photographs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("input", type=Path, help="directory containing input images")
    p.add_argument("-o", "--output", type=Path, default=None,
                   help="output directory (default: input directory)")
    p.add_argument("--mode", choices=[m.value for m in StackMode],
                   default=StackMode.MAX.value,
                   help="stacking algorithm")
    p.add_argument("--comet-length", type=int, default=50,
                   help="tail length in frames (comet mode only)")
    p.add_argument("--dark-frame", type=Path, default=None,
                   help="path to a dark frame to subtract from every input")
    p.add_argument("--image", default="Stacked.jpg",
                   help="output image filename")
    p.add_argument("--video", default="timelapse.mp4",
                   help="output video filename")
    p.add_argument("--fps", type=int, default=25, help="timelapse frames per second")
    p.add_argument("--crf", type=int, default=18,
                   help="libx264 quality (lower = better, 18 is visually lossless)")
    p.add_argument("--no-image", action="store_true",
                   help="skip the stacked-image output")
    p.add_argument("--no-video", action="store_true",
                   help="skip the timelapse-video output")
    p.add_argument("--workers", type=int, default=4,
                   help="image decoder thread pool size")
    p.add_argument("-q", "--quiet", action="store_true",
                   help="suppress the progress bar")
    p.add_argument("-V", "--version", action="version",
                   version=f"astrotrails {__version__}")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.no_image and args.no_video:
        print("error: --no-image and --no-video together leave nothing to do",
              file=sys.stderr)
        return 2
    if args.fps <= 0:
        print("error: --fps must be positive", file=sys.stderr)
        return 2

    input_dir: Path = args.input
    output_dir: Path = args.output or input_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        images = list_images(input_dir)
    except NotADirectoryError:
        print(f"error: {input_dir} is not a directory", file=sys.stderr)
        return 2
    if not images:
        print(f"error: no supported images in {input_dir}", file=sys.stderr)
        return 2

    dark = load_dark_frame(args.dark_frame) if args.dark_frame else None

    params = StackParams(
        mode=StackMode(args.mode),
        comet_length=args.comet_length,
        dark_frame=dark,
        workers=max(1, args.workers),
    )

    # Peek at the first image to size the video writer.
    with Image.open(images[0]) as im:
        width, height = im.size

    print(f"astrotrails {__version__}: {len(images)} images, mode={params.mode.value}")
    cancel = threading.Event()

    # Progress bar shared by the stacking loop and video writer.
    pbar = None if args.quiet else tqdm(total=len(images), unit="frame", desc="Stacking")

    def on_progress(cur: int, tot: int) -> None:
        if pbar is not None:
            pbar.update(cur - pbar.n)

    start = time.perf_counter()
    image_out = output_dir / args.image
    video_out = output_dir / args.video

    try:
        if args.no_video:
            # Image-only path — consume the generator and keep the last frame.
            last = None
            for frame in stack_frames(images, params=params, progress=on_progress, cancel=cancel):
                last = frame
            assert last is not None
            save_image(last, image_out, exif_source=images[0])
            print(f"wrote {image_out}")
        else:
            # Stream frames through ffmpeg; optionally save the last one as the image.
            try:
                writer_ctx = FFmpegPipeWriter(video_out, width, height,
                                              fps=args.fps, crf=args.crf)
            except FFmpegNotFound as e:
                print(f"error: {e}", file=sys.stderr)
                return 3

            last = None
            with writer_ctx as writer:
                for frame in stack_frames(images, params=params,
                                          progress=on_progress, cancel=cancel):
                    writer.write_frame(frame)
                    last = frame
            print(f"wrote {video_out}")
            if not args.no_image and last is not None:
                save_image(last, image_out, exif_source=images[0])
                print(f"wrote {image_out}")

    except KeyboardInterrupt:
        cancel.set()
        print("\ninterrupted", file=sys.stderr)
        return 130
    finally:
        if pbar is not None:
            pbar.close()

    elapsed = time.perf_counter() - start
    print(f"done in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
