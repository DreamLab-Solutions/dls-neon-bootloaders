# Ripristino e rimozione

Conserva strumenti estratti, backup e checksum finché non hai verificato avvio
e ripristino. Nella console esegui **v**, poi **r**, conferma **s** e scrivi
**RIPRISTINA**. Per GRUB ripristina prima di applicare un'altra immagine.

Se hai installato il pacchetto Debian:

```sh
sudo dls-neon-theme restore
sudo apt remove dls-neon-grub
```

Per l'archivio GRUB, dalla sua directory: `sudo python3 dls-neon-theme restore`.
Per l'archivio Limine: `sudo python3 dls-neon-limine restore --approve-boot-write`.
Limine annulla un checkpoint alla volta; `uninstall --approve-boot-write` annulla
tutta la cronologia del tema. I backup vengono conservati.

Se il ripristino segnala modifiche successive, fermati: non copiare il vecchio
file di configurazione sopra voci di kernel o snapshot aggiornate. Confronta file
attuale, originale e candidato; rimuovi solo la grafica gestita conservando tutte
le voci correnti. Non cancellare record o journal per aggirare il controllo.

Se non riesci ad avviare, usa la live USB già verificata e il backup indipendente.
Identifica root ed ESP per UUID, sblocca la cifratura e monta la struttura corretta
prima di verificare i backup. La [guida tecnica in inglese](../RECOVERY.md) spiega
conflitti, transazioni interrotte e recovery da live USB. Non occorre reinstallare
il bootloader o modificare NVRAM per eliminare il solo tema.
