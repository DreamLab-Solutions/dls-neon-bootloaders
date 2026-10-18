# DLS Neon Bootloaders · DreamLab Boot Themes

Four space and AI inspired themes for **GRUB** and **Limine**, with an interactive
terminal installer, image previews, verified backups and conservative restore.
Teal, purple and acid yellow `#D9FF00` are the DreamLab palette.

[Download v0.5.2 preview](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/tag/v0.5.2)
· [Installation](docs/INSTALLER.md) · [Theme gallery](docs/THEMES.md)
· [Compatibility](docs/COMPATIBILITY.md) · [Changelog](docs/CHANGELOG.md)
· [Italiano](docs/it/README.md)

![Synaptic Cosmos running in native Limine at 1920 × 1080](docs/screenshots/limine-synaptic-cosmos-1080p.png)

*Synaptic Cosmos in the real Limine UEFI renderer, captured in an isolated VM.
Menu entries are demonstrations; the screenshot is not an OS boot test.*

## Before you start

This package changes the appearance of an **existing** bootloader. Run it from
the installed Linux system you want to theme, booted through that loader.

| Target | Requirements |
| --- | --- |
| GRUB | Linux x86-64 UEFI; a supported GRUB/shim layout, mounted FAT EFI System Partition and native `grub-script-check`, `grub-probe`, `grub-mkrelpath` tools (or `grub2-*` equivalents). |
| Limine | Linux x86-64 UEFI; the exact qualified **12.8.0** EFI binary and layout, ESP mounted at `/boot`, `/boot/limine.conf` and Secure Boot already disabled. |
| Both | Python **3.11+**, sudo, `efibootmgr`, util-linux (`findmnt`, `lsblk`), plus a verified independent backup and a boot-tested UEFI live USB. |

Check `python3 --version` and the [compatibility matrix](docs/COMPATIBILITY.md),
including the accepted Limine binary hash, before applying. Updated Limine builds
need requalification. BIOS/legacy boot, ARM, systemd-boot, rEFInd and native
Windows/Apple boot screens are outside this installer's supported targets.
Keep your current bootloader and security settings; do not replace or downgrade
them to make a theme pass qualification.

`xdg-open` is optional for opening previews. **Docker is only for development**;
the installer needs no QEMU, Tk, Polkit or Python packages from pip.

## Install: recommended combined package

Use the **combined installer** for guided theme choice and previews on either
supported bootloader. Download these two assets from the release page:

- [`dls-neon-setup-0.5.2.tar.gz`](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/download/v0.5.2/dls-neon-setup-0.5.2.tar.gz)
- [`SHA256SUMS`](https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/download/v0.5.2/SHA256SUMS)

Download them in your browser, or run these commands in an empty download directory:

```sh
curl --fail --location --remote-name https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/download/v0.5.2/dls-neon-setup-0.5.2.tar.gz
curl --fail --location --remote-name https://github.com/DreamLab-Solutions/dls-neon-bootloaders/releases/download/v0.5.2/SHA256SUMS
```

With both files in the same directory, verify the archive **before extracting**:

```sh
sha256sum --check --ignore-missing SHA256SUMS
```

The result must include `dls-neon-setup-0.5.2.tar.gz: OK`. If verification fails
or that archive is missing, stop and download both files again. Then:

```sh
tar -xzf dls-neon-setup-0.5.2.tar.gz
cd dls-neon-setup-0.5.2
python3 dls-neon-setup
```

Run the console as your **normal user**. It requests sudo for system inspection
and separately confirmed writes. The default selection is Synaptic Cosmos.

| Key | What to do |
| --- | --- |
| **1–4** | Select a theme from the collection below. |
| **p** / **b** | Open the preview / switch its GRUB or Limine renderer. This does not change the installed bootloader. |
| **d** | Detect the active bootloader; administrative read access is requested. |
| **o** | Optional GRUB settings: `720p`, `1080p`, `1440p` or `4k`, and a 1–60 second timeout. |
| **v** | Review the actual host plan, selected theme, target and preserved entries. |
| **a** | Apply that reviewed plan after recovery and write confirmations. |
| **r** | Restore the previous appearance checkpoint after reviewing a fresh plan. |
| **q** | Exit without further operations. |

The console currently uses **Italian prompts**: enter **s** at `[s/N]` only when
your independent backup and live USB are verified, then type **APPLICA** to
apply or **RIPRISTINA** to restore. GRUB defaults to a 1080p profile and an
8-second visible menu. Limine retains its current resolution, default and timeout;
an already hidden Limine menu remains hidden.

The installer does not reboot. After a successful write, save your work and
reboot yourself to verify the menu, your chosen OS and desktop return. Keep the
extracted installer and backups until boot and restore checks are complete.
See the [step-by-step installation guide](docs/INSTALLER.md) for the full workflow.

## CLI examples: inspect before applying

From the extracted **combined package** directory:

```sh
python3 dls-neon-setup --help
sudo python3 dls-neon-setup detect
```

Detection reads the active UEFI entry. If it reports GRUB, generate a read-only
plan, for example:

```sh
sudo python3 dls-neon-setup plan --backend grub --theme synaptic-cosmos \
  --profile 1080p --timeout 8
```

For a qualified Limine target instead:

```sh
sudo python3 dls-neon-setup plan --backend limine --theme quantum-fabric
```

`--backend` must match the detected loader. Plans include `can_apply`,
`can_restore`, refusal reasons and a `review_sha256` bound to the exact host and
selection. These examples do not write boot files. Use the interactive console
to apply, or follow the [guarded CLI procedure](docs/AI-INSTALL.md) with the actual
review hash and explicit approval. Never force an unsupported target.

## Restore, switch themes or remove

From the extracted combined package, run `python3 dls-neon-setup`, press **v**
for a fresh plan, then **r**, **s** and **RIPRISTINA** when appropriate.

- **GRUB:** restore the current theme before reviewing and applying another.
  If installed through the `.deb`, restore before `sudo apt remove dls-neon-grub`.
- **Limine:** applying another theme creates a checkpoint; restore undoes one
  checkpoint. The dedicated manager's `uninstall --approve-boot-write` unwinds
  them all; follow the [Limine guide](docs/OMARCHY.md).

Later kernel, snapshot or administrator changes can cause a restore conflict.
Keep the backup and follow [recovery and removal](docs/RECOVERY.md), including the
live-USB procedure, rather than overwriting current boot entries with an old file.

## Install with an AI agent

Give this prompt to an agent with terminal access **on the computer to theme**:

```text
Help me install DreamLab Boot Themes from https://github.com/DreamLab-Solutions/dls-neon-bootloaders.
Read docs/AI-INSTALL.md. Inspect my active bootloader read-only, show the four
themes, download the matching release and verify its checksum. Review the exact
host plan and recovery readiness with me, then apply only after my explicit
approval. Preserve all OS entries and the current bootloader. Never upload my
inventory/backups, bypass guards or reboot automatically.
```

With Codex CLI already installed and signed in:

```sh
codex 'Help me install DreamLab Boot Themes from https://github.com/DreamLab-Solutions/dls-neon-bootloaders. Read docs/AI-INSTALL.md, inspect first, show previews and the exact plan, and obtain my explicit approval before boot-file writes. Preserve all OS entries and never reboot automatically.'
```

The agent handles downloads, verification, inspection and approved installation.
You still choose the theme, approve boot writes and verify your recovery media.
See the [agent installation procedure](docs/AI-INSTALL.md) for the guarded CLI.


## Choose your package

| Release asset | Who it is for |
| --- | --- |
| `dls-neon-setup-0.5.2.tar.gz` | Recommended: terminal chooser, all four themes and GRUB/Limine previews. |
| `dls-neon-grub_0.5.2_all.deb` | Debian/Ubuntu GRUB users who prefer the manager CLI; package installation only stages files. |
| `dls-neon-grub-0.5.2.tar.gz` | Portable GRUB manager and themes; manual CLI workflow. |
| `dls-neon-limine-0.5.2.tar.gz` | Dedicated Limine manager, themes and backup helper; manual CLI workflow. |
| `SHA256SUMS` | SHA-256 checksums for all four downloadable packages. |

The `.deb` and dedicated archives do not include the interactive chooser.
GitHub's automatically generated **Source code** archives are for contributors;
they are not the ready-to-run installer. Previews are included in the combined
archive and work offline. Docker images, QEMU, firmware, bootloader binaries and
personal backup/configuration reports are not runtime downloads.

This is a **preview release** with the hardware limits described below.
The repository now covers both loaders; existing package and command names stay
loader-specific. The v0.5.2 downloads are preserved unchanged from the repository
move. Their embedded guides may refer to the previous repository name; use the
current online guides here for working links. Installation commands are unchanged.

## Themes

| Choice | Theme | Composition |
| --- | --- | --- |
| 1 | Event Horizon | Original portal artwork; left-aligned GRUB menu. |
| 2 | Quantum Fabric | Technological fabric with a dark central menu area. |
| 3 | Sentient Atlas | AI and cosmic structures framing the central menu. |
| 4 | Synaptic Cosmos | Teal/purple neural universe; default console selection. |

See [all four themes in both bootloaders](docs/THEMES.md). GRUB and Limine retain
their own native interface and typography; the same background produces different
menu layouts.

## Compatibility and multiboot

The combined installer qualifies the **active bootloader**, not the distribution
name. Standard GRUB/grub2 layouts are supported; Limine is restricted to the exact
qualified **12.8.0** EFI build and layout. Start with the
[compatibility matrix](docs/COMPATIBILITY.md), especially on other distributions.

Existing Windows, macOS/OpenCore, Linux, recovery, snapshot and custom entries are
preserved. Applying a theme does not discover or add missing operating systems.
Native Windows Boot Manager and Apple boot screens cannot use these themes.

GRUB retains the complete original configuration and appends graphics commands;
Limine retains its entire entry section. Restore checks for later changes before
writing. See [recovery and removal](docs/RECOVERY.md).

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| Checksum mismatch or missing archive | Stop before extraction; download the matching archive and checksum file again. |
| Preview does not open | Open the printed PNG path with your image viewer; `xdg-open` is optional. |
| Host detection or plan is refused | Read the refusal and check the active UEFI entry, required tools and supported layout. An installed GRUB/Limine package alone does not establish compatibility. |
| Theme is not visible after applying | Verify the actual bootloader and retained menu visibility settings; Limine retains its existing timeout. Consult the compatibility and recovery guides. |
| Restore reports changed files | Preserve state and backups, then follow the appearance-only recovery procedure. Do not force-copy an obsolete boot configuration. |

Physical evidence is limited to the documented Omarchy/Limine Synaptic Cosmos
experiment. VM screenshots and software tests do not certify every distribution,
display, encrypted layout or operating-system boot. See
[validation scope](docs/VALIDATION.md) before relying on the preview on another host.

## Documentation and contributing

- [Install, choose a theme and restore](docs/INSTALLER.md)
- [GRUB CLI and Debian package](docs/GRUB.md)
- [Limine CLI and Omarchy notes](docs/OMARCHY.md)
- [Compatibility and known limits](docs/COMPATIBILITY.md)
- [Build and test](docs/DEVELOPMENT.md), [release process](docs/RELEASE.md)
- [Validation evidence](docs/VALIDATION.md), [Limine hardware scope](docs/VALIDATION-OMARCHY.md)
- [Design and artwork provenance](docs/DESIGN.md)

Maintained by [DreamLab Solutions](https://github.com/DreamLab-Solutions).
Code and documentation: [MIT](LICENSE-MIT). Runtime artwork:
[CC BY 4.0 where applicable](ARTWORK-LICENSE.md). DejaVu fonts retain their own
license; DreamLab marks are reserved. See [component licensing](LICENSE).
