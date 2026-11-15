# Release process

Releases are versioned downloads with English notes, four installable packages
and one checksum file. Packaging and verification run in a local checkout.

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
2. Run `bash scripts/validate-local.sh` from a clean checkout of the reviewed
   main commit. The command runs the tests and native previews, builds the four
   packages, and stages the verified set under `dist/release/`.
   Check the extracted console and offline docs.
3. After approval, create a **draft prerelease** from that checkout using the
   commands below. Use a version with no existing release or tag.
4. Review the draft's assets, checksums, English notes and target SHA. Publish it
   as a preview after approval. Never replace a published asset silently; use a
   new version for a changed package. A preview is not a universal support claim.

Use the local GitHub CLI for the approved draft:

```sh
repo=DreamLab-Solutions/dls-neon-bootloaders
tag="v$(cat VERSION)"
commit="$(git rev-parse HEAD)"
remote_tag="$(git ls-remote --refs "https://github.com/$repo.git" "refs/tags/$tag")" &&
  test -z "$remote_tag" &&
  gh release create "$tag" dist/release/* \
    --repo "$repo" --target "$commit" \
    --draft --prerelease --title "DreamLab Boot Themes $tag — preview" \
    --notes-file dist/release/RELEASE-NOTES.md
```

Publish a reviewed draft with `gh release edit "$tag" --repo "$repo" --draft=false`.
Read the release back, download every attached asset and compare its checksum
with the staged release before reporting completion.

## Publish an authenticated Nexus bundle

From the clean checkout of the reviewed `vMAJOR.MINOR.PATCH` tag, prepare the
bundle locally. This runs the complete local validation and stages the four
packages, their checksums, the release notes and source metadata.

```sh
python3 scripts/nexus_release.py
```

Use the unchanged `dist/nexus/<sha256>.tgz` from preparation and keep it for
retries.
Use the existing scoped Sunnyday Nexus publisher credential in the private
`dreamlab/artifacts/nexus.json` file under your XDG configuration directory.
`DREAMLAB_NEXUS_CONFIG` selects an existing credential file, and a process
`DREAMLAB_NEXUS_AUTH` takes precedence.

Replace `PREPARED_SHA256` with the digest printed by the preparation command.

```sh
python3 scripts/nexus_release.py --publish dist/nexus/PREPARED_SHA256.tgz
```

Share the resulting digest URL and SHA-256 with recipients who have approved
Nexus read access. Before unpacking, readers verify the bundle digest, then
run `sha256sum --check SHA256SUMS` against the extracted packages. Public
downloads remain available through the repository's existing release page.

## Preview visibility and public release

The canonical repository and its releases are **public**. The user approved
public publication after source, history, package and documentation review on
2026-10-18. The private predecessor is retained separately; its provider-managed
PR references were not imported. The current v0.5.2 downloads remain unchanged.

Code/documentation is MIT, runtime artwork is CC BY 4.0 where applicable, DejaVu
has its own license and DreamLab marks are reserved. Original concept references are privately archived outside Git and excluded from
the artwork grant. Check every branch/tag, source archive, release package and
provider-managed PR reference/cache before publication. A rewrite or force-push
alone does not prove GitHub has expunged old data. Any future visibility change
needs explicit authorization after reviewing the actual refs and assets. Never silently replace published assets or
remove license attribution to satisfy a scan. See GitHub's [removal procedure](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Before calling a release hardware-qualified, complete the applicable real boot,
restart/cold boot, desktop return, displays and restore/recovery checks and record
evidence. Current physical scope is in [VALIDATION-OMARCHY.md](VALIDATION-OMARCHY.md);
GRUB/other-distribution and Windows/macOS boot remain unqualified. A prerelease
can accurately describe these limits without implying those tests passed.
