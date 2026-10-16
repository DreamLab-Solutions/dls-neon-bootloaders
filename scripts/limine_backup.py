#!/usr/bin/env python3
"""Copy the current ESP and relevant config, verify archive members; never write boot files."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tarfile


def digest(stream):
    result = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(chunk)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    dest = args.destination
    if not dest.is_absolute() or dest.exists() or any(p.is_symlink() for p in dest.parents):
        raise SystemExit('Use a new absolute non-symlink destination outside /boot')
    if dest == Path('/boot') or Path('/boot') in dest.parents:
        raise SystemExit('Backup must be outside ESP')
    if os.geteuid() != 0:
        raise SystemExit('Root read access required')
    dest.mkdir(mode=0o700)
    archive = dest / 'esp-and-config.tar'
    files = sorted(p for p in Path('/boot').rglob('*') if p.is_file())
    files += [p for p in [Path('/etc/fstab'), Path('/etc/default/limine'),
                         Path('/etc/limine-entry-tool.conf'), Path('/etc/limine-snapper-sync.conf')] if p.is_file()]
    files += sorted(Path('/etc/limine-entry-tool.d').glob('*.conf'))
    manifest = {}
    with tarfile.open(archive, 'w') as tar:
        os.chmod(archive, 0o600)
        for path in files:
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise RuntimeError('Unexpected non-regular source')
            with path.open('rb') as stream:
                manifest[str(path).lstrip('/')] = digest(stream)
            tar.add(path, arcname=str(path).lstrip('/'), recursive=False)
    with archive.open('rb') as stream:
        os.fsync(stream.fileno())
        archive_sha = digest(stream)
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        if {member.name for member in members} != set(manifest):
            raise RuntimeError('Archive inventory mismatch')
        for member in members:
            with tar.extractfile(member) as stream:
                if digest(stream) != manifest[member.name]:
                    raise RuntimeError('Archive verification failed: ' + member.name)
    # Detect changed source after copying; this does not freeze package/snapshot services.
    for path in files:
        with path.open('rb') as stream:
            if digest(stream) != manifest[str(path).lstrip('/')]:
                raise RuntimeError('Source changed during backup; do not use this backup')
    nvram = subprocess.check_output(['efibootmgr', '-v'], text=True)
    (dest / 'firmware-entries.txt').write_text(nvram)
    partitions = subprocess.check_output(['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,FSTYPE,UUID,PARTUUID,MOUNTPOINTS'], text=True)
    (dest / 'partitions.json').write_text(partitions)
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'archive_sha256': archive_sha,
              'files': manifest, 'verification': 'archive members and current source re-read match',
              'scope': 'local backup; independent-medium copy and live USB not verified'}
    (dest / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    (dest / 'SHA256SUMS').write_text(archive_sha + '  esp-and-config.tar\n')
    owner = int(os.environ.get('PKEXEC_UID', os.getuid()))
    for path in [*dest.iterdir(), dest]:
        os.chown(path, owner, -1)
        os.chmod(path, 0o700 if path.is_dir() else 0o600)
    print(json.dumps({'destination': str(dest), 'archive_sha256': archive_sha, 'files_verified': len(manifest),
                      'independent_medium': 'not verified', 'live_usb': 'not verified'}))


if __name__ == '__main__':
    main()
