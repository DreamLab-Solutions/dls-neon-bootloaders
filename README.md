# DreamLab · Temi di avvio

Repository ufficiale: [DreamLab-Solutions/dls-neon-grub](https://github.com/DreamLab-Solutions/dls-neon-grub),
mantenuto da DreamLab Solutions. Trasferito dal profilo Sunny-Pirate il 2026-10-16;
la cronologia e le PR sono conservate.

Versione **0.5.0**: console interattiva con scelta e anteprima dei quattro temi.
Il multiboot già presente — Windows, macOS, Linux e voci personalizzate — rimane
intatto. GRUB conserva ogni byte originale e aggiunge solo comandi grafici;
Limine conserva la sezione completa delle voci. Nessuna riscoperta o conversione
OS durante l’applicazione. [Guida e compatibilità](docs/INSTALLER.md).

Verifica il checksum, estrai `dls-neon-setup-0.5.0.tar.gz` e nella cartella esegui
`python3 dls-neon-setup`, senza sudo. Scegli 1–4, **p** per l’anteprima,
**v** per il piano con tutte le voci, **a** per l’applicazione confermata,
**r** per il ripristino e **q** per uscire. Python e sudo bastano; nessuna Tk.
Le anteprime PNG si aprono con il visualizzatore predefinito tramite xdg-open.

Il loader viene rilevato dalla voce UEFI attiva, senza whitelist di distribuzioni:
GRUB/grub2 su layout standard oppure l’esatto Limine 12.8 qualificato. Windows
Boot Manager e il loader Apple non usano questi temi; si installa dal Linux con
GRUB/Limine attivo. Le loro voci nel menu non sono un motivo per fermarsi.
La verifica tecnica, la conservazione delle voci, il backup e le conferme restano.

## Gestori separati

GRUB su Ubuntu/Debian: il `.deb` copia soltanto file in /usr e non attiva il tema.

```sh
sudo apt install ./dist/dls-neon-grub_0.5.0_all.deb
dls-neon-theme install --theme synaptic-cosmos --dry-run
sudo dls-neon-theme install --theme synaptic-cosmos --profile 1080p --timeout 8
sudo dls-neon-theme restore
```

L’archivio GRUB portabile offre gli stessi temi con `./install.sh --theme SLUG`.
Per Limine usare [OMARCHY.md](docs/OMARCHY.md) e il suo gestore dedicato;
non eseguire l’installer GRUB su Omarchy. Nessuno dei gestori usa grub-install,
reinstalla EFI o cambia l’ordine del firmware. Le voci restano della distribuzione.

## Build e verifica

Dipendenze di build Ubuntu/Debian: python3-pil, grub-common,
grub-efi-amd64-bin, grub2-common, xorriso, mtools, qemu-system-x86, ovmf,
make. [Ambiente isolato](packaging/Dockerfile.test).

```sh
make package
make limine-package
make setup-package
python3 -m unittest discover -s tests
python3 scripts/preview.py --headless --theme synaptic-cosmos
python3 scripts/limine_preview.py --theme synaptic-cosmos
```

I pacchetti e checksum sono in dist; build e ISO in build. Il pacchetto unificato
richiede le anteprime verificate conservate nel repository: se il tema GRUB cambia,
rigenerare la prova e aggiornare la sua evidenza prima di confezionarlo.
Le VM usano supporti usa e getta e non collegano dischi host né rete.

110 test, incluse interazioni della console senza GUI, controllano
transazioni, conservazione multiboot, integrità, piani e conferme. I tre nuovi temi GRUB
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
