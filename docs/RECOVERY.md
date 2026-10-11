# Ripristino

## Il sistema parte e non sono intervenuti aggiornamenti

Eseguire `sudo dls-neon-theme restore`. La procedura controlla gli hash della
configurazione, del drop-in, del tema e del backup prima di scrivere.
I backup restano in `/var/lib/dls-neon-grub/backups/` con data UTC.
Le immagini installate restano in `/boot/grub/themes/dls-neon-*` per recupero.

## È stato aggiornato il kernel o modificato GRUB dopo l'installazione

Non ripristinare un vecchio grub.cfg: potrebbe contenere kernel ormai rimossi.
Disattivare soltanto il drop-in del tema, quindi rigenerare dalla configurazione
attuale. Conservare prima una copia della configurazione e leggere `status`.

```sh
sudo mv /etc/default/grub.d/99-dls-neon.cfg /etc/default/grub.d/99-dls-neon.cfg.disabled
sudo update-grub
```

Verificare che `update-grub` termini correttamente e che le voci siano quelle
attese. Se fallisce, ripristinare il nome del drop-in e indagare prima del riavvio.
La procedura manuale lascia il registro di attivazione per indagine: dopo verifica
spostare `active.json` nella cartella del suo backup, senza sovrascrivere altri file.

## Grafica non leggibile nella schermata di GRUB

Premere `c` e digitare `terminal_output console`, poi `Esc` per tornare al menu
testuale. Se la tastiera non risponde o l'avvio resta bloccato, usare il supporto
di ripristino Ubuntu e montare la vera installazione (e /boot separato, se presente).
Seguire il recupero GRUB della propria distribuzione. Questo progetto non modifica
EFI o NVRAM e non richiede di reinstallare GRUB per rimuovere il solo tema.

## Attivazione interrotta

Prima di generare la configurazione viene registrata la transazione con stato
`preparing`. Un arresto del processo o una perdita di alimentazione può richiedere
verifica manuale di drop-in, asset e grub.cfg. Non cancellare il backup. Consultare
`transaction.json`, confrontare gli hash e usare il ripristino manuale sopra.
