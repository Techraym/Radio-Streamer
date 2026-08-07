#!/usr/bin/env bash
set -u
fail=0
warn=0
ok(){ echo "OK   $*"; }
bad(){ echo "FOUT $*"; fail=$((fail+1)); }
note(){ echo "WAARSCHUWING $*"; warn=$((warn+1)); }
echo "=== NRG Radio 1.2.0 healthcheck ==="
[ -f /opt/nrg-radio/VERSION ] && ok "app geïnstalleerd: $(cat /opt/nrg-radio/VERSION)" || bad "/opt/nrg-radio/VERSION ontbreekt"
[ -f /etc/nrg-radio/config.json ] && ok "config aanwezig" || bad "config ontbreekt"
[ -f /etc/nrg-radio/nrg-radio.liq ] && ok "Liquidsoap-config aanwezig" || bad "Liquidsoap-config ontbreekt"
/opt/nrg-radio/scripts/check-music-readonly.sh /mnt/music >/tmp/nrg-radio-storage-check.$$ 2>&1
rc=$?
cat /tmp/nrg-radio-storage-check.$$
rm -f /tmp/nrg-radio-storage-check.$$
[ "$rc" -eq 0 ] || fail=$((fail+1))
if systemctl is-active --quiet nrg-radio; then ok "nrg-radio.service actief"; else bad "nrg-radio.service niet actief"; fi
if systemctl is-active --quiet nrg-radio-api; then
  if curl -fsS --max-time 3 http://127.0.0.1:8042/health >/dev/null 2>&1; then ok "nrg-radio-api.service actief en API bereikbaar"; else bad "nrg-radio-api.service actief maar API niet bereikbaar"; fi
else
  bad "nrg-radio-api.service niet actief"
fi
if systemctl is-enabled --quiet nrg-radio-scan.timer 2>/dev/null; then ok "bibliotheekscan-timer ingeschakeld"; else note "nrg-radio-scan.timer niet ingeschakeld"; fi
if command -v ollama >/dev/null 2>&1; then
  if curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then ok "Ollama API bereikbaar"; else note "Ollama API niet bereikbaar; radio kan met fallback blijven draaien"; fi
else
  note "Ollama niet geïnstalleerd"
fi
if [ -f /var/lib/nrg-radio/nrg-radio.db ]; then count="$(sqlite3 /var/lib/nrg-radio/nrg-radio.db 'select count(*) from tracks where enabled=1;' 2>/dev/null || echo '?')"; ok "muziekdatabase aanwezig; actieve tracks: $count"; else note "muziekdatabase bestaat nog niet"; fi
echo "Resultaat: $fail fout(en), $warn waarschuwing(en)"
[ "$fail" -eq 0 ]
