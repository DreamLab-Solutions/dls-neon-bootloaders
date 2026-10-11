# Prima della pubblicazione

- Completare almeno un avvio reale su x86-64 test laptop con Ubuntu 26.04 UEFI.
- Provare selezione, timer, submenu, avvio Ubuntu e ritorno al desktop.
- Verificare schermo interno ed eventuale monitor esterno usato all'avvio.
- Provare il ripristino e, se desiderato, riattivare il tema.
- Scegliere licenza del codice e condizioni d'uso di artwork e marchio DreamLab.
- Approvare nome pubblico, proprietario GitHub e screenshot da pubblicare.
- Aggiornare VALIDATION.md con evidenze, non con l'esito presunto della VM.
- Solo dopo approvazione: rendere pubblico, creare tag e release con pacchetti
  e checksum; non pubblicare i report locali di sistema o il contenuto dei backup.

Limiti iniziali: target Ubuntu/Debian con GRUB2, grafica statica, formati 16:9
preferiti. Secure Boot del laptop e caricamento del suo kernel richiedono una
prova fisica. La VM usa un firmware UEFI senza Secure Boot per la prova del tema.
