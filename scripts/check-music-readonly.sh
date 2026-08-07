#!/usr/bin/env bash
set -euo pipefail

MOUNTPOINT="${1:-/mnt/music}"

if ! mountpoint -q "$MOUNTPOINT"; then
  echo "FOUT: $MOUNTPOINT is niet gemount."
  exit 20
fi

OPTS="$(findmnt -no OPTIONS --target "$MOUNTPOINT")"

case ",$OPTS," in
  *,ro,*) echo "OK: $MOUNTPOINT is read-only gemount." ;;
  *)
    echo "FOUT: $MOUNTPOINT is NIET read-only gemount."
    echo "Opties: $OPTS"
    exit 21
    ;;
esac

if [ -w "$MOUNTPOINT" ]; then
  echo "FOUT: gebruiker kan toch schrijven naar $MOUNTPOINT."
  exit 22
fi

echo "OK: streamer heeft geen schrijfrechten op de muziekopslag."
