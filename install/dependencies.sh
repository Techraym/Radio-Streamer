#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "FOUT: gebruik sudo"; exit 1; }
echo "=== NRG Radio 1.2 afhankelijkheden ==="
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl ffmpeg git liquidsoap nfs-common python3 python3-pip python3-venv sqlite3 unzip util-linux
for cmd in curl ffmpeg git liquidsoap python3 findmnt mountpoint; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "FOUT: $cmd ontbreekt"; exit 20; }
  echo "OK: $cmd"
done
if [ "${NRG_INSTALL_OLLAMA:-1}" = "1" ]; then
  if command -v ollama >/dev/null 2>&1; then
    echo "OK: Ollama is al geïnstalleerd"
  else
    echo "Ollama downloaden en installeren..."
    tmp="$(mktemp)"
    trap 'rm -f "$tmp"' EXIT
    curl -fsSL https://ollama.com/install.sh -o "$tmp"
    /bin/sh "$tmp"
    rm -f "$tmp"
    trap - EXIT
  fi
  echo "=== Ollama service/model controleren ==="
  systemctl enable --now ollama >/dev/null 2>&1 || true
  OLLAMA_MODEL="${NRG_OLLAMA_MODEL:-llama3.2:1b}"
  for _ in 1 2 3 4 5; do
    if ollama list >/dev/null 2>&1; then break; fi
    sleep 2
  done
  if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fxq "$OLLAMA_MODEL"; then
    echo "OK: Ollama-model $OLLAMA_MODEL is aanwezig"
  else
    echo "Ollama-model $OLLAMA_MODEL downloaden..."
    ollama pull "$OLLAMA_MODEL"
  fi
else
  echo "Ollama overgeslagen via NRG_INSTALL_OLLAMA=0"
fi
echo "=== Versies ==="
python3 --version
ffmpeg -version | head -n1
liquidsoap --version | head -n1
command -v ollama >/dev/null 2>&1 && ollama --version || true
