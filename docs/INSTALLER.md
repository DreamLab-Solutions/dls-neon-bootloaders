# DreamLab · Installer console — 0.5.0

Il tema modifica la grafica di GRUB o Limine. **Windows, macOS, altri Linux e
voci personalizzate già presenti non vengono filtrati o rimossi.** La scelta
dell’immagine non aggiunge sistemi operativi e non ne modifica loader, kernel,
ordine o opzioni. L’installer viene eseguito da Linux; non installa questo tema
nel Windows Boot Manager o nel loader Apple e non migra automaticamente l’avvio.

## Avvio e scelta

Verifica il checksum esterno, estrai `dls-neon-setup-0.5.0.tar.gz` e nella cartella
avvia `python3 dls-neon-setup`, senza sudo. Servono soltanto Python 3 e sudo per
le azioni amministrative. Tk e Polkit non sono richiesti. Per aprire le anteprime
nel visualizzatore predefinito viene usato `xdg-open`; se non è disponibile,
resta indicato il percorso PNG da aprire su un altro schermo/computer.

- **1–4**: scegli Event Horizon, Quantum Fabric (2), Sentient Atlas (3), Synaptic Cosmos (4).
- **p**: apri l’anteprima del menu reale in VM; **b** confronta GRUB/Limine.
- **d**: rileva il loader dalla voce EFI attiva; non dal nome della distribuzione.
- **v**: verifica il piano in sola lettura e mostra tutte le voci da conservare.
- **o**: scegli profilo e attesa GRUB. Limine mantiene le impostazioni native.
- **a**: applica dopo il piano, conferma della recovery e parola **APPLICA**.
- **r**: ripristina il checkpoint dopo conferma separata **RIPRISTINA**.
- **q**: esci senza altre operazioni.

Scelta e anteprime funzionano senza autenticazione. Una verifica non riuscita
lascia aperta la console per continuare a sfogliare. L’applicazione richiede un
loader e percorsi verificabili, un pacchetto integro e lo stesso piano revisionato:
non si aggirano configurazioni ambigue, binari non qualificati o backup corrotti.
Nessun riavvio automatico. Verificare personalmente il successivo avvio reale.

## Multiboot

GRUB 0.5 conserva **ogni byte del file originale**, inclusi preambolo, funzioni,
Windows, macOS/OpenCore, altri Linux, recovery, submenus e voci sconosciute.
Aggiunge in fondo un blocco con soli comandi grafici: non esegue grub-mkconfig,
update-grub o os-prober durante l’installazione. Un hook dedicato in
`/etc/grub.d/99_dls_neon_theme` emette soltanto quel blocco durante i successivi
aggiornamenti della distribuzione. Quegli aggiornamenti continuano a gestire le
proprie voci; il tema non ne altera la politica di rilevamento.

Gli asset GRUB vengono individuati tramite UUID del filesystem e percorso
GRUB-relativo ottenuti dagli strumenti nativi: sono considerati /boot separato
e Btrfs. I layout supportati sono `/boot/grub/grub.cfg` e `/boot/grub2/grub.cfg`,
con strumenti `grub-*` oppure `grub2-*` e directory generatore `/etc/grub.d`.
Sono conservati anche i menu dinamici BLS (`blscfg`): la console li indica senza
riscrivere i file delle voci in /boot/loader/entries.
Il loader EFI attivo e la ESP montata devono corrispondere; non serve che la
distribuzione si chiami Ubuntu, Debian o Omarchy. Le varianti di layout sono
provate con fixture; non sono una certificazione fisica di ogni distribuzione.

Limine conserva byte per byte la sezione completa delle voci e cambia soltanto
le opzioni grafiche. Non impone Omarchy/pacman né un’etichetta firmware chiamata
Limine: verifica il percorso EFI, l’esatto binario 12.8.0 qualificato, UEFI x86-64,
ESP FAT scrivibile in /boot e la guardia Secure Boot esistente. Versioni, percorsi
o loader differenti richiedono verifica tecnica; il solo nome di un altro OS nel
menu non ferma l’installazione.

Se Windows, macOS o un altro Linux è sul disco ma manca dal menu, il tema non lo
crea. Va gestito dalla configurazione del bootloader o dal menu firmware, con una
procedura dedicata. La presenza di una voce non prova che quel sistema sia
avviabile: non cambiamo BCD, FileVault/BitLocker, OpenCore o loader di terzi.

## Backup e ripristino

Prima di applicare: backup indipendente verificato e chiavetta live UEFI usabile.
L’installer conserva un backup di transazione; la conferma della console è una
dichiarazione dell’utente sulla propria recovery. Non registra passphrase.
Il ripristino rifiuta modifiche successive e backup/asset/hook corrotti, conserva
le copie e gestisce anche i vecchi record GRUB con drop-in 0.4 e precedenti.
GRUB richiede il ripristino prima di una nuova scelta; Limine mantiene la propria
cronologia. [Recovery GRUB](RECOVERY.md), [gestore Limine](OMARCHY.md).

## Prove e licenze

Test di transazione e console con Windows, macOS, altri Linux e voci custom;
prove di menu, scelta, submenu, console e scrolling in bootloader UEFI reali in VM.
Queste voci sono dimostrative e non provano l’avvio reale di Windows/macOS.
Resta valida la prova fisica riferita dall’utente per Synaptic Cosmos su Omarchy;
nessuna nuova applicazione è stata effettuata sul laptop per provare la console.

Codice MIT, artwork CC BY 4.0 dove applicabile, provenienza AI e marchi DreamLab
riservati. La foto personale del monitor e i backup restano fuori dal repository.
La visibilità e la release pubblica rimangono separate dal lavoro privato.

Fonti tecniche: [GRUB multiboot](https://www.gnu.org/software/grub/manual/grub/html_node/Multi_002dboot-manual-config.html), [ricerca UUID](https://www.gnu.org/software/grub/manual/grub/html_node/search.html).
