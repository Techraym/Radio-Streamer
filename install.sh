#!/usr/bin/env bash
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "FOUT: gebruik sudo ./install.sh"
  exit 1
fi

SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="/opt/nrg-radio"
ETC_DIR="/etc/nrg-radio"
DATA_DIR="/var/lib/nrg-radio"
MUSIC_DIR="/mnt/music"

CASTER_HOST="morcast.caster.fm"
CASTER_PORT="17615"
CASTER_USER="source"
CASTER_MOUNT="/aQIBb"

echo "================================================="
echo " NRG Radio 1.1 - Proxmox / Debian streamer"
echo "================================================="
echo
echo "Deze VM mag de gedeelde muziekschijf uitsluitend READ-ONLY gebruiken."
echo "Verwachte mountpoint: $MUSIC_DIR"
echo

read -rsp "Caster.fm broadcast-wachtwoord: " CASTER_PASSWORD
echo
[ -n "$CASTER_PASSWORD" ] || { echo "FOUT: leeg wachtwoord."; exit 1; }

apt update
DEBIAN_FRONTEND=noninteractive apt install -y \
  liquidsoap ffmpeg python3 python3-venv python3-pip ca-certificates \
  nfs-common util-linux

if ! id nrg-radio >/dev/null 2>&1; then
  useradd --system --home "$DATA_DIR" --create-home --shell /usr/sbin/nologin nrg-radio
fi

mkdir -p "$APP_DIR" "$ETC_DIR" "$DATA_DIR/generated/announcements" "$MUSIC_DIR"

rm -rf "$APP_DIR/app" "$APP_DIR/scripts"
cp -a "$SRC_DIR/app" "$APP_DIR/"
cp -a "$SRC_DIR/scripts" "$APP_DIR/"
chmod 755 "$APP_DIR"/scripts/*.sh
cp "$SRC_DIR/requirements.txt" "$APP_DIR/"
cp "$SRC_DIR/VERSION" "$APP_DIR/"

cp "$SRC_DIR/config/config.example.json" "$ETC_DIR/config.json"
cp "$SRC_DIR/systemd/nrg-radio.service" /etc/systemd/system/
cp "$SRC_DIR/systemd/nrg-radio-scan.service" /etc/systemd/system/
cp "$SRC_DIR/systemd/nrg-radio-scan.timer" /etc/systemd/system/

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install --upgrade pip
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

mkdir -p "$APP_DIR/assets"
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i anullsrc=r=44100:cl=stereo -t 1 \
  -codec:a libmp3lame -b:a 96k "$APP_DIR/assets/emergency.mp3"

ESCAPED_PASSWORD="$(printf '%s' "$CASTER_PASSWORD" | sed 's/[\\&/]/\\&/g; s/"/\\"/g')"

sed \
  -e "s/__CASTER_HOST__/$CASTER_HOST/g" \
  -e "s/__CASTER_PORT__/$CASTER_PORT/g" \
  -e "s/__CASTER_USER__/$CASTER_USER/g" \
  -e "s/__CASTER_MOUNT__/${CASTER_MOUNT//\//\\/}/g" \
  -e "s/__CASTER_PASSWORD__/$ESCAPED_PASSWORD/g" \
  "$SRC_DIR/liquidsoap/nrg-radio.liq.template" > "$ETC_DIR/nrg-radio.liq"

cat > "$ETC_DIR/caster.env" <<EOF
CASTER_HOST=$CASTER_HOST
CASTER_PORT=$CASTER_PORT
CASTER_USER=$CASTER_USER
CASTER_MOUNT=$CASTER_MOUNT
CASTER_PASSWORD=$CASTER_PASSWORD
EOF

unset CASTER_PASSWORD ESCAPED_PASSWORD

chown -R root:nrg-radio "$APP_DIR" "$ETC_DIR"
chmod 750 "$ETC_DIR"
chmod 640 "$ETC_DIR/config.json" "$ETC_DIR/nrg-radio.liq"
chmod 600 "$ETC_DIR/caster.env"
chown -R nrg-radio:nrg-radio "$DATA_DIR"

"$APP_DIR/venv/bin/python" -m py_compile "$APP_DIR"/app/*.py
liquidsoap --check "$ETC_DIR/nrg-radio.liq"

systemctl daemon-reload
systemctl enable nrg-radio.service nrg-radio-scan.timer

echo
echo "================================================="
echo " Installatie gereed"
echo "================================================="
echo
echo "BELANGRIJK: configureer nu eerst /mnt/music als read-only NFS-mount."
echo
echo "Voorbeeld /etc/fstab op de streamer:"
echo "  STORAGE-IP:/srv/music /mnt/music nfs ro,_netdev,nofail,x-systemd.automount 0 0"
echo
echo "Daarna:"
echo "  systemctl daemon-reload"
echo "  mount /mnt/music"
echo "  /opt/nrg-radio/scripts/check-music-readonly.sh /mnt/music"
echo "  systemctl start nrg-radio-scan.service"
echo "  systemctl start nrg-radio"
echo
echo "Status:"
echo "  systemctl status nrg-radio --no-pager -l"
echo "  journalctl -u nrg-radio -f"
