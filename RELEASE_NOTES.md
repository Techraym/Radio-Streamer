# NRG Radio 1.2.0 — Release Notes

Releaseversie voor de headless Debian streamer-VM onder Proxmox.

Belangrijkste toevoegingen ten opzichte van 1.1:

- website/API-service op poort 8042;
- now-playing, status en speelgeschiedenis;
- albumhoes rechtstreeks uit MP3 ID3/APIC;
- lokale cover-cache;
- healthcheck en smoke-test;
- API systemd-service;
- read-only bescherming van `/mnt/music`;
- automatische muziekscan;
- installer en dependency-downloader;
- Ollama + `llama3.2:1b` installatiecontrole.

De Caster.fm broadcast credentials worden niet in de repository opgeslagen.
