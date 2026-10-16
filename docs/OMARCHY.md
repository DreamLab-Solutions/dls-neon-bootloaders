# DreamLab AI universe themes for Omarchy / Limine — 0.4.0

This is a native Limine appearance adapter. It keeps the GRUB implementation
available as a separate target. It does not install GRUB, replace Limine,
change partitions, EFI executables, firmware variables, UKIs, kernel arguments,
default entries, timeout or snapshot integration. Do not run the GRUB install.sh
on Omarchy. Limine cannot reproduce GRUB's free-positioned boot_menu or PF2
fonts: expect the native Limine menu over the selected background.

## Compatibility

Initial activation guard: UEFI x86-64 Omarchy, pacman Limine 12.8.0, writable
FAT ESP mounted at `/boot`, active firmware entry named Limine using the qualified `/EFI/limine/limine_x64.efi`
binary (SHA256 recorded in screenshot evidence), Secure Boot
disabled and readable configuration. Other versions require requalification;
never disable Secure Boot to get a passing result. The guard is a prerequisite,
not evidence of a successful hardware installation. Snapper and UKI entries
remain byte-for-byte distribution-owned. No hook invokes limine-update.

See [the verified porting evidence](VALIDATION-OMARCHY.md) in the repository.
Before each activation, inspect the exact live configuration, default/timeout
and available video mode with privileged read-only operations. Omarchy `refresh limine` overwrites the
config and invokes update tools; do not use it as a theme installer or rollback.
Use it only under a separately reviewed recovery plan. An Omarchy update/reset
may change this file: automatic restoration deliberately refuses such conflicts.

## Build and review

From the repository: `python3 scripts/limine_build.py`. Python 3 standard library
only; the original wallpaper is copied, not regenerated. The archive includes
checksums and does not execute anything on extraction. Verify its external
checksum before extracting: `sha256sum -c SHA256SUMS-limine` in dist.

Run `sudo python3 dls-neon-limine inspect` for a read-only summary of real entry
titles, default/timeout and EFI file names (keep this system report private).

In the extracted folder, `python3 dls-neon-limine plan` prints the exact proposed
diff and writes nothing. Reading `/boot` may require `sudo`; even a privileged
plan remains read-only. No default or timeout change is included; if the menu is
hidden, propose and approve visibility separately before activation.

For a full read-only backup of ESP/config to a new directory outside the ESP,
use `sudo python3 backup-read-only.py /absolute/path/new-backup`. The archive
is reread and compared to its source files; keep it private and verify a copy
on independent media. This is separate from the installer transaction backup.

Only after review, backup and usable live USB, activate explicitly:
`sudo python3 dls-neon-limine install --approve-boot-write --expected-config-sha256 HASH_FROM_PLAN`.
This creates a verified before/after backup and journal in
`/var/lib/dls-neon-limine/backup-UUID`, stages only its owned assets in
`/boot/dls-neon-limine/HASH`, checks concurrent modification and replaces the
appearance config. Root backup directory is mode 0700. Read back the config,
asset hashes and unchanged entry section before reboot. Copy the backup and
release checksum to a separate recovery medium and verify the copied hashes.
No script restarts the machine. The user initiates the reboot after approval.

`sudo python3 dls-neon-limine status` reports the active/interrupted transaction.
`sudo python3 dls-neon-limine restore --approve-boot-write` restores the exact
previous appearance checkpoint and removes only its unchanged owned assets.
`uninstall` unwinds all theme checkpoints back to the original Omarchy appearance.
Backups are retained. Restore before deleting the extracted tool. Do not remove
the runtime artwork while the configuration references it.

## Transaction failures and conflicts

A pending journal survives a failed activation. Run status, inspect the backed-up
before/after hashes and current file. Restore accepts only the exact original or
candidate config. It rejects edited/corrupt assets or backups, and any later
kernel/snapshot/admin config change. This avoids restoring obsolete boot entries.
It uses an advisory application lock; distribution update tools do not share it.
Do not activate during kernel/package/snapshot operations. Concurrent writes in
the last read/replace interval and sudden power loss cannot be ruled out by this
tool: use a recovery USB and complete physical recovery testing before release.

If a later update changed the entries, never force-copy the whole old config.
Review the current file alongside before.conf and after.conf; remove only the
DLS marked appearance block, reinstate the saved original appearance options,
and retain all current entries, UKI paths, command lines, security/default/timeout
settings. Inspect a diff with an administrator and revalidate paths before
replacement. The automatic tool stops instead of guessing such a merge.

## Recovery from a trusted live USB

Before activation: boot-test a current Arch/Omarchy rescue USB in UEFI mode;
verify keyboard, ability to unlock your LUKS volume with your passphrase and
read the independent backup. Do not store the passphrase in a report. Identify
partitions by UUID; device names can change. Have firmware boot-menu access.

If the themed menu is unusable, boot that USB. Use `lsblk -f` and the saved
inventory to identify the Omarchy ESP and encrypted root; do not format anything.
Open the LUKS root, mount Btrfs subvolume `@` under `/mnt`, then mount its ESP at
`/mnt/boot`. Check before/after SHA256 values in the retained backup under
`/mnt/var/lib/dls-neon-limine`. If current config equals the candidate and the
backup hash matches, restore before.conf to `/mnt/boot/limine.conf`; verify byte
identity and retain assets until a successful boot. If entries changed, follow
the appearance-only conflict procedure above. Unmount and close the LUKS mapping
cleanly before the user reboots. No bootloader reinstall, NVRAM edit or EFI
binary replacement is required for a theme rollback. Do not run the normal host
guard from a live USB: BootCurrent there identifies the USB, not installed Limine.
Exact device-specific commands are to be prepared only after privileged discovery
and independent backup verification; this plan is not a claim recovery was tested.

## Release gates

Portable package, failure tests and isolated real-Limine rendering must pass.
Physical activation, cold boot, restart, desktop return, actual video mode,
snapshot menu, other OS selection and rollback must be verified separately.
Record failures and unsupported modes honestly. At 1024x768 the 16:9 source
wallpaper is stretched to 4:3; this is a functional fallback, not a faithful
artwork composition. 4K and physical display modes remain untested. Do not call a screenshot VM a
successful Omarchy kernel boot. Review reference-image redistribution clearance,
public owner/name and clean screenshots before changing repository visibility.
Do not publish UUIDs, disk serials, raw boot configs, backup content or local reports.

## Select and switch themes — 0.3.0

`python3 dls-neon-limine themes` lists the packaged themes. The new collection
contains Quantum Fabric (displayed proposal 2), Sentient Atlas (3), and Synaptic
Cosmos (4). Event Horizon is retained for existing users and rollback; proposal
1, Neural Observatory, is not included. Extraction/package installation never
selects or activates a theme. With no explicit theme, data/ retains Event Horizon.

Fresh activation of a chosen theme:
`sudo python3 dls-neon-limine plan --theme synaptic-cosmos`
then, only after approval and recovery checks:
`sudo python3 dls-neon-limine install --theme synaptic-cosmos --approve-boot-write --expected-config-sha256 HASH_FROM_PLAN`.

For an already managed theme, review:
`sudo python3 dls-neon-limine plan --replace --theme synaptic-cosmos`
then apply the approved switch:
`sudo python3 dls-neon-limine switch --theme synaptic-cosmos --approve-boot-write --expected-config-sha256 HASH_FROM_PLAN`.

A switch retains the prior active record and its assets as a checkpoint.
`restore` undoes one theme activation/switch. After Event Horizon → Synaptic
Cosmos, one restore returns to Event Horizon; a second returns to original
Omarchy. `uninstall` unwinds the whole chain, retaining backups. Use the 0.3.0 or later
manager for this history, not a portable copy of the earlier 0.2.0 tool.
An already retained ancestor theme is restored with restore rather than claiming
its existing asset directory again. Switching refuses modified configs/assets,
wrong reviewed hashes and interrupted transactions. A failed switch is recovered
from its pending journal before considering the old active record.

In the repository build all theme data with `python3 scripts/limine_build.py`.
To use repository scripts, add `--source build/limine` before `--theme SLUG`.
The current experiment uses Synaptic Cosmos; this is not a claim of a successful
hardware reboot. Review the actual Limine VM screenshot before applying it.
