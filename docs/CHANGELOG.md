# Changelog

## 0.5.1 — 2026-10-16

- Make English the primary documentation language, with a release-download quick
  start, backend guides, compatibility matrix, recovery and development instructions.
- Add a gallery of all four themes in native GRUB and Limine; keep concise Italian
  user help in `docs/it/` and remove obsolete recovery instructions.
- Publish the combined console, GRUB portable/Debian and Limine portable packages
  as one versioned preview release with English notes and a unified SHA-256 file.
- Preserve offline documentation links and include referenced screenshots in each
  package; validate manifests, package contents and release asset consistency.
- Add a manual build-to-draft release workflow. Docker images remain development
  tools and are excluded from runtime packages.
- Installer behavior and artwork are unchanged from 0.5.0. Hardware qualification
  remains limited to the previously observed Omarchy/Synaptic Cosmos experiment.

## 0.5.0 — Console and multiboot preservation

- Replace Tk with a dependency-light interactive console and optional native-image
  previews. Browsing never requests root; plan and writes remain separate.
- Detect the actual UEFI loader instead of distribution identity. Accept standard
  GRUB/grub2 paths/tools/vendor directories; keep all technical Limine EFI guards.
- Preserve every original GRUB config byte and append appearance-only commands;
  use a dedicated generator hook for persistence, without rerunning os-prober or
  regenerating OS entries during installation. Resolve assets by filesystem UUID
  and GRUB-relative paths. Restore legacy drop-in records as well as new hooks.
- Cover Windows, macOS/OpenCore, other Linux and custom entries in both managers.
  This is entry preservation, not a claim of Windows/macOS kernel boot support.

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

## 0.3.0 — AI universe collection

- Package Quantum Fabric, Sentient Atlas and Synaptic Cosmos with recorded
  prompts/provenance; preserve Event Horizon and its source artwork.
- Add explicit theme selection and switching, retaining the previous theme and
  assets. Restore undoes one checkpoint; uninstall unwinds all checkpoints.
- Verify switch failure/recovery, prior-asset conflicts and interrupted journals.
- Add per-theme native Limine previews with optional real entry-title fixtures;
  all boot paths remain demo-only and no host disk is attached.

## 0.2.0 — Omarchy / Limine preview

- Add native Limine appearance adapter; retain existing GRUB target separately.
- Read-only plan and inspection, verified transaction backup, explicit activation,
  restore/uninstall, interrupted-write recovery and conservative conflict stops.
- Real UEFI Limine screenshot harness, no host disk or VM network.
- Record chosen MIT / CC BY 4.0 component licensing and AI artwork provenance.
- Hardware installation, OS boot and public visibility remain unverified/pending.

## 0.1.1 — 2026-10-11

- Handle an OS-prober EFI label's Linux device suffix changing after disk renumbering
  only when the boot entry ID, filesystem UUID and EFI loader path still match.
- Compare EFI commands, reject removed/reordered entries and retain aborted
  activation evidence; parse headers containing `${menuentry_id_option}` correctly.
- Reproduce the reported issue with synthetic fixtures. Full physical activation
  remained pending. Version 0.5 later removed regeneration from theme activation.

## 0.1.0 — 2026-10-11

- First private GRUB preview, portable/Debian packages, backup/restore activation
  and isolated UEFI menu rendering in QEMU.
