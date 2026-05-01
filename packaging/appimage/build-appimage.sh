#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Build a portable Linux .AppImage using python-appimage.  The resulting
# binary runs on any glibc >= 2.28 system (Ubuntu 20.04+, Debian 11+, RHEL 9+).
#
# Requires: python3, pip, python-appimage, libfuse2.  See BUILDING.md.
set -euo pipefail

cd "$(dirname "$0")/../.."                     # repo root
REPO_ROOT="$PWD"
VERSION="$(python3 -c 'from astrotrails._version import __version__; print(__version__)')"
OUTDIR="$REPO_ROOT/packaging/appimage"
RECIPE="$OUTDIR/recipe"

PY_VERSION="${ASTROTRAILS_APPIMAGE_PY:-3.11}"

echo ">> building astrotrails $VERSION AppImage (Python $PY_VERSION)"

# Wipe any previous recipe
rm -rf "$RECIPE"
mkdir -p "$RECIPE"

# ---------------- entry point ------------------------------------------------
cat > "$RECIPE/entrypoint.sh" <<'EOF'
#!/bin/sh
# Route between CLI and GUI.  The first argument "--cli" (if present) switches
# us to the command-line interface; anything else drops into the GUI.
APPDIR="$(dirname "$(readlink -f "$0")")"
export PYTHONPATH="$APPDIR/opt/astrotrails:${PYTHONPATH:-}"
PYBIN="$APPDIR/opt/python*/bin/python*"
PY="$(ls $PYBIN 2>/dev/null | head -n1)"
[ -z "$PY" ] && PY="python3"

if [ "${1:-}" = "--cli" ]; then
    shift
    exec "$PY" -m astrotrails "$@"
else
    exec "$PY" -m astrotrails.gui "$@"
fi
EOF
chmod +x "$RECIPE/entrypoint.sh"

# ---------------- python-appimage recipe -------------------------------------
cat > "$RECIPE/requirements.txt" <<EOF
$REPO_ROOT[gui]
EOF

cat > "$RECIPE/astrotrails.desktop" <<'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=astrotrails
GenericName=Startrails Generator
Comment=Stack night-sky photos into startrails and timelapse videos
Exec=AppRun
Icon=astrotrails
Terminal=false
Categories=Graphics;Photography;Science;
EOF

cp "$REPO_ROOT/packaging/assets/astrotrails.png" "$RECIPE/astrotrails.png"

# ---------------- build ------------------------------------------------------
# python-appimage's "manylinux" build: give it a requirements file and an
# entrypoint, and it produces a self-contained .AppImage.
cd "$OUTDIR"
rm -f astrotrails-*.AppImage

python3 -m python_appimage build app \
    --python-version "$PY_VERSION" \
    --name "astrotrails-$VERSION-x86_64" \
    "$RECIPE"

mv "astrotrails-$VERSION-x86_64-x86_64.AppImage" \
   "astrotrails-$VERSION-x86_64.AppImage" 2>/dev/null || true

echo
echo ">> produced: $(ls -1 "$OUTDIR"/astrotrails-*.AppImage)"
