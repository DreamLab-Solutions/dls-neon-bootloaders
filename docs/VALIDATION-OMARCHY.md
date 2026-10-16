# Omarchy / Limine validation

## Qualified environment

The original port target was Omarchy 4.0.4, x86-64 UEFI, Btrfs root on LUKS2,
with a separate FAT ESP mounted at `/boot`. The active EFI entry used the
qualified Limine 12.8.0 binary. Its exact path/hash and current installer limits
are listed in [COMPATIBILITY.md](COMPATIBILITY.md).

The original configuration contained Omarchy, its kernel and two snapshots.
Ubuntu had a firmware entry on another disk but was absent from the actual
Limine menu. Automatic bootloader discovery being enabled was not proof that
Ubuntu had been imported or could boot. The theme did not add that missing entry.

Privileged read-only discovery and a verified local ESP/config backup preceded
the appearance activation. The user confirmed an independent backup and tested
recovery media, then explicitly approved activation. Recovery readiness was
user-reported; copying/mounting from the live USB was not observed by the agent.

## Rendering and transactions

Real Limine 12.8.0 UEFI captures were produced in QEMU/OVMF at 1920×1080,
1280×720 and 1024×768 on disposable media, without host disks or VM networking.
All four themes have native menu captures; selection/submenu and Synaptic Cosmos
fallback captures are preserved in `screenshots/` with adjacent evidence JSON.
The [gallery](THEMES.md) displays the main screenshots.

The upstream test archive is pinned to v12.8.0 with SHA-256
`e21b0a9ce1cf83e79eb0f3fa6d6de49a1b6d1288df11e2232e41c9f4916b673d`.
Tests cover appearance-only diffs, complete entry-section preservation, verified
backup, switch history, interrupted journals, stale configuration, corrupt assets,
symlinks, traversal, concurrent modification, locking and platform guards.

## Physical result

The user selected Synaptic Cosmos for the laptop experiment and reported a
successful real boot. The supplied monitor photo was inspected; a new boot ID
and running Omarchy kernel were read independently afterward. This supports the
observed appearance and user-reported boot on that installation. It does not
prove separate cold/restart cycles, physical rollback, another display or boot
of another operating system.

The 0.4/0.5 selector and later documentation/release work did not reapply the
theme to laptop boot files. Existing evidence must not be relabelled as hardware
qualification of every later package. No automatic reboot, EFI replacement,
NVRAM change or bootloader migration was performed.

## Current limits

Limine keeps its centred native menu and bitmap typography. 4:3 modes stretch
the source composition. Other EFI builds or mount layouts need requalification.
Omarchy reset/kernel/snapshot updates can alter configuration and stop automatic
restore. See [OMARCHY.md](OMARCHY.md) and [RECOVERY.md](RECOVERY.md).

Runtime packages exclude private configs/backups, the hardware photo and the
original concept reference. Repository visibility still needs separate reference
clearance because excluded files can remain in Git history.
