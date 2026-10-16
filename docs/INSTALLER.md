# DreamLab · Selettore dei temi di avvio — 0.4.0

Il pacchetto unificato `dls-neon-setup-0.4.0.tar.gz` offre la scelta di Event
Horizon, Quantum Fabric (2), Sentient Atlas (3) e Synaptic Cosmos (4), con
anteprime del menu registrate nel vero GRUB e Limine in VM. L’anteprima è
un riferimento a 1080p con voci dimostrative: risoluzione, testo e menu reali
dipendono dal firmware e dalla distribuzione. Nessun bootloader viene installato
oppure migrato; il selettore rileva la distribuzione e verifica la voce UEFI attiva.

## Avvio

Verifica `SHA256SUMS-setup` accanto all’archivio, estrailo e dalla sua cartella
esegui `python3 dls-neon-setup`, senza sudo. Servono Python 3, Tk e Polkit/pkexec.
Su Ubuntu/Debian Tk è il pacchetto `python3-tk`; su Omarchy `tk`. Se mancano,
il programma lo segnala senza installarli automaticamente. I gestori CLI dei
pacchetti separati restano disponibili.

1. Scegli l’immagine. Puoi confrontare le anteprime dei due bootloader; questo
   cambia solo l’immagine mostrata, non il bootloader che sarà configurato.
2. Usa **Verifica piano**: l’autenticazione amministratore permette una lettura
   della configurazione e dell’avvio attivo; questo passo non scrive file di boot.
3. Conferma di aver verificato backup indipendente e live USB UEFI utilizzabile.
4. Usa **Applica tema** e conferma la modifica. Il piano viene ricontrollato,
   viene conservato un backup di transazione e sono verificate le voci di avvio.
5. Riavvia personalmente e verifica menu, caricamento del sistema e desktop.
   Il programma non riavvia e non presenta l’applicazione dei file come prova
   di un avvio fisico riuscito.

**Ripristina precedente** usa il checkpoint del gestore appropriato. I backup
restano in `/var/lib/dls-neon-grub` o `/var/lib/dls-neon-limine`. Per Limine,
più cambi possono avere più checkpoint; il gestore CLI `uninstall` li percorre
tutti. Per GRUB, ripristina il tema attivo prima di sceglierne un altro. Un
aggiornamento successivo di kernel/configurazione può rendere necessario il
confronto manuale: il ripristino automatico non forza file modificati.

## Compatibilità

| Sistema | Bootloader qualificato dal selettore | Stato |
|---|---|---|
| Ubuntu / Debian x86-64 UEFI | GRUB, avvio EFI ubuntu/debian, ESP FAT in /boot/efi corrispondente alla voce attiva | Build, transazioni e menu provati; nuovi temi provati in VM, avvio fisico Ubuntu ancora da qualificare |
| Omarchy x86-64 UEFI | Limine 12.8.0, esatto binario qualificato, Secure Boot disabilitato, ESP FAT in /boot | Synaptic Cosmos osservato sul monitor reale e test positivo riferito dall’utente; nuovo boot ID osservato |
| Ubuntu con Limine / Omarchy con GRUB / BIOS / altri loader o versioni | Nessuna applicazione | Il selettore si ferma; non converte l’avvio |

GRUB applica il profilo tipografico scelto e rende visibile il menu con l’attesa
esplicita mostrata nel piano (predefinita 8 secondi). Limine conserva risoluzione,
default e timeout. Entrambi mantengono le voci della distribuzione e non cercano
o aggiungono sistemi operativi. Ubuntu sul secondo disco deve essere già una
voce del bootloader, oppure essere avviato dal menu firmware: la scelta del tema
non risolve l’importazione di quella voce.

## Recovery e distribuzione

Preparare e verificare una live USB UEFI e una copia del backup fuori dal disco
prima di applicare. Per recovery e conflitti consultare [OMARCHY.md](OMARCHY.md)
e [RECOVERY.md](RECOVERY.md). Il selettore conserva i controlli dei due gestori;
non disabilita guardie di versione, cifratura o Secure Boot e non usa grub-install.
La conferma nel selettore è una dichiarazione dell’utente sulla propria recovery,
non una verifica automatica della chiavetta o del supporto indipendente.

Codice MIT; artwork CC BY 4.0 dove esistono diritti applicabili, con provenienza
AI e marchi DreamLab riservati. La foto personale del monitor rimane fuori dal
repository. Il merge privato non equivale a una release o cambio di visibilità.
