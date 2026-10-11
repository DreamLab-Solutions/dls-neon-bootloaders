# DLS Neon GRUB

Tema GNU GRUB ispirato al concept DreamLab: portale spaziale, teal, viola e
giallo **#D9FF00**. Il menu è nativo e navigabile da tastiera; le voci reali
rimangono quelle generate dalla distribuzione. Versione **0.1.0 — anteprima privata**.

![Concept approvato](assets/reference/approved-concept.png)

## Provarlo su Ubuntu

Il pacchetto `.deb` copia soltanto i file in `/usr`: **non modifica l'avvio**.
L'attivazione è un comando separato, crea un backup e non riavvia il computer.

```sh
sudo apt install ./dist/dls-neon-grub_0.1.0_all.deb
dls-neon-theme install --dry-run
sudo dls-neon-theme install --profile 1080p --timeout 8
```

Il controllo finale rifiuta modifiche inattese alle voci di boot. Se la generazione
fallisce, la configurazione attiva resta quella precedente. L'installer non usa
`grub-install`, non scrive nella partizione EFI e non modifica l'ordine UEFI.

Il profilo 1080p è il punto di partenza per il laptop. Altri profili: `720p`, `1440p`,
`4k`. La risoluzione disponibile durante l'avvio dipende dal firmware, non dal
desktop Linux. GRUB sceglie un fallback se quella richiesta non è disponibile.
Il profilo tipografico resta quello scelto: per schermi piccoli usare `720p`.

Per usare l'archivio portabile senza installare un pacchetto:

```sh
tar -xzf dist/dls-neon-grub-0.1.0.tar.gz
cd dls-neon-grub-0.1.0
./install.sh --dry-run
sudo ./install.sh --profile 1080p --timeout 8
```

## Ripristino

```sh
sudo dls-neon-theme status
sudo dls-neon-theme restore
```

Con l'archivio portabile usare `sudo python3 ./dls-neon-theme restore`.
Il ripristino conserva backup e immagini; rimuove il nostro drop-in e ripristina
esattamente `grub.cfg` se non sono intervenuti aggiornamenti. Se nel frattempo
cambiano kernel o configurazione, si ferma: seguire [RECOVERY.md](docs/RECOVERY.md).
Disinstallare il `.deb` non disattiva automaticamente il tema: ripristinare prima.

## Sviluppo e prova senza riavviare

Dipendenze di build su Ubuntu/Debian:

```sh
sudo apt install python3-pil grub-common grub-efi-amd64-bin grub2-common xorriso mtools qemu-system-x86 qemu-system-gui ovmf make
make package
make preview
```

La VM usa GNU GRUB UEFI, un CD virtuale generato dal progetto e voci dimostrative;
non collega dischi del laptop né rete. `Enter` nelle voci dimostrative mostra
solo un messaggio: questa prova verifica grafica, selezione, submenu e console,
non il caricamento del kernel del laptop.

```sh
python3 scripts/preview.py --headless --profile 1080p
python3 scripts/preview.py --headless --profile 720p
python3 scripts/preview.py --headless --profile 1080p --resolution 1024x768
```

Screenshot e ISO finiscono in `build/`. `make package` crea archivio, `.deb` e
`SHA256SUMS` in `dist/`. I font DejaVu sono inclusi con la relativa licenza.
Il wallpaper è un'immagine statica: animazioni e transizioni non sono implementate.

## Fonti, prove e pubblicazione

- [Decisioni grafiche e provenienza](docs/DESIGN.md)
- [Stato delle verifiche](docs/VALIDATION.md)
- [Passi prima della pubblicazione](docs/RELEASE.md)
- [Formato ufficiale dei temi GNU GRUB](https://www.gnu.org/software/grub/manual/grub/html_node/Theme-file-format.html)

Il codice e l'artwork restano in anteprima privata finché non vengono scelti
licenza e nome pubblico e completata la prova sul laptop.
