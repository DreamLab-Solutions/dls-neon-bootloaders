# Design e provenienza

Fonte: conversazione ChatGPT private design discussion (archived outside Git),
letta il 2026-10-11, inclusa l'immagine finale allegata e approvata dall'utente.
Il recupero disponibile contiene cinque scambi recenti: non presume altri requisiti.

Decisioni esplicite recuperate: palette dls-theme con teal, viola e giallo; teal
distinguibile dal cyan; giallo esatto #D9FF00; usare l'ultima immagine allegata.
L'immagine originale è conservata senza alterazioni in assets/reference/approved-concept.png.

Il tool integrato imagegen ha ricavato assets/backgrounds/portal.png rimuovendo
solo le finte voci e il rettangolo selezionato dal concept. Prompt completo in
artwork-prompt.txt. Il risultato è stato ispezionato visivamente. Non è stata
rigenerata l'identità DreamLab né cambiata la composizione deliberatamente.
La tinta UI selezionata è deterministica #D9FF00; il colore del raster è pittorico.

Le etichette di avvio sono generate da Ubuntu, non impresse nel wallpaper.
"Recovery mode" dipende dai submenu della distribuzione. Il tema non aggiunge
azioni di spegnimento o modifica delle impostazioni firmware al sistema reale.

Implementazione nativa: boot_menu, nove tasselli per la selezione, scrollbar,
font PF2 DejaVu Sans Mono, terminale opaco per mantenere leggibile la console.
Layout relativi allo schermo e quattro scale tipografiche. Il wallpaper mantiene
il testo di branding del riferimento; il testo operativo è disegnato da GRUB.

Il progetto è autonomo rispetto ai repository della piattaforma DreamLab e
Sunnyday: non modifica le loro fondazioni grafiche o librerie. Il registro
SharePoint esistente è stato consultato; nessuna scheda specifica per questo
nuovo prodotto è stata identificata. Questa nota documenta il progetto locale,
non dichiara un aggiornamento del registro condiviso.
