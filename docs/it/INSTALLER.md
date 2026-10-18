# Installazione da Linux

Scarica `dls-neon-setup-0.5.2.tar.gz` e `SHA256SUMS` dagli asset della
[release](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/tag/v0.5.2).
Nella cartella dei download:

```sh
sha256sum --check --ignore-missing SHA256SUMS
tar -xzf dls-neon-setup-0.5.2.tar.gz
cd dls-neon-setup-0.5.2
python3 dls-neon-setup
```

Prosegui solo se il checksum dell'archivio risulta **OK**. Avvia la console dal
tuo utente normale: sudo viene richiesto per leggere il sistema e per applicare
un'operazione confermata. Servono Python 3.11+, sudo, efibootmgr, util-linux e,
per GRUB, i suoi strumenti nativi di verifica e risoluzione dei percorsi.
`xdg-open` serve solo ad aprire le anteprime. Docker non è richiesto.

| Tasto | Azione |
| --- | --- |
| **1–4** | Scegli il tema; Synaptic Cosmos è la selezione iniziale. |
| **p** | Apri l'anteprima dell'immagine con il menu nativo. |
| **b** | Confronta anteprime GRUB/Limine; non cambia il bootloader installato. |
| **v** | Verifica il piano e leggi le voci da conservare. |
| **o** | Cambia profilo e attesa GRUB. |
| **a** | Applica il piano dopo le conferme. |
| **r** | Ripristina il checkpoint precedente. |
| **q** | Esci. |

Prima di applicare verifica un backup su supporto indipendente e una live USB
avviabile in UEFI, con accesso alla root cifrata se presente. Premi **v**, leggi
il piano, poi **a**. Conferma la recovery con **s** e digita **APPLICA**. Il programma
non riavvia: dovrai controllare personalmente il successivo menu e avvio reale.

La [matrice di compatibilità](../COMPATIBILITY.md) descrive i layout supportati:
GRUB UEFI x86-64 oppure l'esatto Limine 12.8.0 qualificato. La presenza di Windows,
macOS, altri Linux o voci personalizzate non blocca il tema. Le voci esistenti
restano intatte; i sistemi mancanti non vengono aggiunti automaticamente.

La console usa GRUB a 1080p con attesa di 8 secondi come default; Limine conserva
risoluzione, voce predefinita e attesa. Per cambiare tema GRUB ripristina prima
quello attivo. Se un aggiornamento ha cambiato le voci, segui la
[guida di ripristino](RECOVERY.md).

I pacchetti `.deb` e gli archivi dedicati offrono la CLI senza selettore:
[GRUB](../GRUB.md), [Limine/Omarchy](../OMARCHY.md). L'archivio Source code di
GitHub è per sviluppatori, non è l'installer pronto all'uso.
