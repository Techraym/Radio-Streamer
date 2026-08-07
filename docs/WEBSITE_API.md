# NRG Radio 1.2 Website API

De API draait standaard op poort `8042`. Bind-adres en poort staan in `/etc/nrg-radio/config.json`.

## Endpoints

- `GET /health`
- `GET /api/status`
- `GET /api/now-playing`
- `GET /api/history?limit=20`
- `GET /api/cover/current`
- `GET /api/cover/{track_id}`

## Albumhoezen

De cover wordt uitsluitend uit de embedded ID3 `APIC`-tag van de MP3 gelezen. Bij meerdere afbeeldingen wordt eerst `Front Cover` (picture type 3) gebruikt.

Er worden geen losse `cover.jpg`-bestanden gezocht en er wordt geen externe coverprovider gebruikt. Als de MP3 geen APIC-afbeelding bevat, gebruikt de API de NRG Radio fallback-afbeelding.

De bron onder `/mnt/music` blijft read-only. Een gevonden afbeelding mag alleen lokaal worden gecachet in `/var/lib/nrg-radio/cover-cache`.

## Website

Gebruik voor `raysnijder.nl` bij voorkeur een HTTPS reverse proxy naar poort 8042. CORS staat standaard open voor:

```text
https://raysnijder.nl
https://www.raysnijder.nl
```

Voorbeeld `now-playing`:

```json
{
  "station": "NRG Radio",
  "playing": true,
  "kind": "music",
  "track_id": 123,
  "artist": "Artiest",
  "title": "Titel",
  "album": "Album",
  "year": 1999,
  "cover_url": "/api/cover/current"
}
```
