# Validation scope

## What has been checked

- Transaction, integrity, interrupted-write, concurrent-change and conservative
  restore tests for both managers; console browsing/cancellation/confirmation.
- Byte preservation for Windows, macOS/OpenCore, other Linux and custom menu
  fixtures, including dynamic GRUB BLS source handling.
- Native GRUB UEFI rendering in isolated QEMU/OVMF at 720p, 1080p, 1440p, 4K and
  fallback 1024×768. AI collection captures include selection, submenus, console
  and scrolling at 1080p. The 0.5 preview also checks a mode switch from 1024×768.
- Real GRUB parser checks, filesystem UUID and GRUB-relative asset paths, literal
  appearance-only generator output, backup/config permissions and legacy restore.
- Debian isolated builds and GitHub Actions for packaging, tests and native
  bootloader previews. See [Actions](https://github.com/DreamLab-Solutions/dls-neon-grub/actions)
  and the [first GRUB run](https://github.com/DreamLab-Solutions/dls-neon-grub/actions/runs/38157482076).
- Limine and physical Omarchy scope is recorded in
  [VALIDATION-OMARCHY.md](VALIDATION-OMARCHY.md).

Screenshot evidence JSON files in `screenshots/` retain image hashes, resolutions
and test scope. Test VMs use disposable media, no host disks and no VM network.
Demo entries point to nonexistent OS paths: screenshots prove rendering and
navigation, not kernel boot. Personal hardware photos and system backups stay
outside this repository and its packages.

## Hardware scope and open qualification

Synaptic Cosmos on the existing Omarchy/Limine installation was reported working
by the user. A monitor photo was inspected and a changed boot ID/running Omarchy
kernel was read independently. Separate cold/restart cycles, internal/external
display combinations, physical rollback and Ubuntu/GRUB hardware installation
remain unqualified. Windows/macOS/other-Linux physical boot is not certified.

The historical Ubuntu 0.1 activation stopped before replacing `grub.cfg` when an
OS-prober label changed after disk renumbering. Later fixtures covered that case;
0.5 activation now avoids regenerating entries entirely. Earlier Ubuntu host
inspection does not qualify the later Omarchy installation.

Version 0.5.1 changes documentation and release packaging, not the installer
transaction or existing artwork. Its release checks verify archive contents,
manifests, documentation links and checksums alongside the existing test suite.
The earlier physical boot observation is not a new hardware test of this package.
