# Release process

Releases are versioned downloads with English notes, four installable packages
and one checksum file. CI artifacts are temporary build outputs; they are not
the user-facing distribution channel.

## Repository move

`DreamLab-Solutions/dls-neon-bootloaders` is the canonical source for both GRUB
and Limine. It starts from the sanitized main history, without importing PR refs
from the private predecessor. The v0.5.2 tag and its preview assets are retained
unchanged; their embedded documentation reflects the repository name at build
time. Current guides on main use the new repository. Build any changed downloads
under a new version, following the process below.

## Contents of v0.5.2

| Asset | Purpose |
| --- | --- |
| `dls-neon-setup-0.5.2.tar.gz` | Recommended combined console, all themes and native previews. |
| `dls-neon-grub_0.5.2_all.deb` | Debian/Ubuntu GRUB manager; no automatic activation. |
| `dls-neon-grub-0.5.2.tar.gz` | Portable GRUB manager and themes. |
| `dls-neon-limine-0.5.2.tar.gz` | Dedicated Limine manager, themes and backup helper. |
| `SHA256SUMS` | Exact SHA-256 values for the four packages. |
| `RELEASE-NOTES.md` | English notes and installation instructions, also used as the release body. |

Runtime archives contain documentation, applicable licenses and referenced images.
They exclude Docker images, developer containers, QEMU/OVMF/EFI executables,
private configs/backups/photos and privately archived original concept references.
GitHub automatically adds Source code archives; those contain repository source
and must not be presented as the ready-to-run installer.

## Prepare a release

1. Update `VERSION`, the current download filenames in English/Italian guides,
   and `docs/CHANGELOG.md`. Keep installer behavior and qualified hardware scope
   explicit; documentation changes do not establish a new physical boot result.
2. Run the tests and native preview workflows on the exact release source.
   Build the four packages, then run `python3 scripts/release.py` to verify and
   stage the complete set. Check the extracted console and offline docs.
3. Run the **Prepare release** workflow manually from the reviewed main commit.
   It builds and validates packages and creates a **draft prerelease** bound to
   that commit. It refuses an existing release/tag rather than replacing assets.
4. Review the draft's assets, checksums, English notes and target SHA. Publish it
   as a preview after approval. Never replace a published asset silently; use a
   new version for a changed package. A preview is not a universal support claim.

For a local reviewed build, the equivalent GitHub CLI command is:

```sh
gh release create v0.5.2 dist/release/* \
  --repo DreamLab-Solutions/dls-neon-bootloaders --target REVIEWED_COMMIT_SHA \
  --draft --prerelease --title 'DreamLab Boot Themes v0.5.2 — preview' \
  --notes-file dist/release/RELEASE-NOTES.md
```

Publish a reviewed draft with `gh release edit v0.5.2 --draft=false`.
Read the release back, download every attached asset and compare its checksum
with the staged release before reporting completion.

## Preview visibility and public release

The repository is currently **private**. Its releases inherit that access;
creating a release does not make the repository or downloads public. The user
requested release packaging and documentation; a visibility change is separate.

Code/documentation is MIT, runtime artwork is CC BY 4.0 where applicable, DejaVu
has its own license and DreamLab marks are reserved. Original concept references are privately archived outside Git and excluded from
the artwork grant. Check every branch/tag, source archive, release package and
provider-managed PR reference/cache before publication. A rewrite or force-push
alone does not prove GitHub has expunged old data. Keep visibility private until
provider-side exposure is resolved. Never silently replace published assets or
remove license attribution to satisfy a scan. See GitHub's [removal procedure](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Before calling a release hardware-qualified, complete the applicable real boot,
restart/cold boot, desktop return, displays and restore/recovery checks and record
evidence. Current physical scope is in [VALIDATION-OMARCHY.md](VALIDATION-OMARCHY.md);
GRUB/other-distribution and Windows/macOS boot remain unqualified. A prerelease
can accurately describe these limits without implying those tests passed.
