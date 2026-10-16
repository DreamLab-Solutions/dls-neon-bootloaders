# Limine manager and Omarchy

Use the [combined installer](INSTALLER.md) for guided image choice and previews.
This page covers the dedicated `dls-neon-limine-0.5.2.tar.gz` archive and its CLI.
It contains all four themes, a backup helper and documentation. It does not
install Limine or GRUB. Check the exact supported layout in
[COMPATIBILITY.md](COMPATIBILITY.md).

## Download, inspect and back up

Download the dedicated archive and `SHA256SUMS` from
[Releases](https://github.com/DreamLab-Solutions/dls-neon-grub/releases/tag/v0.5.2).
In the download directory:

```sh
sha256sum --check --ignore-missing SHA256SUMS
tar -xzf dls-neon-limine-0.5.2.tar.gz
cd dls-neon-limine-0.5.2
python3 dls-neon-limine themes
sudo python3 dls-neon-limine inspect
sudo python3 dls-neon-limine plan --theme synaptic-cosmos
```

`inspect` and `plan` read the host without writing boot files. Keep the report
private. Review the exact appearance diff and the printed **Baseline SHA256**.
Default entry, timeout, kernel arguments and snapshot entries are retained.

The helper below copies the ESP and relevant config into a **new**, absolute
directory outside `/boot`, rereads every archived file and compares it with its
source. Replace the example path with your chosen backup location:

```sh
sudo python3 backup-read-only.py /absolute/path/new-limine-backup
```

Copy that backup to independent media and verify its checksum there. Boot-test a
UEFI Arch/Omarchy rescue USB, including access to encrypted root and the backup.
The helper cannot verify that independent copy or your live USB on your behalf.

## Apply and switch

Only after review and recovery preparation, paste the 64-character baseline
hash from your own plan in place of `HASH_FROM_PLAN`:

```sh
sudo python3 dls-neon-limine install --theme synaptic-cosmos \
  --expected-config-sha256 HASH_FROM_PLAN --approve-boot-write
sudo python3 dls-neon-limine status
```

The explicit flag authorizes this boot-file write. The qualified EFI build/path,
Secure Boot state and current config are checked again. No reboot is performed.

For another theme, first use `plan --theme quantum-fabric --replace`, review the
new hash, then use `switch --theme quantum-fabric` with the same two approval/hash
options. Each switch retains the prior appearance as a checkpoint. A theme already
in retained history must be reached through restore rather than overwritten.

## Restore and uninstall

```sh
sudo python3 dls-neon-limine restore --approve-boot-write
```

This undoes one checkpoint. To unwind every checkpoint back to the original
appearance:

```sh
sudo python3 dls-neon-limine uninstall --approve-boot-write
```

Backups remain under `/var/lib/dls-neon-limine/backup-*`. Keep the tool and owned
assets until recovery is complete. Changed kernel/snapshot entries or modified
assets stop automatic restore; follow [RECOVERY.md](RECOVERY.md).

## Omarchy-specific behavior

Omarchy `refresh limine` can overwrite configuration and invoke update tools.
It is not this theme's installer or rollback command. Package/reset operations
can change `limine.conf`; the manager deliberately refuses stale restoration.
Do not apply while kernel/snapshot updates are running. The adapter does not
invoke `limine-update`, change firmware order, replace EFI binaries, or change
kernel command lines, UKIs, default entries or timeout.

The current guard no longer requires Omarchy, pacman or a firmware label named
Limine. It still requires the **exact qualified 12.8.0 binary and path**. A
successful test on one Omarchy installation is not blanket support for every
Limine system. See [validation scope](VALIDATION-OMARCHY.md).
