# Installation

Use the combined archive for an interactive terminal workflow on GRUB or Limine.
For a manager-only installation, use the [GRUB](GRUB.md) or [Limine](OMARCHY.md)
guide. Check [compatibility](COMPATIBILITY.md) before applying a theme.

## 1. Download and verify

Open [Releases](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/tag/v0.5.2)
and download `dls-neon-setup-0.5.2.tar.gz` and `SHA256SUMS` from **Assets**.
Do not use the automatic Source code download as an installer. Release assets
are available from this public repository without signing in.

From the download directory:

```sh
sha256sum --check --ignore-missing SHA256SUMS
tar -xzf dls-neon-setup-0.5.2.tar.gz
cd dls-neon-setup-0.5.2
python3 dls-neon-setup
```

The checksum command must report `dls-neon-setup-0.5.2.tar.gz: OK`.
If you prefer GitHub CLI, download the same assets with:

```sh
gh release download v0.5.2 --repo DreamLab-Solutions/dls-neon-bootloaders \
  --pattern 'dls-neon-setup-0.5.2.tar.gz' --pattern SHA256SUMS
```

## 2. Check prerequisites

Run from the installed Linux system, booted in x86-64 UEFI mode through the
bootloader you intend to theme. You need Python 3.11+, sudo, efibootmgr and
util-linux (`findmnt`, `lsblk`). GRUB also needs `grub-script-check`, `grub-probe`
and `grub-mkrelpath`, or their `grub2-*` equivalents. Keep the existing bootloader;
use your distribution's packages to supply missing inspection utilities.

Image previews use `xdg-open` when available. Otherwise the console prints a PNG
path you can open yourself. Browsing needs no root, Tk, Polkit, Docker, QEMU or
network connection. A successful preview does not qualify the host boot layout.

Before applying, verify a backup on independent media and boot-test a suitable
UEFI live USB. For encrypted root, confirm that you can unlock it from that USB.
Keep recovery material and saved system inventory private. Avoid kernel,
bootloader and snapshot updates while inspecting or applying the theme.

## 3. Choose, preview and review

Start `python3 dls-neon-setup` as your normal user. The console opens with
Synaptic Cosmos selected. Its current prompts are in Italian; the keys below
are the same in every environment.

| Key | Action |
| --- | --- |
| **1**, **2**, **3**, **4** | Select Event Horizon, Quantum Fabric, Sentient Atlas or Synaptic Cosmos. |
| **p** | Open the selected image with the native bootloader menu. |
| **b** | Switch the preview between GRUB and Limine; this does not change the host target. |
| **d** | Inspect the active UEFI entry to detect the actual bootloader. Requires sudo. |
| **v** | Read and validate the host plan; list the existing entries to retain. Requires sudo. |
| **o** | Choose GRUB typography/resolution profile and a 1–60 second timeout. |
| **a** | Apply the reviewed plan after separate recovery and write confirmations. |
| **r** | Restore the previous appearance checkpoint after a fresh plan and confirmation. |
| **q** | Exit. |

For GRUB the default is the 1080p profile and an 8-second visible menu. Limine
keeps its current resolution, default entry and timeout. A Limine installation
whose menu is hidden needs a separate reviewed visibility change.

## 4. Apply explicitly

Press **v**, read the proposed target, selected theme, settings and entry list.
Press **a** only after that review. At the recovery question `[s/N]`, enter **s**
(Italian for yes) only if the independent backup and live USB are verified.
Then type **APPLICA** exactly. Cancellation leaves the boot files untouched.
Sudo is requested for the privileged operation, not for opening the console.

The installer verifies bundle integrity, the active EFI target and the exact
reviewed configuration before writing. It retains a transaction backup and
checks the resulting files. A changed plan or unsupported layout stops writes;
you can still browse images. Never disable the guards to force installation.

No reboot is performed. Save your work, reboot yourself and check the actual
menu, chosen Linux boot and desktop return. File verification alone is not a
successful reboot test.

## Change theme or remove it

GRUB: use **v**, then **r**, confirm **s** and **RIPRISTINA**. Review and apply
the new theme after restoring. GRUB deliberately requires that extra restore.

Limine: applying a new theme creates another checkpoint. **r** restores one
checkpoint. To unwind all checkpoints, use the dedicated manager's `uninstall`
command described in [OMARCHY.md](OMARCHY.md).

Keep the extracted tools and backups until restore is complete. If a later
kernel or administrator change causes a conflict, follow [RECOVERY.md](RECOVERY.md)
instead of replacing the whole configuration with an old backup.

## Existing Windows, macOS or other Linux installations

Existing entries are retained, including custom entries, submenus, snapshots and
dynamic GRUB BLS sources. The installer does not run OS discovery, rewrite BCD,
OpenCore, BitLocker/FileVault settings, or add entries for another disk. Missing
entries need a separate bootloader/firmware configuration task. Entry preservation
does not certify that the corresponding operating system boots on your hardware.
