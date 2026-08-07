#!/usr/bin/env bash
set -u
fail=0
warn=0
ok(){ echo "OK   $*"; }
bad(){ echo "FOUT $*"; fail=$((fail+1)); }
note(){ echo "WAARSCHUWING $*"; warn=$((warn+1)); }
PY="/opt/nrg-radio/venv/bin/python"
APP="/opt/nrg-radio/app"
CFG="/etc/nrg-radio/config.json"
echo "=== NRG Radio 1.2 smoke test ==="
if /opt/nrg-radio/scripts/check-music-readonly.sh /mnt/music; then :; else fail=$((fail+1)); fi
if "$PY" -m py_compile "$APP"/*.py; then ok "Python-code compileert"; else bad "Python compilefout"; fi
if liquidsoap --check /etc/nrg-radio/nrg-radio.liq >/tmp/nrg-liquidsoap-check.$$ 2>&1; then ok "Liquidsoap-config geldig"; else cat /tmp/nrg-liquidsoap-check.$$; bad "Liquidsoap-config ongeldig"; fi
rm -f /tmp/nrg-liquidsoap-check.$$
if NRG_CONFIG="$CFG" "$PY" "$APP/scan_music.py"; then ok "muziekscan uitgevoerd"; else bad "muziekscan mislukt"; fi
TRACK="$(cd "$APP" && NRG_CONFIG="$CFG" "$PY" - <<'PY'
from music_selector import pick_track
t=pick_track()
print(t["path"] if t else "")
PY
)"
if [ -n "$TRACK" ] && [ -r "$TRACK" ]; then
  ok "trackselectie: $TRACK"
  if ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$TRACK" >/dev/null 2>&1; then ok "FFmpeg kan geselecteerde track lezen"; else bad "FFmpeg kan geselecteerde track niet lezen"; fi
else
  bad "geen leesbare track geselecteerd"
fi
if command -v ollama >/dev/null 2>&1 && curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then ok "Ollama API bereikbaar"; else note "Ollama niet bereikbaar; fallback-presentatie blijft beschikbaar"; fi
if systemctl is-active --quiet nrg-radio-api 2>/dev/null; then
  if curl -fsS --max-time 3 http://127.0.0.1:8042/health >/dev/null 2>&1; then ok "NRG Radio API bereikbaar"; else bad "API-service actief maar /health reageert niet"; fi
else
  note "API-service is nog niet gestart"
fi
echo "Resultaat: $fail fout(en), $warn waarschuwing(en)"
[ "$fail" -eq 0 ]
