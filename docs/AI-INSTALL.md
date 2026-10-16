# Installation with an AI agent

An agent can perform installation through the combined package's CLI. It needs
terminal access on the target Linux computer. A cloud-only agent cannot inspect
that computer merely because a user supplied a local path.

## Copyable prompt

```text
Install DreamLab Boot Themes from https://github.com/DreamLab-Solutions/dls-neon-grub
using docs/AI-INSTALL.md. Inspect the actual active UEFI bootloader read-only,
qualify its layout, show the four themes and verify the release checksum. Ask
which theme I prefer if I have not chosen one. Review the plan and backup/live
USB readiness with me. Apply through the guarded CLI only after explicit approval.
Preserve all existing boot entries and the current bootloader. Keep inventory,
passphrases and backups private. Do not bypass checks or reboot automatically.
```

For Codex CLI, pass that instruction as the initial interactive prompt; see the
[official CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli).
Other terminal-capable agents can use the same prompt. Do not run the agent
itself with sudo or disable its permission controls.

## Procedure for the agent

1. Read [compatibility](COMPATIBILITY.md), [installation](INSTALLER.md) and
   [recovery](RECOVERY.md). Inspect the active UEFI loader, ESP mount, encryption
   and multiboot entries read-only. Keep inventory local. Request administrative
   read access through normal authentication, never a password in chat.
2. Download the combined archive and `SHA256SUMS` from a compatible published
   [release](https://github.com/DreamLab-Solutions/dls-neon-grub/releases/tag/v0.5.2).
   Verify before extraction. Do not use a source archive, pipe a remote script
   through sudo, install another bootloader or downgrade EFI files.
3. Show the four images in `previews/grub/` or `previews/limine/`. Use an existing
   user choice; otherwise ask. Review GRUB profile/timeout changes. Limine keeps
   its resolution/default/timeout.
4. Generate the guarded plan below. Show the target, preserved entries, theme
   and proposed settings. Confirm an independently verified backup and a
   boot-tested UEFI live USB, including encrypted-root access if applicable.
5. Obtain explicit approval for this write. Apply with its exact review hash and
   the same selection. A changed plan needs fresh review; never invent a hash
   or bypass qualification. Cancellation means stop.
6. Read the result/status and retain the backup. Report file verification separately
   from boot success. The user initiates and verifies the next reboot.

## Guarded CLI

From the extracted package run `sudo python3 dls-neon-setup detect`. Generate a
plan using the detected backend and selected options. For example, **only on a
qualified GRUB target**, after selecting Synaptic Cosmos:

```sh
sudo python3 dls-neon-setup plan --backend grub --theme synaptic-cosmos \
  --profile 1080p --timeout 8
```

The JSON includes `review_sha256`, configuration path, entries, `can_apply` and
any refusal reason. It binds bundle, system and selection. For Limine use
`--backend limine`; this does not select or migrate the installed bootloader.
Stop if qualification fails or `can_apply` is false.

Only after explicit approval and verified recovery readiness, substitute the
actual `review_sha256` from the plan for `REVIEW_HASH_FROM_PLAN`:

```sh
sudo python3 dls-neon-setup apply --backend grub --theme synaptic-cosmos \
  --profile 1080p --timeout 8 --expected-review REVIEW_HASH_FROM_PLAN \
  --approve-boot-write --recovery-confirmed
```

These flags assert real approval and recovery readiness; do not add them as
unattended defaults. Keep the JSON private. The console is an alternative with
exact `s`/`APPLICA` confirmations; do not fake those through a pipe.

Restore needs a fresh current plan, `can_restore`, explicit approval and `restore`
with the same review/approval options. If later updates changed entries/assets,
stop for appearance-only recovery. This does not authorize EFI replacement,
NVRAM edits, OS-entry/encryption changes or automatic reboot.
