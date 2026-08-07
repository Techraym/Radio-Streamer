#!/usr/bin/env bash
set -euo pipefail

REPO="Techraym/Radio-Streamer"
BRANCH="${NRG_BRANCH:-main}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

[ "$(id -u)" -eq 0 ] || { echo "FOUT: gebruik sudo"; exit 1; }

if ! command -v curl >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y curl ca-certificates
fi

URL="https://github.com/${REPO}/archive/refs/heads/${BRANCH}.tar.gz"
echo "NRG Radio downloaden van $URL"
curl -fsSL "$URL" -o "$WORKDIR/radio-streamer.tar.gz"
tar -xzf "$WORKDIR/radio-streamer.tar.gz" -C "$WORKDIR"

SRC="$(find "$WORKDIR" -mindepth 1 -maxdepth 1 -type d -name 'Radio-Streamer-*' | head -n1)"
[ -n "$SRC" ] || { echo "FOUT: repository niet gevonden na uitpakken"; exit 10; }

bash "$SRC/install/dependencies.sh"

if ! bash "$SRC/install/preflight.sh"; then
  echo
  echo "Installatie gestopt. /mnt/music moet actief en read-only gemount zijn."
  exit 11
fi

cd "$SRC"
bash ./install.sh
