# NRG Radio 1.1

NRG Radio is een headless AI-radiostreamer voor Debian onder Proxmox.

## Architectuur

- **Debian VM 1 – Top40Archiver:** read/write toegang tot de gedeelde USB-muziekschijf.
- **Debian VM 2 – NRG Radio:** uitsluitend read-only toegang tot dezelfde muziek.
- De muziekbibliotheek staat op `/mnt/music`.
- NRG Radio schrijft database, geschiedenis, cache en TTS alleen naar de lokale VM-schijf.
- Liquidsoap stuurt de stream naar Caster.fm als 96 kbps MP3.

## Functies

- lokale muziek scannen en indexeren;
- SQLite muziekbibliotheek en speelgeschiedenis;
- metadata uit MP3/FLAC/M4A/Ogg/Opus;
- artiest-repeat standaard 8 uur;
- track-repeat standaard 72 uur;
- dagdeelafhankelijke muziekselectie;
- uitgesloten genres;
- lokale AI-presentator via Ollama;
- Nederlandse spraak via Edge TTS;
- automatische fallback wanneer Ollama tijdelijk niet beschikbaar is;
- systemd-service en automatische herstart;
- automatische bibliotheekscan iedere 10 minuten;
- harde controle dat `/mnt/music` read-only is.

## Caster.fm

Voorbereid voor:

```text
Host:       morcast.caster.fm
Port:       17615
Username:   source
Mountpoint: /aQIBb
Bitrate:    96 kbps MP3
```

Het broadcast-wachtwoord staat **niet** in GitHub en wordt tijdens installatie lokaal gevraagd.

## Installeren

Zorg eerst dat de gedeelde muziekopslag op de streamer beschikbaar is als read-only mount:

```text
192.168.1.103:/srv/music /mnt/music nfs ro,_netdev,nofail,x-systemd.automount 0 0
```

Daarna kan de complete installer vanaf GitHub worden gestart met:

```bash
curl -fsSL https://raw.githubusercontent.com/Techraym/Radio-Streamer/main/bootstrap.sh | sudo bash
```

De bootstrap:
1. downloadt de benodigde Debian-pakketten;
2. installeert indien nodig Ollama;
3. controleert Debian, internet, opslag en RAM;
4. controleert dat `/mnt/music` werkelijk read-only is;
5. stopt als de streamer naar de muziekbron kan schrijven;
6. installeert NRG Radio;
7. controleert Python en Liquidsoap.

Ollama niet automatisch installeren:

```bash
curl -fsSL https://raw.githubusercontent.com/Techraym/Radio-Streamer/main/bootstrap.sh | sudo NRG_INSTALL_OLLAMA=0 bash
```

## Beheer

```bash
systemctl status nrg-radio --no-pager -l
journalctl -u nrg-radio -f
systemctl status nrg-radio-scan.timer
```

Handmatig scannen:

```bash
sudo systemctl start nrg-radio-scan.service
```
