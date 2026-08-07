#!/usr/bin/env bash
set -u
MUSIC_MOUNT="${NRG_MUSIC_MOUNT:-/mnt/music}"
MIN_RAM_MB="${NRG_MIN_RAM_MB:-1500}"
MIN_DISK_MB="${NRG_MIN_DISK_MB:-4096}"
fail=0
warn=0
ok(){ echo "OK   $*"; }
bad(){ echo "FOUT $*"; fail=$((fail+1)); }
note(){ echo "WAARSCHUWING $*"; warn=$((warn+1)); }
echo "=== NRG Radio 1.2 installatiecontrole ==="
if [ "$(id -u)" -eq 0 ]; then ok "root/sudo"; else bad "voer uit met sudo"; fi
if [ -r /etc/os-release ]; then . /etc/os-release; [ "${ID:-}" = "debian" ] && ok "${PRETTY_NAME:-Debian}" || bad "Debian vereist; gevonden: ${PRETTY_NAME:-onbekend}"; else bad "/etc/os-release ontbreekt"; fi
case "$(dpkg --print-architecture 2>/dev/null || uname -m)" in amd64|arm64|x86_64|aarch64) ok "architectuur ondersteund" ;; *) note "architectuur niet standaard getest" ;; esac
getent hosts github.com >/dev/null 2>&1 && ok "internet/DNS" || bad "github.com niet bereikbaar"
ram_mb="$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo 2>/dev/null || echo 0)"
[ "$ram_mb" -ge "$MIN_RAM_MB" ] && ok "RAM ${ram_mb} MB" || note "RAM ${ram_mb} MB; aanbevolen minimaal ${MIN_RAM_MB} MB"
disk_mb="$(df -Pm / | awk 'NR==2 {print $4}')"
[ "${disk_mb:-0}" -ge "$MIN_DISK_MB" ] && ok "vrije lokale opslag ${disk_mb} MB" || bad "te weinig lokale opslag"
if mountpoint -q "$MUSIC_MOUNT" 2>/dev/null; then
  ok "$MUSIC_MOUNT is gemount"
  opts="$(findmnt -no OPTIONS --target "$MUSIC_MOUNT" 2>/dev/null || true)"
  case ",$opts," in *,ro,*) ok "$MUSIC_MOUNT is read-only" ;; *) bad "$MUSIC_MOUNT is NIET read-only: $opts" ;; esac
else
  bad "$MUSIC_MOUNT is niet gemount"
fi
if [ -w "$MUSIC_MOUNT" ] 2>/dev/null; then bad "streamer kan schrijven naar $MUSIC_MOUNT"; else ok "streamer heeft geen schrijfrechten op muziekopslag"; fi
echo "Resultaat: $fail fout(en), $warn waarschuwing(en)"
[ "$fail" -eq 0 ]
