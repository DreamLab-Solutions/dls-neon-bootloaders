# DreamLab · Temi di avvio

Versione **0.4.0**: selettore grafico con scelta e anteprima di Event Horizon,
Quantum Fabric (proposta 2), Sentient Atlas (3) e Synaptic Cosmos (4).

## Installazione guidata

Verifica il checksum esterno, estrai `dls-neon-setup-0.4.0.tar.gz` e dalla sua
cartella avvia `python3 dls-neon-setup`, senza sudo. Servono Python 3, Tk e
Polkit/pkexec; il programma segnala le dipendenze mancanti senza installarle.
[Guida completa, compatibilità e recovery](docs/INSTALLER.md).

Scegli l’immagine, confronta il menu GRUB/Limine e usa **Verifica piano**.
Il piano autentica una lettura del sistema; l’applicazione è un passo separato,
con conferma di backup/live USB e approvazione esplicita della modifica.
Il piano viene ricontrollato prima della transazione e non c’è riavvio automatico.
**Ripristina precedente** conserva i backup e rifiuta conflitti con aggiornamenti.

| Target del selettore | Compatibilità |
|---|---|
| Ubuntu/Debian x86-64 UEFI con GRUB | ESP FAT in /boot/efi corrispondente alla voce EFI ubuntu/debian attiva; tutti e quattro i temi; profili 720p/1080p/1440p/4k e attesa esplicita |
| Omarchy x86-64 UEFI con Limine | Esatto Limine 12.8.0 qualificato, ESP FAT in /boot, Secure Boot disabilitato; tutti e quattro i temi; impostazioni native conservate |
| Altri loader, combinazioni o versioni | Applicazione fermata; nessuna migrazione automatica |

Le anteprime vengono da bootloader reali in VM a 1080p con voci dimostrative.
Non qualificano l’avvio del kernel; risoluzione e testo reali dipendono dal sistema.
Il selettore non importa sistemi operativi: Ubuntu sul secondo disco deve essere
già nel menu del loader o essere selezionato dal firmware.

## Gestori separati

GRUB su Ubuntu/Debian: il `.deb` copia soltanto file in /usr e non attiva il tema.

```sh
sudo apt install ./dist/dls-neon-grub_0.4.0_all.deb
dls-neon-theme install --theme synaptic-cosmos --dry-run
sudo dls-neon-theme install --theme synaptic-cosmos --profile 1080p --timeout 8
sudo dls-neon-theme restore
```

L’archivio GRUB portabile offre gli stessi temi con `./install.sh --theme SLUG`.
Per Limine usare [OMARCHY.md](docs/OMARCHY.md) e il suo gestore dedicato;
non eseguire l’installer GRUB su Omarchy. Nessuno dei gestori usa grub-install,
reinstalla EFI o cambia l’ordine del firmware. Le voci restano della distribuzione.

## Build e verifica

Dipendenze di build Ubuntu/Debian: python3-pil, python3-tk, grub-common,
grub-efi-amd64-bin, grub2-common, xorriso, mtools, qemu-system-x86, ovmf,
xvfb, xauth, make. [Ambiente isolato](packaging/Dockerfile.test).

```sh
make package
make limine-package
make setup-package
xvfb-run -a python3 -m unittest discover -s tests
python3 scripts/preview.py --headless --theme synaptic-cosmos
python3 scripts/limine_preview.py --theme synaptic-cosmos
```

I pacchetti e checksum sono in dist; build e ISO in build. Il pacchetto unificato
richiede le anteprime verificate conservate nel repository: se il tema GRUB cambia,
rigenerare la prova e aggiornare la sua evidenza prima di confezionarlo.
Le VM usano supporti usa e getta e non collegano dischi host né rete.

92 test, incluse interazioni del selettore su display isolato, controllano
transazioni, confronto voci, integrità, piani e conferme. I tre nuovi temi GRUB
sono provati con selezione, sottomenu, console e scorrimento. Synaptic Cosmos
è osservato nella foto del monitor reale, con prova positiva riferita dall’utente
e nuovo boot ID/kernel Omarchy verificati in sola lettura. Restano da qualificare
Ubuntu fisico, cicli cold/restart distinti, altri display/OS e rollback fisico.

- [Prove GRUB](docs/VALIDATION.md) e [Limine / porting](docs/VALIDATION-OMARCHY.md)
- [Recovery GRUB](docs/RECOVERY.md), [guida Limine](docs/OMARCHY.md)
- [Design](docs/DESIGN.md), [provenienza AI](docs/ai-artwork-provenance.json)
- [Licenze](LICENSE), [artwork](ARTWORK-LICENSE.md), [gate pubblicazione](docs/RELEASE.md)

Codice MIT; artwork CC BY 4.0 dove applicabile; font con licenza propria;
marchi DreamLab riservati. Riferimenti e foto personali non sono inclusi nei
pacchetti runtime. Il repository resta privato: il merge non è una release pubblica.
