# SPDX-License-Identifier: GPL-3.0-or-later
# CLI-only Docker image.  Running the PyQt6 GUI inside a container needs X11
# forwarding and is outside the scope of this image — install the .deb or
# .AppImage instead for the desktop experience.

# ---- build stage: produce a wheel -------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build
RUN pip install --no-cache-dir --upgrade pip build

COPY pyproject.toml README.md LICENSE.txt CHANGELOG.md MANIFEST.in ./
COPY astrotrails ./astrotrails
RUN python -m build --wheel

# ---- runtime stage: slim + system ffmpeg ------------------------------------
FROM python:3.12-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl \
 && rm /tmp/*.whl

# astrotrails will detect /usr/bin/ffmpeg and skip the imageio-ffmpeg fallback.
WORKDIR /work
VOLUME ["/work"]

ENTRYPOINT ["astrotrails"]
CMD ["--help"]

LABEL org.opencontainers.image.title="astrotrails"
LABEL org.opencontainers.image.description="Generate startrails images and timelapse videos."
LABEL org.opencontainers.image.source="https://github.com/theogatsios/astrotrails"
LABEL org.opencontainers.image.licenses="GPL-3.0-or-later"
