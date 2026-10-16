#!/usr/bin/env python3
"""Appearance-only GRUB activation preserving every original config byte."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

NAME = "dls-neon"
DROPIN = "etc/default/grub.d/99-dls-neon.cfg"
CONFIG = "boot/grub/grub.cfg"
STATE = "var/lib/dls-neon-grub"
GFX = {"720p": "1280x720", "1080p": "1920x1080", "1440p": "2560x1440", "4k": "3840x2160"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def tree_digest(path):
    return {str(p.relative_to(path)): digest(p) for p in sorted(path.rglob("*")) if p.is_file()}


def verify_assets(source):
    if source.is_symlink() or any(p.is_symlink() for p in source.rglob("*")):
        raise RuntimeError("Theme assets must not contain symlinks")
    manifest = json.loads((source / "manifest.json").read_text())
    if not manifest or any(Path(n).name != n for n in manifest):
        raise RuntimeError("Invalid asset manifest")
    actual = tree_digest(source)
    actual.pop("manifest.json", None)
    if actual != manifest:
        raise RuntimeError("Theme asset checksums do not match; rebuild or re-extract the package")


def atomic_copy(source, destination):
    fd, tmp = tempfile.mkstemp(prefix=".dls-neon-", dir=destination.parent)
    os.close(fd)
    try:
        shutil.copy2(source, tmp)
        os.replace(tmp, destination)
    finally:
        Path(tmp).unlink(missing_ok=True)


def boot_entries(text):
    return re.findall(r"^[ \t]*(?:menuentry|submenu)[ \t]+(.+?)[ \t]+\{[ \t]*$", text, re.MULTILINE)


def has_bls_menu(text):
    return bool(re.search(r'^\s*blscfg(?:\s|;|$)',text,re.M))


def has_native_menu(text):
    return bool(boot_entries(text) or has_bls_menu(text))


def entry_headers(text):
    return re.findall(r"^[ \t]*(menuentry|submenu)[ \t]+(.+?)[ \t]+\{[ \t]*$", text, re.MULTILINE)


def efi_id(tokens):
    """Only distro-generated EFI entries with a filesystem UUID qualify."""
    for index, token in enumerate(tokens[:-1]):
        if token in ("$menuentry_id_option", "${menuentry_id_option}", "--id"):
            value = tokens[index + 1]
            if re.fullmatch(r"osprober-efi-[0-9A-Fa-f]+(?:-[0-9A-Fa-f]+)+", value):
                return value
    return None


def efi_body(text, header, identity):
    """Compare EFI commands, allowing only device hints resolved by the same UUID.

    Deliberately limited to the standalone stanza format emitted by 30_os-prober.
    Unknown/custom formats fail closed instead of evaluating GRUB shell code.
    """
    pattern = (r"^[ \t]*menuentry[ \t]+" + re.escape(header)
               + r"[ \t]+\{[ \t]*\n(.*?)^[ \t]*\}[ \t]*$")
    bodies = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
    if len(bodies) != 1:
        return None
    uuid = identity.removeprefix("osprober-efi-")
    normalized, searches, loaders = [], 0, 0
    for line in bodies[0].splitlines():
        tokens = shlex.split(line, comments=True)
        if not tokens:
            continue
        if len(tokens) == 2 and tokens[0] == "set" and re.fullmatch(r"root=hd\d+,(?:gpt|msdos)\d+", tokens[1]):
            # 30_os-prober follows this fallback with a filesystem UUID search.
            normalized.append(("set", "root=<device-hint>"))
        elif tokens[0] == "search":
            if "--fs-uuid" not in tokens or "--set=root" not in tokens or tokens[-1] != uuid:
                return None
            searches += 1
            normalized.append(tuple(t for t in tokens if not t.startswith("--hint-")))
        else:
            if tokens[0] == "chainloader":
                loaders += 1
                if len(tokens) != 2 or not tokens[1].startswith("/"):
                    return None
            normalized.append(tuple(tokens))
    return normalized if searches and loaders == 1 else None


def compatible_boot_entries(before, after):
    """Keep order, hierarchy markers, IDs and EFI targets; tolerate device labels."""
    original, candidate = entry_headers(before), entry_headers(after)
    if not original or len(original) != len(candidate):
        return False
    try:
        for (old_kind, old_header), (new_kind, new_header) in zip(original, candidate):
            if old_kind != new_kind:
                return False
            old, new = shlex.split(old_header), shlex.split(new_header)
            identity = efi_id(old)
            if old_kind == "menuentry" and identity:
                if efi_id(new) != identity or old[1:] != new[1:]:
                    return False
                # Only the generated '(on /dev/...)' suffix may change.
                label = r" \(on /dev/[A-Za-z0-9_./-]+\)$"
                if re.sub(label, "", old[0]) != re.sub(label, "", new[0]):
                    return False
                old_body = efi_body(before, old_header, identity)
                if old_body is None or old_body != efi_body(after, new_header, identity):
                    return False
            elif old_header != new_header:
                return False
        return True
    except ValueError:
        return False


HOOK = 'etc/grub.d/99_dls_neon_theme'
CONFIGS = ('boot/grub/grub.cfg', 'boot/grub2/grub.cfg')
BEGIN = '# BEGIN DLS NEON GRUB\n'
END = '# END DLS NEON GRUB\n'


def appearance_commands(prefix, profile, timeout, fonts):
    """Native commands only; deliberately contains no OS entries or boot commands."""
    if profile not in GFX or not 1 <= timeout <= 60:
        raise RuntimeError('Invalid appearance settings')
    if not re.fullmatch(r'\(\$(?:root|dls_theme_root)\)/[A-Za-z0-9_./@+-]+', prefix):
        raise RuntimeError('Unsupported GRUB asset path')
    if any(not re.fullmatch(r'dejavu-[0-9]+\.pf2', name) for name in fonts):
        raise RuntimeError('Unexpected font name')
    commands = ['terminal_output console', 'insmod all_video', 'insmod gfxterm', 'insmod gfxmenu', 'insmod png',
                f'set gfxmode={GFX[profile]},1280x720,1024x768,auto']
    commands += [f'loadfont "{prefix}/{name}"' for name in fonts]
    commands += ['set gfxterm_font="DejaVu Sans Mono Regular 14"',
                 'terminal_output gfxterm', f'set theme="{prefix}/theme-{profile}.txt"',
                 'export theme', 'set timeout_style=menu', f'set timeout={timeout}']
    return '\n'.join(commands) + '\n'


class Manager:
    # root/runner are for isolated transaction tests, never exposed by CLI.
    def __init__(self, root=Path('/'), runner=subprocess.run, config=CONFIG, tools=None):
        if config not in CONFIGS:
            raise RuntimeError('Unsupported GRUB configuration path')
        self.root, self.run, self.config = Path(root), runner, config
        self.tools = tools or {'check':'grub-script-check', 'probe':'grub-probe', 'relpath':'grub-mkrelpath'}

    def p(self, relative):
        path = self.root / relative
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != self.root):
            raise RuntimeError(f'Refusing symlink in system path: {path}')
        return path

    @contextmanager
    def locked(self):
        state = self.p(STATE);state.mkdir(parents=True,exist_ok=True,mode=0o700)
        with self.p(STATE+'/lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield

    def install(self, source, profile, timeout, expected_config=None):
        verify_assets(source)
        cfg, hook = self.p(self.config), self.p(HOOK)
        before = cfg.read_bytes()
        if not has_native_menu(before.decode()) or BEGIN.encode() in before:
            raise RuntimeError('No native entries, or appearance is already managed')
        if not hook.parent.is_dir():
            raise RuntimeError('Expected /etc/grub.d generator directory')
        if hook.exists() or self.p(DROPIN).exists():
            raise RuntimeError('An activation already exists; restore it first')
        with self.locked():
            active = self.p(STATE+'/active.json')
            if active.exists() or hook.exists() or self.p(DROPIN).exists():
                raise RuntimeError('An active or interrupted transaction already exists')
            baseline = hashlib.sha256(before).hexdigest()
            if digest(cfg) != baseline or (expected_config is not None and expected_config != baseline):
                raise RuntimeError('Reviewed GRUB configuration changed; make a new plan')
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            key=hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest()[:12]
            theme_rel=f'{Path(self.config).parent}/themes/{NAME}-{key}-{stamp}'
            target=self.p(theme_rel)
            if target.exists():raise RuntimeError('Preserving existing theme directory')
            backup=self.p(STATE+'/backups/'+stamp);backup.mkdir(parents=True,mode=0o700)
            (backup/'grub.cfg').write_bytes(before)
            shutil.copystat(cfg,backup/'grub.cfg')
            if digest(backup/'grub.cfg') != baseline:raise RuntimeError('Backup checksum mismatch')
            record={'backup':str(backup.relative_to(self.root)),'theme':theme_rel,
                    'profile':profile,'timeout':timeout,'status':'preparing','config':self.config,
                    'hook':HOOK,'config_before':baseline,'theme_hashes':tree_digest(source),
                    'mode':'appearance-only; all original configuration bytes retained'}
            active.write_text(json.dumps(record,indent=2)+'\n')
            staged=None
            try:
                target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(source,target);verify_assets(target)
                uuid=self.run([self.tools['probe'],'--target=fs_uuid',str(target)],check=True,capture_output=True,text=True).stdout.strip()
                relpath=self.run([self.tools['relpath'],str(target)],check=True,capture_output=True,text=True).stdout.strip()
                if not re.fullmatch(r'[0-9A-Fa-f-]+',uuid) or not relpath.startswith('/'):
                    raise RuntimeError('Cannot qualify filesystem UUID and GRUB-relative asset path')
                commands=appearance_commands('($dls_theme_root)'+relpath,profile,timeout,sorted(p.name for p in target.glob('*.pf2')))
                block=BEGIN+f'if search --no-floppy --fs-uuid --set=dls_theme_root {uuid}; then\n'+commands+'fi\n'+END
                hook.write_text("#!/bin/sh\n# DLS appearance only; no discovery or OS entries.\ncat <<'DLS_NEON_EOF'\n"+block+'DLS_NEON_EOF\n')
                os.chmod(hook,0o755)
                fd,name=tempfile.mkstemp(prefix='.dls-neon-candidate-',dir=cfg.parent)
                with os.fdopen(fd,'wb') as stream:
                    stream.write(before + (b'' if before.endswith(b'\n') else b'\n') + block.encode())
                    stream.flush();os.fsync(stream.fileno())
                staged=Path(name)
                self.run([self.tools['check'],str(staged)],check=True)
                candidate=staged.read_bytes()
                if not candidate.startswith(before) or candidate[len(before):].count(BEGIN.encode()) != 1:
                    raise RuntimeError('Original GRUB bytes changed; refusing activation')
                if digest(cfg) != baseline:
                    raise RuntimeError('GRUB configuration changed concurrently; preserving it')
                os.chmod(staged,cfg.stat().st_mode & 0o777)
                record.update(status='active',config_after=digest(staged),hook_hash=digest(hook))
                (backup/'transaction.json').write_text(json.dumps(record,indent=2)+'\n')
                active.write_text(json.dumps(record,indent=2)+'\n')
                os.replace(staged,cfg)
                return record
            except BaseException as error:
                hook.unlink(missing_ok=True)
                if target.exists():shutil.rmtree(target)
                active.unlink(missing_ok=True)
                record.update(status='aborted',error=str(error),config_unchanged=digest(cfg)==baseline)
                (backup/'transaction.json').write_text(json.dumps(record,indent=2)+'\n')
                raise
            finally:
                if staged:staged.unlink(missing_ok=True)

    def restore(self):
        with self.locked():
            active=self.p(STATE+'/active.json')
            if not active.is_file():raise RuntimeError('No active DLS Neon installation')
            record=json.loads(active.read_text())
            if record['status']!='active':raise RuntimeError('Interrupted activation: inspect retained backup before manual recovery')
            config=record.get('config',CONFIG)
            if config not in CONFIGS:raise RuntimeError('Invalid saved configuration path')
            cfg=self.p(config)
            managed=HOOK if 'hook' in record else DROPIN
            if 'hook' in record and record['hook']!=HOOK:raise RuntimeError('Invalid saved hook path')
            control=self.p(managed)
            theme_name=record['theme'];backup_name=record['backup']
            if not re.fullmatch(r'boot/grub2?/themes/dls-neon-[A-Za-z0-9-]+',theme_name) or not re.fullmatch(r'var/lib/dls-neon-grub/backups/[A-Za-z0-9]+',backup_name):
                raise RuntimeError('Invalid saved state paths')
            theme,backup=self.p(theme_name),self.p(backup_name)
            expected=record['hook_hash'] if 'hook' in record else record['dropin_hash']
            if digest(cfg)!=record['config_after'] or digest(control)!=expected:
                raise RuntimeError('GRUB changed after activation; automatic restore would overwrite later work. See docs/RECOVERY.md')
            if tree_digest(theme)!=record['theme_hashes']:raise RuntimeError('Installed theme changed; refusing to delete it')
            if digest(backup/'grub.cfg')!=record['config_before']:raise RuntimeError('Backup checksum mismatch')
            self.run([self.tools['check'],str(backup/'grub.cfg')],check=True)
            control.unlink()
            try:atomic_copy(backup/'grub.cfg',cfg)
            except BaseException:
                record['status']='restore-interrupted';active.write_text(json.dumps(record)+'\n');raise
            record['status']='restored';(backup/'transaction.json').write_text(json.dumps(record,indent=2)+'\n');active.unlink()
            return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("install", help="Activate with a validated configuration and backup")
    install.add_argument("--source", type=Path, default=Path("/usr/share/dls-neon-grub/theme"))
    install.add_argument("--theme", choices=["event-horizon", "quantum-fabric", "sentient-atlas", "synaptic-cosmos"])
    install.add_argument("--profile", choices=GFX, default="1080p")
    install.add_argument("--timeout", type=int, default=8)
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--config", choices=CONFIGS, default=CONFIG)
    sub.add_parser("restore", help="Restore the exact pre-install configuration if unchanged")
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.action == "install":
            if not 1 <= args.timeout <= 60:
                parser.error("timeout must be between 1 and 60 seconds")
            if args.theme:
                args.source = args.source.parent / "themes" / args.theme
            args.source = args.source.resolve()
            verify_assets(args.source)
            if args.dry_run:
                print(json.dumps({"action": "preview-only", "assets": str(args.source),
                    "profile": args.profile, "gfxmode": GFX[args.profile], "timeout": args.timeout,
                    "writes": ["/boot/grub/themes/dls-neon-<asset-hash>", "/" + HOOK,
                               "/" + args.config, "/" + STATE],
                    "preserves": ["distribution boot entries", "EFI files and NVRAM", "/etc/default/grub"],
                    "reboot": False}, indent=2))
                return
        if os.geteuid() != 0:
            parser.error("run this action with sudo; install --dry-run does not need sudo")
        commands = {k: (shutil.which(v) or shutil.which(v.replace("grub-", "grub2-")) or v) for k,v in {"check":"grub-script-check","probe":"grub-probe","relpath":"grub-mkrelpath"}.items()}
        manager = Manager(config=getattr(args,"config",CONFIG), tools=commands)
        if args.action == "install":
            result = manager.install(args.source, args.profile, args.timeout)
        elif args.action == "restore":
            result = manager.restore()
        else:
            active = manager.p(STATE + "/active.json")
            result = json.loads(active.read_text()) if active.exists() else {"status": "inactive"}
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"dls-neon-theme: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
