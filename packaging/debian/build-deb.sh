#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Build a Debian/Ubuntu .deb using fpm.
#
# Strategy: pip-install astrotrails (plus GUI + ffmpeg) into a staging root
# at /opt/astrotrails, drop thin wrapper scripts in /usr/bin, and ship a
# .desktop file + icon for the application menu.
#
# Requires: python3, pip, ruby, fpm.  See BUILDING.md for setup.
set -euo pipefail

cd "$(dirname "$0")/../.."                     # repo root
REPO_ROOT="$PWD"
VERSION="$(python3 -c 'from astrotrails._version import __version__; print(__version__)')"
ARCH="$(dpkg --print-architecture 2>/dev/null || echo amd64)"
STAGE="$(mktemp -d)"
OUTDIR="$REPO_ROOT/packaging/debian"

echo ">> building astrotrails $VERSION for $ARCH"
echo ">> staging root: $STAGE"

# -------- 1. install the package into /opt/astrotrails inside the stage ------
mkdir -p "$STAGE/opt/astrotrails"
python3 -m pip install --no-compile --no-warn-script-location \
    --target "$STAGE/opt/astrotrails" \
    "$REPO_ROOT"[gui]

# -------- 2. thin wrappers in /usr/bin --------------------------------------
mkdir -p "$STAGE/usr/bin"
cat > "$STAGE/usr/bin/astrotrails" <<'EOF'
#!/bin/sh
exec /usr/bin/env PYTHONPATH=/opt/astrotrails python3 -m astrotrails "$@"
EOF
cat > "$STAGE/usr/bin/astrotrails-gui" <<'EOF'
#!/bin/sh
exec /usr/bin/env PYTHONPATH=/opt/astrotrails python3 -m astrotrails.gui "$@"
EOF
chmod 0755 "$STAGE/usr/bin/astrotrails" "$STAGE/usr/bin/astrotrails-gui"

# -------- 3. desktop entry + icon -------------------------------------------
mkdir -p "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps"
cp "$REPO_ROOT/packaging/debian/astrotrails.desktop" \
   "$STAGE/usr/share/applications/astrotrails.desktop"
cp "$REPO_ROOT/packaging/assets/astrotrails.png" \
   "$STAGE/usr/share/icons/hicolor/256x256/apps/astrotrails.png"

# -------- 4. license, copyright ---------------------------------------------
mkdir -p "$STAGE/usr/share/doc/astrotrails"
cp "$REPO_ROOT/LICENSE.txt"    "$STAGE/usr/share/doc/astrotrails/copyright"
cp "$REPO_ROOT/CHANGELOG.md"   "$STAGE/usr/share/doc/astrotrails/changelog"
gzip -9n "$STAGE/usr/share/doc/astrotrails/changelog"

# -------- 5. bake the .deb with fpm -----------------------------------------
cd "$OUTDIR"
rm -f astrotrails_*.deb

fpm -s dir -t deb \
    -n astrotrails \
    -v "$VERSION" \
    --architecture "$ARCH" \
    --license "GPL-3.0-or-later" \
    --maintainer "Theo Gatsios <theogat@protonmail.com>" \
    --url "https://github.com/theogatsios/astrotrails" \
    --description "Stack night-sky photos into startrails images and timelapse videos" \
    --category "graphics" \
    --depends "python3 (>= 3.9)" \
    --depends "python3-pyqt6" \
    --depends "ffmpeg" \
    --deb-no-default-config-files \
    --chdir "$STAGE" \
    opt usr

echo
echo ">> produced: $(ls -1 "$OUTDIR"/astrotrails_*.deb)"
rm -rf "$STAGE"
