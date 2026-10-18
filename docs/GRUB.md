# GRUB manager and Debian package

For interactive choice and previews use the [combined installer](INSTALLER.md).
The `.deb` and portable GRUB archive provide the manager CLI and all four themes.
They do not replace GRUB or add operating-system entries.

## Debian / Ubuntu

Download `dls-neon-grub_0.5.2_all.deb` and `SHA256SUMS` from
[Releases](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/tag/v0.5.2).
Verify the checksum in the download directory, then install:

```sh
sha256sum --check --ignore-missing SHA256SUMS
sudo apt install ./dls-neon-grub_0.5.2_all.deb
dls-neon-theme install --theme synaptic-cosmos --dry-run
```

Installing the `.deb` stages files under `/usr`; it does not activate the theme.
`--dry-run` describes the planned action and verifies the selected assets; it
does not provide the combined console's full host qualification/review workflow.
After verifying your independent backup, live USB and active GRUB layout:

```sh
sudo dls-neon-theme install --theme synaptic-cosmos --profile 1080p --timeout 8
sudo dls-neon-theme status
```

The manager defaults to `/boot/grub/grub.cfg`. A verified grub2 layout can use
`--config boot/grub2/grub.cfg` on the install command. The combined console
detects the layout automatically and is the recommended route if unsure.

## Portable GRUB archive

Download and verify `dls-neon-grub-0.5.2.tar.gz`, extract it and enter its directory:

```sh
tar -xzf dls-neon-grub-0.5.2.tar.gz
cd dls-neon-grub-0.5.2
./install.sh --theme synaptic-cosmos --dry-run
sudo ./install.sh --theme synaptic-cosmos --profile 1080p --timeout 8
sudo python3 dls-neon-theme status
```

The script uses the themes in the extracted archive. Native GRUB probe, path and
syntax-check tools are required on the host. It does not install a bootloader.

## Restore and remove

For the `.deb`, restore before removing the package:

```sh
sudo dls-neon-theme restore
sudo apt remove dls-neon-grub
```

For the archive: `sudo python3 dls-neon-theme restore` from its directory.
Restore before changing to another GRUB theme. Backups and recovery assets are
retained. If there were later kernel/config updates, follow [RECOVERY.md](RECOVERY.md)
instead of copying an obsolete `grub.cfg` over current entries.
