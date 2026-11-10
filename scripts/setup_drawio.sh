#!/usr/bin/env bash
# Installs the draw.io desktop CLI (headless) used to export PNG/PDF exactly as draw.io renders them.
# Idempotent: does nothing if already present. Override location with DRAWIO_HOME.
set -e
DRAWIO_HOME="${DRAWIO_HOME:-/tmp/drawio-cli}"
VER="${DRAWIO_VERSION:-26.0.9}"
BIN="$DRAWIO_HOME/opt/drawio/drawio"
if [ -x "$BIN" ]; then echo "draw.io CLI ready: $BIN"; exit 0; fi
command -v xvfb-run >/dev/null 2>&1 || { (apt-get update -qq && apt-get install -y -qq xvfb) >/dev/null 2>&1 || true; }
command -v xvfb-run >/dev/null 2>&1 || { echo "xvfb-run missing and could not be installed"; exit 1; }
mkdir -p "$DRAWIO_HOME"
curl -sSL -o "$DRAWIO_HOME/drawio.deb" "https://github.com/jgraph/drawio-desktop/releases/download/v${VER}/drawio-amd64-${VER}.deb"
dpkg-deb -x "$DRAWIO_HOME/drawio.deb" "$DRAWIO_HOME"
rm -f "$DRAWIO_HOME/drawio.deb"
python3 -c "import PIL, pypdf" 2>/dev/null || pip install -q pillow pypdf --break-system-packages
echo "draw.io CLI ready: $BIN"
