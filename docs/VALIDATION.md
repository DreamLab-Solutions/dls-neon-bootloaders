# Verifiche — 2026-10-11

## Verificato

- Host: x86-64 test laptop, Ubuntu 26.04.1 LTS x86_64, UEFI, GNU GRUB 2.14.
  La configurazione di partenza dichiara menu nascosto e timeout zero.
- Build dei font PF2 e degli asset con manifest SHA-256; pacchetti `.deb` e
  `.tar.gz`, installer portabile e checksum separati.
- 11 test di transazione superati: installazione/ripristino, reinstallazione,
  errore del generatore, errore di sintassi, variazione delle voci di boot,
  tema non caricato, scrittura concorrente, aggiornamento successivo,
  drop-in esistente, asset corrotti/symlink e backup corrotto.
- Esecuzione del vero GNU GRUB 2.14 in QEMU 10.2.1 con firmware OVMF UEFI,
  senza collegamento ai dischi del laptop e senza rete nella VM.
- Profili 1280×720, 1920×1080, 2560×1440 e 3840×2160: screenshot reali del
  menu e del timer, selezione tramite frecce, submenu, console e scorrimento.
  Screenshot rappresentativi conservati in `docs/screenshots/`.
- Fallback 1024×768 con tipografia 1080p: menu e navigazione funzionano, ma
  le etichette lunghe vengono tagliate. Se il firmware usa questa risoluzione,
  selezionare il profilo compatto 720p; il formato 4:3 deforma il wallpaper 16:9.
- Il primo workflow GitHub ha completato build, test, packaging e preview
  su Ubuntu 24.04: [run iniziale](https://github.com/Sunny-Pirate/dls-neon-grub/actions/runs/38157482076).

La prova iniziale a bassa risoluzione ha evidenziato un errore nella VM:
la scelta implicita del font iniziale impediva l'attivazione di gfxterm.
La preview ora imposta un font iniziale di 14px e 64 MiB di memoria video,
attende le dimensioni richieste e i pixel della selezione #D9FF00 e rifiuta
cinque schermate identiche. Non considera riuscita una semplice uscita di QEMU.
Il timer della demo è 120 secondi; l'attivazione sul laptop propone 8 secondi.

## Da completare sul laptop

Il `.deb` non è stato installato e il tema non è stato attivato nel GRUB del
laptop: `sudo` richiede autenticazione interattiva dell'utente. Nessuna modifica
a /boot, /etc/default/grub, EFI o NVRAM è stata applicata. Il file grub.cfg attivo
richiede privilegi per la lettura e non è stato acquisito senza autenticazione.

Restano da verificare l'effettiva modalità video del firmware, il caricamento
di Ubuntu con Secure Boot nelle impostazioni reali, il ritorno al desktop e il
ripristino sul sistema fisico. La VM prova tema e navigazione con voci dimostrative,
non costituisce prova dell'avvio del kernel del laptop.
