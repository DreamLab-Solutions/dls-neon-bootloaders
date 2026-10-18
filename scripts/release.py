#!/usr/bin/env python3
"""Validate and stage versioned release assets; never touches host boot files."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tarfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO = 'https://github.com/DreamLab-Solutions/dls-neon-bootloaders'
LINK = re.compile(r'!?\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def check_links(files):
    """Check local Markdown destinations in a repository or an offline package."""
    for name, data in files.items():
        if not name.endswith('.md'):
            continue
        for target in LINK.findall(data.decode('utf-8')):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(parsed.path)))
            if path not in files and not any(x.startswith(path.rstrip('/') + '/') for x in files):
                raise RuntimeError(f'Broken offline link: {name} -> {target}')


def source_docs():
    paths = [ROOT/'README.md', ROOT/'LICENSE', ROOT/'LICENSE-MIT', ROOT/'ARTWORK-LICENSE.md']
    paths += [p for p in (ROOT/'docs').rglob('*') if p.is_file()]
    check_links({str(p.relative_to(ROOT)): p.read_bytes() for p in paths})


def archive_files(archive):
    files = {}
    for member in archive.getmembers():
        path = PurePosixPath(member.name)
        if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir()):
            raise RuntimeError('Unsafe package member: ' + member.name)
        name = str(path)
        if name in files:
            raise RuntimeError('Duplicate package member: ' + name)
        if any(x in path.parts for x in ('.git', 'local', 'assets', 'node_modules')) or path.suffix.lower() in {'.efi', '.iso', '.qcow2', '.vmdk'} or path.name.startswith('Dockerfile'):
            raise RuntimeError('Development/private material in runtime package: ' + name)
        if member.isfile():
            files[name] = archive.extractfile(member).read()
    return files


def validate_tar(path, version):
    expected_root = path.name.removesuffix('.tar.gz')
    with tarfile.open(path, 'r:gz') as archive:
        raw = archive_files(archive)
    if not raw or any(not n.startswith(expected_root + '/') for n in raw):
        raise RuntimeError('Unexpected archive root: ' + path.name)
    files = {n[len(expected_root)+1:]: b for n, b in raw.items()}
    required = {'README.md', 'VERSION', 'LICENSE', 'LICENSE-MIT', 'ARTWORK-LICENSE.md'}
    if not required <= files.keys() or files['VERSION'].decode().strip() != version:
        raise RuntimeError('Missing metadata or wrong version: ' + path.name)
    for name, data in files.items():
        if PurePosixPath(name).name != 'manifest.json':
            continue
        manifest = json.loads(data)
        if not isinstance(manifest, dict):
            raise RuntimeError('Invalid manifest: ' + name)
        for target, expected in manifest.items():
            candidate = posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            if candidate not in files or hashlib.sha256(files[candidate]).hexdigest() != expected:
                raise RuntimeError('Manifest mismatch: ' + name + ' -> ' + target)
        if name == 'manifest.json' and set(manifest) != set(files) - {'manifest.json'}:
            raise RuntimeError('Incomplete combined package manifest')
    if expected_root.startswith('dls-neon-setup-') and 'manifest.json' not in files:
        raise RuntimeError('Missing combined package manifest')
    check_links(files)
    return files


def validate_deb(path, version):
    actual = subprocess.check_output(['dpkg-deb', '--field', str(path), 'Version'], text=True).strip()
    if actual != version:
        raise RuntimeError('Debian package version mismatch')
    payload = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(path)])
    with tarfile.open(fileobj=io.BytesIO(payload), mode='r:') as archive:
        files = archive_files(archive)
    if 'usr/bin/dls-neon-theme' not in files or not any(n.endswith('/LICENSE-DejaVu.txt') for n in files):
        raise RuntimeError('Incomplete Debian runtime package')
    check_links(files)
    return files


def asset_names(version):
    return [f'dls-neon-setup-{version}.tar.gz', f'dls-neon-grub_{version}_all.deb',
            f'dls-neon-grub-{version}.tar.gz', f'dls-neon-limine-{version}.tar.gz']


def release_notes(version):
    changelog = (ROOT/'docs/CHANGELOG.md').read_text()
    match = re.search(r'^## ' + re.escape(version) + r'[^\n]*\n(.*?)(?=^## |\Z)', changelog, re.M | re.S)
    if not match:
        raise RuntimeError('Current version missing from changelog')
    return f'''# DreamLab Boot Themes v{version} — preview

Four themes for the existing GRUB or qualified Limine bootloader. This preview
contains an interactive terminal chooser, offline native-menu image previews,
verified transaction backups and conservative restore.

## Download

| Asset | Use |
| --- | --- |
| `dls-neon-setup-{version}.tar.gz` | Recommended combined console for GRUB/Limine. |
| `dls-neon-grub_{version}_all.deb` | Debian/Ubuntu GRUB manager; no automatic activation. |
| `dls-neon-grub-{version}.tar.gz` | Portable GRUB CLI and four themes. |
| `dls-neon-limine-{version}.tar.gz` | Limine CLI, four themes and backup helper. |
| `SHA256SUMS` | Checksums for these four packages. |

Use **Assets** below. GitHub's automatic Source code archives are developer
sources, not the ready-to-run installer. Docker is not required. Release assets
are publicly downloadable without repository access or a GitHub account.

## Install the combined console

Download its archive and `SHA256SUMS` into one directory, then:

```sh
sha256sum --check --ignore-missing SHA256SUMS
tar -xzf dls-neon-setup-{version}.tar.gz
cd dls-neon-setup-{version}
python3 dls-neon-setup
```

Continue only if the archive reports **OK**. Run as your normal user; sudo is
requested for inspection and approved writes. Choose **1–4**, **p** for preview,
**v** for the host plan, **a** to apply, **r** to restore. Current prompts are
Italian: confirm verified recovery with **s**, then **APPLICA** or **RIPRISTINA**.

Have a verified independent backup and a boot-tested UEFI live USB before applying.
The installer does not reboot. Existing OS entries are preserved; missing ones
are not discovered or added. Requirements: Linux x86-64 UEFI, Python 3.11+, sudo,
efibootmgr/util-linux and native GRUB tools where applicable. Limine is limited
to the exact qualified 12.8.0 EFI build/path. Native Windows/Apple boot screens
are not targets. Hardware evidence is limited to the existing user-reported
Omarchy/Synaptic Cosmos experiment; GRUB/other-OS physical boot remains unqualified.

[Installation]({REPO}/blob/v{version}/docs/INSTALLER.md) ·
[Compatibility]({REPO}/blob/v{version}/docs/COMPATIBILITY.md) ·
[Gallery]({REPO}/blob/v{version}/docs/THEMES.md) ·
[Recovery]({REPO}/blob/v{version}/docs/RECOVERY.md) ·
[Italiano]({REPO}/blob/v{version}/docs/it/README.md)

## Changes

{match[1].strip()}

## Licensing

Code/documentation: MIT. Runtime artwork: CC BY 4.0 where applicable, with AI
provenance disclosed. DejaVu retains its own license; DreamLab marks are reserved.
Component licenses are included. The original concept reference and private
hardware/configuration/backup material are excluded from runtime packages.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist', type=Path, default=ROOT/'dist')
    parser.add_argument('--check-docs', action='store_true')
    args = parser.parse_args()
    source_docs()
    if args.check_docs:
        print('Source documentation links: OK')
        return
    version = (ROOT/'VERSION').read_text().strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise RuntimeError('Invalid release version')
    from privacy_check import check_files
    names = asset_names(version)
    for name in names:
        path = args.dist/name
        if name.endswith('.deb'):
            contents = validate_deb(path, version)
        else:
            contents = validate_tar(path, version)
        check_files(contents)
    notes = release_notes(version)
    stage = args.dist/'release'
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    for name in names:
        shutil.copy2(args.dist/name, stage/name)
    (stage/'SHA256SUMS').write_text(''.join(
        hashlib.sha256((stage/name).read_bytes()).hexdigest() + '  ' + name + '\n' for name in names))
    (stage/'RELEASE-NOTES.md').write_text(notes)
    print(f'Validated v{version}: four runtime packages, checksums and English notes in {stage}')


if __name__ == '__main__':
    main()
