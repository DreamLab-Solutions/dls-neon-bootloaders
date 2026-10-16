## 0.4.0 — Guided choice and native previews

- Add an unprivileged graphical chooser, real bootloader previews and explicit
  authenticated plan/apply/restore for qualified Ubuntu/Debian GRUB and Omarchy Limine.
- Package all four theme choices for both bootloaders; centre the GRUB menu for
  the AI universe artwork and retain Event Horizon's original composition.
- Bind application to the exact reviewed config, state, selection and bundle;
  recheck the GRUB baseline inside the transaction. Keep recovery confirmation,
  restore conflict checks and no automatic bootloader migration or reboot.
- Record the user's successful hardware test, monitor-photo observation and changed
  boot ID without claiming unobserved cold/warm cycles or physical rollback.

# 0.3.0 — AI universe collection

- Package Quantum Fabric, Sentient Atlas and Synaptic Cosmos with recorded
  prompts/provenance; preserve Event Horizon and its source artwork.
- Add explicit theme selection and switching, retaining the previous theme and
  assets. Restore undoes one checkpoint; uninstall unwinds all checkpoints.
- Verify switch failure/recovery, prior-asset conflicts and interrupted journals.
- Add per-theme native Limine previews with optional real entry-title fixtures;
  all boot paths remain demo-only and no host disk is attached.

# 0.2.0 — Omarchy / Limine preview

- Add native Limine appearance adapter; retain existing GRUB target separately.
- Read-only plan and inspection, verified transaction backup, explicit activation,
  restore/uninstall, interrupted-write recovery and conservative conflict stops.
- Real UEFI Limine screenshot harness, no host disk or VM network.
- Record chosen MIT / CC BY 4.0 component licensing and AI artwork provenance.
- Hardware installation, OS boot and public visibility remain unverified/pending.

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
