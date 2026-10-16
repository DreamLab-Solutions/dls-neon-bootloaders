# Compatibility

The combined installer detects the bootloader from the **active UEFI firmware
entry**. A distribution name, installed package or operating-system menu label
is not sufficient to establish compatibility.

| Target | Supported conditions | Evidence and limits |
| --- | --- | --- |
| GRUB on Debian/Ubuntu | Active x86-64 UEFI GRUB/shim; unambiguous `/boot/grub/grub.cfg` or `/boot/grub2/grub.cfg`; matching mounted FAT ESP; native GRUB tools and `/etc/grub.d`. | Real GRUB UEFI rendering in VM, Debian build/tests. Physical Ubuntu activation/recovery is not qualified. |
| GRUB on other Linux distributions | Same technical layout; `grub-*` and `grub2-*` utilities; vendor EFI paths and BLS source preservation. | Covered by software fixtures, not a hardware support claim for every distribution. |
| Limine on Omarchy | Active x86-64 UEFI Limine **12.8.0**, exact qualified binary/path, writable FAT ESP at `/boot`, `/boot/limine.conf`, Secure Boot disabled. | Native rendering in VM; user-reported successful Synaptic Cosmos boot on the existing Omarchy installation. |
| Limine on other Linux distributions | Same qualified binary and layout; no distro or pacman requirement. | Technical guard and fixture coverage; physical boot not qualified. |
| Other Limine versions/layouts | Requalification required. | Writes are refused; previews remain available. |
| BIOS/legacy boot, ARM, systemd-boot, rEFInd | Outside the combined installer's supported target. | No automatic conversion or migration. |
| Native Windows Boot Manager / Apple boot screen | Not a theme target. | Existing chainload entries inside GRUB/Limine are preserved. |

## Qualified Limine binary

Path: `/EFI/limine/limine_x64.efi` on the ESP mounted at `/boot`.
SHA-256 of the accepted EFI binary:

```text
3fe0de87c13a12998b3c785b0c57ddfbcd6fc57251c1b0628604583ec8e9a5ff
```

A bootloader update can invalidate this qualification. The installer stops
rather than silently accepting a different build. Do not turn Secure Boot off
or replace an EFI binary merely to make this theme installer pass.

## Appearance and displays

GRUB offers 720p, 1080p, 1440p and 4K layout/font profiles. The firmware must
actually provide the requested mode. At 1024×768 use the compact 720p profile;
long entries can otherwise be truncated. The source artwork is 1672×941, not a
native 4K master. A 4:3 mode stretches the 16:9 composition.

Limine keeps its native menu, bitmap typography and current video settings.
Its menu cannot reproduce GRUB's positioned widgets or PF2 fonts. Choose one
of the three central compositions if the original Event Horizon feels off-centre.

## Multiboot, encryption and updates

Windows, macOS/OpenCore, other Linux, recovery and custom menu entries do not
block installation merely because they are present. GRUB retains every original
configuration byte and appends graphics; Limine retains its complete entry
section. A theme does not add missing entries or qualify other operating-system
boots, Secure Boot chains, BitLocker, FileVault or third-party loader behavior.

Encrypted root and separate `/boot`/Btrfs layouts require working native path
resolution and recovery access. Never alter encryption to install artwork.
Distribution updates retain ownership of kernel and snapshot entries. Later
config changes can cause restore conflicts; see [recovery](RECOVERY.md).
