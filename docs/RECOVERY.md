# Restore, removal and recovery

Keep the extracted installer, transaction backup, release checksum and a verified
independent copy until you have completed both boot and restore checks. Have a
boot-tested UEFI live USB and access to any encrypted root filesystem.

## The system still boots

For the combined installer, run `python3 dls-neon-setup`, press **v**, then **r**.
Review the plan, confirm recovery readiness with **s**, then type **RIPRISTINA**.

For the GRUB manager installed by the `.deb`:

```sh
sudo dls-neon-theme status
sudo dls-neon-theme restore
```

For a dedicated archive, run the corresponding manager from its extracted folder:

```sh
sudo python3 dls-neon-theme restore
```

or, for Limine:

```sh
sudo python3 dls-neon-limine status
sudo python3 dls-neon-limine restore --approve-boot-write
```

GRUB restores its pre-theme appearance before a new theme can be applied. Limine
restore undoes one checkpoint; `uninstall --approve-boot-write` unwinds all
checkpoints. After a successful GRUB restore, `sudo apt remove dls-neon-grub`
can remove a Debian package installation. Retained backup/assets are deliberate.

## Automatic restore reports a conflict

Stop and inspect the current file and saved before/after hashes. A later kernel,
snapshot, package update or administrator edit can make a whole-file restore
unsafe. Do not force-copy an old config over new entries.

| Manager | State and retained backup | Owned appearance files |
| --- | --- | --- |
| GRUB | `/var/lib/dls-neon-grub/active.json`, `backups/*/grub.cfg`, `backups/*/transaction.json` | Marked graphics block at the end of the active `grub.cfg`; `/etc/grub.d/99_dls_neon_theme`; dedicated theme directory. |
| Limine | `/var/lib/dls-neon-limine/active.json`, `pending.json`, `backup-*/before.conf`, `after.conf`, metadata | Marked graphics block before the entries in `/boot/limine.conf`; `/boot/dls-neon-limine/<hash>`. |

Compare the live configuration with its saved baseline and candidate. An
administrator can remove only the DLS graphics block and unchanged owned GRUB
hook, or reinstate Limine's saved appearance keys, **while retaining every current
boot entry, kernel path, security option, default and timeout**. Keep copies and
review a diff before any manual write. Use native syntax checks where available.
The automatic manager refuses this merge rather than guessing it.

Legacy GRUB 0.4 and earlier records may own
`/etc/default/grub.d/99-dls-neon.cfg` instead of the generator hook. The current
manager understands those records when unchanged. A conflict needs review of
that recorded drop-in; do not run a generic old `update-grub` recipe as a theme
rollback or discard the record to bypass checks.

## Menu graphics are unreadable

In GRUB, try **c**, enter `terminal_output console`, then press **Esc** to return
to the text menu. If the keyboard/menu is unusable, boot the trusted live USB.
For Limine, use the live USB if the native menu cannot be used.

## Recover from a live USB

1. Boot the USB in UEFI mode. Identify the installed root and ESP by UUID using
   `lsblk -f` and your saved inventory; device names can change. Do not format.
2. Unlock encrypted root using your own recovery credentials, mount the correct
   root/subvolume, then mount any separate `/boot` and ESP in their installed layout.
3. Read the retained transaction and verify its backup hashes. If the installed
   config still exactly matches the recorded candidate, restore the verified
   original config and recorded appearance state. If entries changed, perform
   the appearance-only review above instead.
4. Retain recovery assets and backups, unmount cleanly and reboot when ready.

The USB's active EFI entry identifies the USB, so do not run the normal installed
host guard there and interpret its target as the laptop's installed bootloader.
Mount/unlock commands depend on the saved partition and subvolume layout; there
is no safe universal device-name recipe. Removing this theme does not require
reinstalling GRUB/Limine, changing NVRAM or replacing an EFI executable.

## Interrupted activation

Preserve the transaction/journal and owned files. Use `status`, compare current
hashes with the retained baseline/candidate and follow the relevant restore path.
Do not delete backups, active records or a pending journal merely to retry.
The tool does not lock distribution update services or protect against every
power-loss timing; independent recovery remains necessary.
