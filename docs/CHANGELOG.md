# Changelog

## 0.1.1 — 2026-10-11

Corregge l'interruzione dell'attivazione quando cambia il nome Linux del disco
Windows, pur rimanendo uguale l'UUID della sua partizione EFI.

- Tollerato soltanto il suffisso del dispositivo nell'etichetta delle voci EFI
  generate da os-prober, con stesso ID, UUID e percorso del loader.
- Confrontati anche i comandi della voce EFI; soltanto root e hint hardware
  risolti tramite lo stesso UUID possono differire.
- Restano bloccati cambi di destinazione, rimozione e riordino delle voci.
- Le attivazioni interrotte conservano candidato, diff e stato `aborted`.
- Corretta l'estrazione delle intestazioni con `${menuentry_id_option}`.

Il problema è stato riprodotto con fixture sintetiche equivalenti alle intestazioni
fornite dall'utente. Il nome corrente del disco e l'UUID sono stati verificati
localmente. Il contenuto completo del grub.cfg protetto non è stato letto dalla
chat; la configurazione candidata verrà controllata dall'installer autenticato.

## 0.1.0 — 2026-10-11

Prima anteprima privata del tema, pacchetti portabile e Debian, attivazione con
backup e ripristino, prova UEFI in QEMU.
