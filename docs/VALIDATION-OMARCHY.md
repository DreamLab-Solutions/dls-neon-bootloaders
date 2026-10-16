# Omarchy / Limine port — evidence on 2026-10-16

## Verified

- Existing private repository `Sunny-Pirate/dls-neon-grub` was cloned under
  `~/Projects/dls-neon-grub`; development branch `feat/omarchy-limine`.
- Actual target: Omarchy 4.0.4, UEFI x86-64, root Btrfs on LUKS2, separate FAT
  ESP mounted at `/boot`, SecureBoot variable disabled. Installed Limine 12.8.0.
- The firmware BootCurrent names Limine. The actual ESP EFI executable matches
  the installed package and the verified upstream 12.8.0 binary byte for byte:
  SHA256 `3fe0de87c13a12998b3c785b0c57ddfbcd6fc57251c1b0628604583ec8e9a5ff`.
- Protected configuration read via authenticated read-only operations. It contains
  Omarchy, its kernel and two snapshots. Ubuntu has a firmware entry on the
  second physical disk but is absent from the actual Limine menu. Automatic
  FIND_BOOTLOADERS is enabled; that is not evidence Ubuntu was imported or boots.
- Exact appearance candidate prepared from the verified baseline: every byte
  from the first menu entry onward is unchanged. Default entry 2 remains,
  timeout remains unspecified, security and kernel settings remain unchanged.
- Local backup copied and reread: all 24 ESP/config files matched archived bytes
  and a second source read. Private archive and device inventory remain outside
  the repository in the local Codex work directory. Backup creation itself wrote
  no boot file; the later approved appearance activation is recorded below.
- 52 tests pass under both the host Python 3.14 and isolated Debian Python 3.11:
  26 retained GRUB cases plus 26 Limine cases. Limine coverage includes read-only
  plans, exact entry preservation, install/restore, later-kernel conflict,
  interrupted asset/config writes, corruption, symlinks, path traversal,
  ownership, concurrent change, lock contention and platform/bootloader guards.
- Both GRUB 0.2.0 archive/deb and Limine 0.2.0 archive built successfully in the
  isolated Debian test image. The existing GRUB installer logic is unchanged.
- Real Limine UEFI graphics in QEMU 7.2.22/OVMF, TCG, no network and only a
  disposable FAT disk image. Menu, selection and snapshot submenu captured at
  1920x1080, 1280x720 and 1024x768; native palette and distinct screens checked.
  [1080p screenshot](screenshots/limine-1080p.png),
  [1024x768 screenshot](screenshots/limine-1024x768.png).
  Hashes and rendering scope are in the adjacent evidence JSON files.
- Test download pinned to upstream release v12.8.0 and archive SHA256
  `e21b0a9ce1cf83e79eb0f3fa6d6de49a1b6d1288df11e2232e41c9f4916b673d`.

## Limits and remaining gates

The UI remains Limine's centred menu and bitmap type. It does not reproduce
GRUB positioning, outline selection or PF2 typography. 1024x768 stretches the
source artwork. The source is 1672x941; no new native 4K art was generated.
Only explicitly qualified 12.8.0 EFI build is allowed by the activation guard.
A package upgrade that changes it requires review, not disabling the guard.

These VM entries are deliberately demonstrations with nonexistent kernel paths.
They prove loader rendering/navigation, not OS kernel boot or a full boot
lifecycle. No actual Omarchy boot under the new theme, Ubuntu boot, 4K firmware
mode, hardware restart/cold boot, agent-observed independent backup copy, live-USB recovery or
physical rollback has been verified. The user subsequently confirmed the recovery and independent-copy checks
complete and explicitly approved activation; those checks are user-reported.

No unattended reboot, bootloader migration, EFI executable replacement or NVRAM
edit was performed. The approved appearance activation is recorded below. Public repository visibility and releases remain pending physical
qualification and reference-image redistribution clearance. Runtime artwork
licensing is CC BY 4.0 where applicable; code MIT; DreamLab marks reserved.

## Approved appearance activation — 2026-10-16

The user explicitly approved proceeding and confirmed completion of the recovery
checks. The exact approved 0.2.0 archive and local backup checksums were reverified;
platform guards passed and the live config matched the reviewed baseline.
Authenticated activation completed, followed by an independent privileged readback:

- Active config matches the exact reviewed appearance candidate.
- The entire native entry section is byte-identical to its baseline.
- All other files in the prior ESP/config inventory remain unchanged.
- The two owned appearance assets match their checksums; no interrupted journal.
- Firmware entries and order remain unchanged; transaction backup is retained.

This verifies files on disk. No hardware reboot or themed OS startup was performed,
and the current boot ID is unchanged. Visual rendering on the actual display,
cold boot/restart, desktop return and hardware rollback remain pending. The user
initiates the reboot; do not silently reboot or mark physical qualification passed.
Private local backups, raw boot config and identifying inventory are excluded
from this repository. Public visibility and releases remain pending.

## AI universe collection — 0.3.0

The user selected displayed proposals 2 (Quantum Fabric), 3 (Sentient Atlas)
and 4 (Synaptic Cosmos) for packaging, and explicitly requested 4 as a laptop
experiment. This replaces the previous visual direction, without changing the
native centred Limine menu. Event Horizon remains available for rollback.

- Exact selected generated PNG bytes are preserved with hashes and full prompts
  in ai-artwork-provenance.json. Source dimensions are 1672 × 941, not native 4K.
- All three new themes render in real Limine 12.8 UEFI/QEMU at 1920×1080, using
  the real native entry titles from the target but nonexistent demo boot paths.
  Synaptic Cosmos also renders and navigates at 1024×768; 4:3 stretches the art.
- 69 tests pass: 65 transaction/comparison cases and four native-menu navigation
  regression cases. The transaction cases include 13 new theme-history checks:
  read-only switch plans, previous-theme restore, complete uninstall, bad reviewed
  hash, edited current/previous assets, config updates, interrupted writes before
  and after config/state commit, ancestor ownership and checkpoint corruption.
- Portable catalog/assets are verified; the existing GRUB packages also build.
  The selectable new catalog belongs to the Limine package; the GRUB target keeps
  its existing Event Horizon implementation.

The preview navigation derives the visible directory rows from the entry hierarchy,
checks native branding after each action and requires distinct menu/selection/
expanded-submenu screenshots. The real target has an initially expanded Omarchy
root: a kernel row must not be mistaken for the Snapshots directory. The four
regression cases cover expanded roots, flat demos, hidden children and missing
directories. VM entries use nonexistent boot paths and cannot prove a kernel boot.

## Approved Synaptic Cosmos experiment — 2026-10-16

The user selected displayed proposals 2–4 for the package and explicitly requested
proposal 4 on the laptop. The recovery approval and prior full backup were retained.
The authenticated switch from Event Horizon to Synaptic Cosmos passed host/version
and exact current-config guards. Independent privileged readback verified:

- Selected artwork and appearance hashes match the reviewed package.
- The complete native boot-entry section is byte-identical.
- Every other file in the prior ESP/config inventory and firmware entries is unchanged.
- The new transaction backup and its before/after hashes are valid; no pending journal.
- Event Horizon assets and the previous transaction checkpoint are retained and verified.

The 0.3.0 manager's restore action returns one checkpoint to Event Horizon;
uninstall unwinds both checkpoints to the original Omarchy appearance. Physical
rollback is not yet verified. The running boot ID remains unchanged: this verifies
the configured files, not the next hardware boot, display result or desktop return.
The user initiates the reboot. Public visibility and releases remain pending.
Private backups, full boot configuration and device identifiers remain excluded.


## Physical evidence and guided installer — 0.4.0

The user supplied a monitor photograph showing the native Synaptic Cosmos menu
and stated “testato e funziona perfettamente”. The photograph is directly observed;
the test result is user-reported. A fresh host read independently observed a new
boot ID and a running Omarchy kernel after the theme activation. The private photo,
boot IDs and identifying host report are excluded from GitHub. This supports a
real displayed themed menu and a subsequent running system, not independent
verification of every snapshot, cold/warm cycle, internal display or rollback.

The user explicitly requested completion of choice/preview for both bootloaders
before the authorized PR merge. Version 0.4.0 adds a Tk chooser with unprivileged
previews, an authenticated read-only plan and explicit reviewed application/restore.
Its source/package tests cover integrity, unsafe paths/symlinks, target mismatch,
UEFI partition mismatch, missing approvals/recovery, stale plans and UI confirmation
and selection changes. Native GRUB previews cover all three new artworks including
selection, submenu, console and scrolling; those entries remain demo-only.

The installer matrix and exact limitations are in [INSTALLER.md](INSTALLER.md).
The Limine manager and its runtime data are unchanged by the chooser. No theme was
reapplied to the working laptop to test the new interface. Public release remains
separate from merging the private implementation.

The final 0.4.0 suite passes 92 tests on isolated Debian Python 3.11/Tk/Xvfb.
The packaged chooser was opened and its GRUB/Limine previews switched without
requesting privileges or enabling application before a reviewed plan.
