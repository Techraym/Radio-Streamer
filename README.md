# NRG Radio 1.2.0

Headless AI-radiostreamer voor Debian onder Proxmox.

## Architectuur

- Debian VM 1: Top40Archiver met read/write toegang tot de gedeelde USB-muziekschijf.
- Debian VM 2: NRG Radio met uitsluitend read-only toegang tot dezelfde muziek.
- Muziekbron op de streamer: `/mnt/music`.
- Database, geschiedenis, AI/TTS-audio en cover-cache staan lokaal op de streamer-VM.
- Liquidsoap stuurt 96 kbps MP3 naar Caster.fm.

## Functies

- lokale muziekbibliotheek scannen en indexeren;
- SQLite catalogus en speelgeschiedenis;
- artiest-repeat standaard 8 uur;
- track-repeat standaard 72 uur;
- dagdeelafhankelijke muziekselectie;
- uitgesloten genres;
- lokale AI-presentator via Ollama;
- Nederlandse Edge TTS;
- fallback-presentatie als Ollama niet beschikbaar is;
- automatische bibliotheekscan iedere 10 minuten;
- website/API-service op poort 8042;
- now-playing en historie via JSON;
- albumhoes uit de embedded ID3/APIC-tag van de MP3;
- lokale cover-cache zonder wijzigingen aan `/mnt/music`;
- CORS voor `raysnijder.nl`;
- healthcheck en smoke-test;
- systemd-services met automatische herstart.

## Albumhoezen

NRG Radio leest de albumhoes rechtstreeks uit het `APIC`-frame van de ID3-tag van de MP3. Als meerdere afbeeldingen aanwezig zijn, krijgt `Front Cover` (picture type 3) voorrang.

NRG Radio schrijft nooit tags of covers terug naar de muziekbron. Alleen een cachekopie wordt lokaal opgeslagen in:

```text
/var/lib/nrg-radio/cover-cache
```

Als een MP3 geen embedded albumhoes heeft, retourneert de API een NRG Radio fallback-afbeelding.

## Caster.fm

Voorbereid voor:

```text
Host:       morcast.caster.fm
Port:       17615
Username:   source
Mountpoint: /aQIBb
Bitrate:    96 kbps MP3
```

Het broadcast-wachtwoord staat niet in GitHub en wordt tijdens installatie lokaal gevraagd.

## Installatie

De muziekopslag moet **voor de installatie** al actief en read-only gemount zijn op `/mnt/music`. Voorbeeld:

```text
192.168.1.103:/srv/music /mnt/music nfs ro,_netdev,nofail,x-systemd.automount 0 0
```

Installeer daarna rechtstreeks vanaf GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/Techraym/Radio-Streamer/main/bootstrap.sh | sudo bash
```

De bootstrap downloadt vereiste Debian-pakketten, installeert Ollama en `llama3.2:1b` indien nodig, controleert de read-only opslag en installeert de applicatie.

## Services

```bash
systemctl status nrg-radio --no-pager -l
systemctl status nrg-radio-api --no-pager -l
systemctl status nrg-radio-scan.timer --no-pager -l
```

## Controle

```bash
sudo /opt/nrg-radio/scripts/healthcheck.sh
sudo /opt/nrg-radio/scripts/smoke-test.sh
```

## API

```bash
curl http://127.0.0.1:8042/health
curl http://127.0.0.1:8042/api/status
curl http://127.0.0.1:8042/api/now-playing
curl http://127.0.0.1:8042/api/history
```

Zie ook `docs/WEBSITE_API.md`.
