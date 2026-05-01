# astrotrails: generate startrails images and timelapse videos.
# Copyright (C) 2026 Theodoros Gatsios
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""astrotrails — stack night-sky photographs into startrails and timelapses."""

from ._version import __version__
from .core import (
    StackMode,
    list_images,
    load_dark_frame,
    save_image,
    stack,
    stack_frames,
)
from .video import FFmpegPipeWriter, find_ffmpeg

__all__ = [
    "__version__",
    "StackMode",
    "FFmpegPipeWriter",
    "find_ffmpeg",
    "list_images",
    "load_dark_frame",
    "save_image",
    "stack",
    "stack_frames",
]
