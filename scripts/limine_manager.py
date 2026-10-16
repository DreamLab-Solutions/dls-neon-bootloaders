#!/usr/bin/env python3
"""Conservative Limine appearance activation. Python standard library only."""
import argparse
from contextlib import contextmanager
import difflib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import uuid

KEYS = set('wallpaper wallpaper_style backdrop interface_branding interface_branding_color interface_branding_colour interface_help_color interface_help_colour interface_help_color_bright interface_help_colour_bright term_background term_foreground term_foreground_bright term_background_bright term_palette term_palette_bright term_margin term_margin_gradient'.split())
BEGIN = '# BEGIN DLS NEON LIMINE\n'
END = '# END DLS NEON LIMINE\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def regular(path):
    for part in [path, *path.parents]:
        if part.is_symlink():
            raise RuntimeError(f'Symlink refused: {part}')
    if not path.is_file():
        raise RuntimeError(f'Expected regular file: {path}')
    return path.read_bytes()


def atomic(path, data):
    fd, temp = tempfile.mkstemp(prefix='.dls-neon-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def key(line):
    match = re.match(r'^\s*([a-zA-Z_]+)\s*:', line)
    return match.group(1).lower() if match else None


def candidate(original, appearance):
    text = original.decode('utf-8')
    if BEGIN in text or END in text:
        raise RuntimeError('Already managed; restore before installing another version')
    lines = text.splitlines(keepends=True)
    first = next((n for n, line in enumerate(lines) if line.lstrip().startswith('/')), None)
    if first is None:
        raise RuntimeError('No native Limine entries found')
    head, entries = lines[:first], lines[first:]
    if any(key(line) in KEYS for line in entries):
        raise RuntimeError('Appearance options inside entry section: manual review required')
    if any('${' in line and key(line) in KEYS for line in head):
        raise RuntimeError('Appearance macros need manual review')
    # Preserve every non-appearance line, including default, timeout and security options.
    clean = ''.join(line for line in head if key(line) not in KEYS)
    if clean and not clean.endswith('\n'):
        clean += '\n'
    return (clean + BEGIN + appearance + END + ''.join(entries)).encode()


def assets(source):
    manifest = json.loads(regular(source / 'manifest.json'))
    if set(manifest) != {'background.png', 'appearance.conf'}:
        raise RuntimeError('Unexpected asset manifest')
    for name, digest in manifest.items():
        if sha(regular(source / name)) != digest:
            raise RuntimeError('Asset checksum mismatch: ' + name)
    key_id = manifest['background.png'][:16]
    appearance = regular(source / 'appearance.conf').decode()
    for line in appearance.splitlines():
        if line.strip() and not line.startswith('#') and key(line) not in KEYS:
            raise RuntimeError('Non-appearance setting refused')
    expected = f'wallpaper: boot():/dls-neon-limine/{key_id}/background.png'
    if appearance.splitlines().count(expected) != 1:
        raise RuntimeError('Unexpected wallpaper reference')
    return key_id, appearance, manifest


class Manager:
    def __init__(self, root=Path('/')):
        self.root = root
        self.config = root / 'boot/limine.conf'
        self.state = root / 'var/lib/dls-neon-limine'
        self.active = self.state / 'active.json'
        self.pending = self.state / 'pending.json'

    def owned_assets(self, meta):
        if not re.fullmatch(r'[0-9a-f]{16}', meta['asset']):
            raise RuntimeError('Invalid asset path')
        if set(meta['manifest']) != {'background.png', 'appearance.conf'}:
            raise RuntimeError('Invalid owned asset manifest')
        directory = self.root / 'boot/dls-neon-limine' / meta['asset']
        actual = {p.name: sha(regular(p)) for p in directory.iterdir()}
        if actual != meta['manifest']:
            raise RuntimeError('Previous theme assets changed; review before switching')

    def plan(self, source, replace=False):
        key_id, appearance, manifest = assets(source)
        old = regular(self.config)
        baseline = old
        if replace:
            if self.pending.exists():
                raise RuntimeError('Interrupted transaction exists; recover first')
            previous = json.loads(regular(self.active))
            if sha(old) != previous['after']:
                raise RuntimeError('Active config changed; review updates before switching')
            self.owned_assets(previous)
            text = old.decode()
            if text.count(BEGIN) != 1 or text.count(END) != 1:
                raise RuntimeError('Managed appearance block missing or ambiguous')
            start = text.index(BEGIN)
            end = text.index(END) + len(END)
            first = next((i for i, line in enumerate(text.splitlines(True)) if line.lstrip().startswith('/')), None)
            if first is None or start >= end or end > len(''.join(text.splitlines(True)[:first])):
                raise RuntimeError('Managed block must precede every boot entry')
            baseline = (text[:start] + text[end:]).encode()
        new = candidate(baseline, appearance)
        return old, new, key_id, manifest

    @contextmanager
    def lock(self):
        for part in [self.state, *self.state.parents]:
            if part.is_symlink():
                raise RuntimeError('State path is a symlink')
        self.state.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state, 0o700)
        with (self.state / 'lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def install(self, source, expected=None, replace=False):
        with self.lock():
            if self.pending.exists() or (self.active.exists() and not replace):
                raise RuntimeError('Active or interrupted transaction exists; inspect status and recover')
            if replace and not self.active.exists():
                raise RuntimeError('No active theme to switch; use install')
            previous = json.loads(regular(self.active)) if replace else None
            old, new, key_id, manifest = self.plan(source, replace=replace)
            if expected is not None and sha(old) != expected:
                raise RuntimeError('Reviewed configuration changed; make a new plan')
            destination = self.root / 'boot/dls-neon-limine' / key_id
            for part in [destination, *destination.parents]:
                if part.is_symlink():
                    raise RuntimeError('Asset destination symlink refused')
            if destination.exists():
                raise RuntimeError('Asset destination exists; refusing to claim ownership')
            backup = self.state / ('backup-' + str(uuid.uuid4()))
            backup.mkdir(mode=0o700)
            atomic(backup / 'before.conf', old)
            atomic(backup / 'after.conf', new)
            metadata = {'backup': backup.name, 'before': sha(old), 'after': sha(new),
                        'asset': key_id, 'manifest': manifest}
            if previous is not None:
                metadata['previous'] = previous
            atomic(backup / 'manifest.json', (json.dumps(metadata, indent=2) + '\n').encode())
            if sha(regular(backup / 'before.conf')) != metadata['before']:
                raise RuntimeError('Backup verification failed')
            atomic(self.pending, json.dumps(metadata).encode())
            # Keep the journal on failure. Recovery never guesses which files are current.
            destination.mkdir(parents=True)
            for name in manifest:
                atomic(destination / name, regular(source / name))
            for name, digest in manifest.items():
                if sha(regular(destination / name)) != digest:
                    raise RuntimeError('Staged asset mismatch')
            if regular(self.config) != old:
                raise RuntimeError('Configuration changed concurrently')
            atomic(self.config, new)
            if regular(self.config) != new:
                raise RuntimeError('Configuration verification failed')
            atomic(self.active, json.dumps(metadata).encode())
            self.pending.unlink()
            print('Activated; hardware reboot is NOT verified. Backup: ' + str(backup))

    def restore(self):
        with self.lock():
            record = self.pending if self.pending.exists() else self.active
            meta = json.loads(regular(record))
            if not re.fullmatch(r'backup-[0-9a-f-]{36}', meta['backup']):
                raise RuntimeError('Invalid backup path')
            if not re.fullmatch(r'[0-9a-f]{16}', meta['asset']):
                raise RuntimeError('Invalid asset path')
            backup = self.state / meta['backup']
            old = regular(backup / 'before.conf')
            if sha(old) != meta['before']:
                raise RuntimeError('Backup corrupted')
            previous = meta.get('previous')
            if previous is not None:
                if previous['after'] != meta['before']:
                    raise RuntimeError('Invalid previous-theme checkpoint')
                self.owned_assets(previous)
            current = regular(self.config)
            if sha(current) not in {meta['before'], meta['after']}:
                raise RuntimeError('Boot config changed after activation; refusing to overwrite updates. See OMARCHY.md')
            destination = self.root / 'boot/dls-neon-limine' / meta['asset']
            if destination.exists():
                # Allow a partially staged transaction; reject extra or edited files.
                for item in destination.iterdir():
                    if item.name not in meta['manifest'] or sha(regular(item)) != meta['manifest'][item.name]:
                        raise RuntimeError('Owned asset modified; refusing removal')
            # Restore first; then remove only recorded unchanged files. A crash leaves a retryable journal.
            atomic(self.config, old)
            if regular(self.config) != old:
                raise RuntimeError('Restore verification failed')
            if destination.exists():
                for item in destination.iterdir():
                    item.unlink()
                destination.rmdir()
            if previous is None:
                self.active.unlink(missing_ok=True)
            else:
                atomic(self.active, json.dumps(previous).encode())
            self.pending.unlink(missing_ok=True)
            print('Previous theme restored.' if previous else 'Original appearance restored.')
            print('Verified backup retained at ' + str(backup))

    def uninstall(self):
        seen = set()
        for _ in range(128):
            record = self.pending if self.pending.exists() else self.active
            if not record.exists():
                return
            meta = json.loads(regular(record))
            if meta['backup'] in seen:
                raise RuntimeError('Theme history cycle; manual review required')
            seen.add(meta['backup'])
            self.restore()
        raise RuntimeError('Theme history exceeds safety limit')


def host_guard():
    if os.uname().machine != 'x86_64':
        raise RuntimeError('This adapter is qualified only for x86-64')
    if os.geteuid() != 0:
        raise RuntimeError('Activation/restore requires root; dry-run does not')
    if not Path('/sys/firmware/efi').is_dir():
        raise RuntimeError('This adapter supports UEFI only')
    result = subprocess.run(['efibootmgr', '-v'], check=True, capture_output=True, text=True).stdout
    current = re.search(r'^BootCurrent: ([0-9A-Fa-f]{4})$', result, re.M)
    if not current:
        raise RuntimeError('Active UEFI entry is not identified as Limine')
    active_line = next((line for line in result.splitlines() if line.startswith('Boot' + current[1])), '')
    if r'\efi\limine\limine_x64.efi' not in active_line.lower():
        raise RuntimeError('Active UEFI entry is not identified as Limine by its EFI path')
    if sha(regular(Path('/boot/EFI/limine/limine_x64.efi'))) != '3fe0de87c13a12998b3c785b0c57ddfbcd6fc57251c1b0628604583ec8e9a5ff':
        raise RuntimeError('Active ESP Limine binary is not the qualified 12.8.0 build')
    mount = subprocess.run(['findmnt', '-J', '-M', '/boot', '-o', 'TARGET,FSTYPE,OPTIONS'],
                           check=True, capture_output=True, text=True)
    data = json.loads(mount.stdout)['filesystems'][0]
    if data['fstype'] != 'vfat' or 'rw' not in data['options'].split(','):
        raise RuntimeError('/boot must be the mounted writable FAT ESP')
    for name in ['SecureBoot', 'SetupMode']:
        paths = list(Path('/sys/firmware/efi/efivars').glob(name + '-*'))
        if len(paths) != 1:
            raise RuntimeError('Cannot verify Secure Boot state')
        value = regular(paths[0])
        if len(value) != 5 or (name == 'SecureBoot' and value[4] != 0):
            raise RuntimeError('Secure Boot enabled or unknown: this adapter is not qualified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['themes', 'inspect', 'plan', 'install', 'switch', 'status', 'restore', 'uninstall'])
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent / 'data')
    parser.add_argument('--theme', choices=['event-horizon', 'quantum-fabric', 'sentient-atlas', 'synaptic-cosmos'])
    parser.add_argument('--replace', action='store_true', help='Plan a switch from an active managed theme; read-only')
    parser.add_argument('--expected-config-sha256', help='Reviewed baseline hash; required for installation')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--approve-boot-write', action='store_true', help='Only after reviewing backup/recovery and exact diff')
    args = parser.parse_args()
    if args.theme:
        args.source = args.source.parent / 'themes' / args.theme
    manager = Manager()
    try:
        if args.action == 'themes':
            catalog = Path(__file__).resolve().parent / 'catalog.json'
            print(regular(catalog).decode())
        elif args.action == 'inspect':
            content = regular(manager.config)
            lines = content.decode().splitlines()
            report = {'config_sha256': sha(content),
                      'entries': [line.strip() for line in lines if line.lstrip().startswith('/')],
                      'settings': [line for line in lines if key(line) in {'timeout', 'quiet', 'default_entry', 'remember_last_entry', 'graphics', 'interface_resolution', 'term_font_scale'}],
                      'efi_files': sorted(str(path.relative_to('/boot')) for path in Path('/boot/EFI').rglob('*') if path.is_file() and path.suffix.lower() == '.efi'),
                      'scope': 'read-only; no boot writes, backup creation or reboot'}
            print(json.dumps(report, indent=2, ensure_ascii=False))
        elif args.action == 'status':
            for path in [manager.active, manager.pending]:
                if path.exists():
                    print(regular(path).decode())
            print('Current configuration SHA256: ' + sha(regular(manager.config)))
        elif args.action == 'plan' or (args.action in {'install', 'switch'} and args.dry_run):
            old, new, _, _ = manager.plan(args.source, replace=args.replace or args.action == 'switch')
            print(''.join(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                             fromfile='limine.conf', tofile='candidate.conf')))
            print('Baseline SHA256: ' + sha(old))
            print('Read-only plan; no backup or boot files created.')
        else:
            if args.dry_run:
                raise RuntimeError('Use plan for install preview; restore/uninstall dry-run is not supported')
            if not args.approve_boot_write:
                raise RuntimeError('Explicit --approve-boot-write required')
            if args.action in {'install', 'switch'} and not re.fullmatch(r'[0-9a-f]{64}', args.expected_config_sha256 or ''):
                raise RuntimeError('Install/switch requires --expected-config-sha256 from the reviewed plan')
            host_guard()
            if args.action in {'install', 'switch'}:
                manager.install(args.source, args.expected_config_sha256, replace=args.action == 'switch')
            elif args.action == 'uninstall':
                manager.uninstall()
            else:
                manager.restore()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
