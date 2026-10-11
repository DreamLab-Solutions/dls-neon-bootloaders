#!/usr/bin/env python3
"""Transactional Ubuntu/Debian GRUB theme activation. Standard library only."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
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
    return re.findall(r"^\s*(?:menuentry|submenu)\s+(.+?)(?:\s*\{|$)", text, re.MULTILINE)


class Manager:
    # root and runner are injectable for isolated transaction tests, not exposed by CLI.
    def __init__(self, root=Path("/"), runner=subprocess.run):
        self.root = Path(root)
        self.run = runner

    def p(self, relative):
        path = self.root / relative
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != self.root):
            raise RuntimeError(f"Refusing symlink in system path: {path}")
        return path

    @contextmanager
    def locked(self):
        state = self.p(STATE)
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.p(STATE + "/lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield

    def install(self, source, profile, timeout):
        verify_assets(source)
        cfg, dropin = self.p(CONFIG), self.p(DROPIN)
        if not cfg.is_file() or not self.p("etc/default/grub").is_file():
            raise RuntimeError("Expected Ubuntu/Debian GRUB paths were not found")
        if not boot_entries(cfg.read_text()):
            raise RuntimeError("Current GRUB configuration has no boot entries")
        if dropin.exists():
            raise RuntimeError("An activation already exists; restore it before installing again")
        if self.p(STATE + "/active.json").exists():
            raise RuntimeError("An active or interrupted transaction exists; inspect status first")
        with self.locked():
            # Recheck after acquiring the lock.
            if dropin.exists() or self.p(STATE + "/active.json").exists():
                raise RuntimeError("An activation already exists")
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            asset_id = hashlib.sha256((source / "manifest.json").read_bytes()).hexdigest()[:12]
            theme_rel = f"boot/grub/themes/{NAME}-{asset_id}-{stamp}"
            target = self.p(theme_rel)
            if target.exists():
                raise RuntimeError(f"Preserving existing directory: {target}")
            backup = self.p(STATE + "/backups/" + stamp)
            backup.mkdir(parents=True, mode=0o700)
            shutil.copy2(cfg, backup / "grub.cfg")
            shutil.copy2(self.p("etc/default/grub"), backup / "grub-defaults.reference")
            if dropin.parent.exists():
                shutil.copytree(dropin.parent, backup / "grub.d.reference")
            record = {"backup": str(backup.relative_to(self.root)), "theme": theme_rel,
                      "profile": profile, "timeout": timeout, "status": "preparing",
                      "config_before": digest(cfg), "theme_hashes": tree_digest(source)}
            (backup / "transaction.json").write_text(json.dumps(record, indent=2) + "\n")
            active = self.p(STATE + "/active.json")
            active.write_text(json.dumps(record, indent=2) + "\n")
            staged = None
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, target)
                verify_assets(target)
                dropin.parent.mkdir(parents=True, exist_ok=True)
                # Let GRUB choose a supported fallback without altering kernel gfxpayload.
                dropin.write_text(
                    "# Managed by dls-neon-grub; restore with dls-neon-theme restore\n"
                    f"GRUB_THEME=/{theme_rel}/theme-{profile}.txt\n"
                    "GRUB_TIMEOUT_STYLE=menu\n"
                    f"GRUB_TIMEOUT={timeout}\n"
                    f"GRUB_GFXMODE={GFX[profile]},1280x720,1024x768,auto\n"
                    "GRUB_TERMINAL_OUTPUT=gfxterm\n")
                os.chmod(dropin, 0o644)
                fd, staged_name = tempfile.mkstemp(prefix=".dls-neon-candidate-", dir=cfg.parent)
                os.close(fd)
                staged = Path(staged_name)
                self.run(["grub-mkconfig", "-o", str(staged)], check=True)
                self.run(["grub-script-check", str(staged)], check=True)
                text = staged.read_text()
                if f"/{theme_rel}/theme-{profile}.txt" not in text or "insmod gfxmenu" not in text:
                    raise RuntimeError("Generated configuration did not activate the theme")
                if boot_entries(text) != boot_entries((backup / "grub.cfg").read_text()):
                    raise RuntimeError("Boot entries changed during generation; review before activation")
                if digest(cfg) != record["config_before"]:
                    raise RuntimeError("GRUB configuration changed concurrently; preserving it")
                # Preserve access mode, then publish only the validated configuration.
                os.chmod(staged, cfg.stat().st_mode & 0o777)
                record.update(status="active", config_after=digest(staged), dropin_hash=digest(dropin))
                (backup / "transaction.json").write_text(json.dumps(record, indent=2) + "\n")
                active.write_text(json.dumps(record, indent=2) + "\n")
                os.replace(staged, cfg)
                return record
            except BaseException:
                # The live config is replaced only at the end, so generation errors keep it intact.
                dropin.unlink(missing_ok=True)
                if target.exists():
                    shutil.rmtree(target)
                active.unlink(missing_ok=True)
                raise
            finally:
                if staged:
                    staged.unlink(missing_ok=True)
                    Path(str(staged) + ".new").unlink(missing_ok=True)

    def restore(self):
        with self.locked():
            active = self.p(STATE + "/active.json")
            if not active.is_file():
                raise RuntimeError("No active DLS Neon installation")
            record = json.loads(active.read_text())
            if record["status"] != "active":
                raise RuntimeError("Interrupted activation: inspect retained backup before manual recovery")
            cfg, dropin = self.p(CONFIG), self.p(DROPIN)
            theme = self.p(record["theme"])
            backup = self.p(record["backup"])
            if digest(cfg) != record["config_after"] or digest(dropin) != record["dropin_hash"]:
                raise RuntimeError("GRUB changed after activation; automatic restore would overwrite later work. See docs/RECOVERY.md")
            if tree_digest(theme) != record["theme_hashes"]:
                raise RuntimeError("Installed theme changed; refusing to delete it")
            if digest(backup / "grub.cfg") != record["config_before"]:
                raise RuntimeError("Backup checksum mismatch")
            self.run(["grub-script-check", str(backup / "grub.cfg")], check=True)
            # Removing our drop-in leaves distro defaults untouched. Retain assets and backups.
            dropin.unlink()
            try:
                atomic_copy(backup / "grub.cfg", cfg)
            except BaseException:
                # Leave an explicit record; the active config still points at retained assets.
                record["status"] = "restore-interrupted"
                active.write_text(json.dumps(record, indent=2) + "\n")
                raise
            record["status"] = "restored"
            (backup / "transaction.json").write_text(json.dumps(record, indent=2) + "\n")
            active.unlink()
            return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    install = sub.add_parser("install", help="Activate with a validated configuration and backup")
    install.add_argument("--source", type=Path, default=Path("/usr/share/dls-neon-grub/theme"))
    install.add_argument("--profile", choices=GFX, default="1080p")
    install.add_argument("--timeout", type=int, default=8)
    install.add_argument("--dry-run", action="store_true")
    sub.add_parser("restore", help="Restore the exact pre-install configuration if unchanged")
    sub.add_parser("status")
    args = parser.parse_args()
    try:
        if args.action == "install":
            if not 1 <= args.timeout <= 60:
                parser.error("timeout must be between 1 and 60 seconds")
            args.source = args.source.resolve()
            verify_assets(args.source)
            if args.dry_run:
                print(json.dumps({"action": "preview-only", "assets": str(args.source),
                    "profile": args.profile, "gfxmode": GFX[args.profile], "timeout": args.timeout,
                    "writes": ["/boot/grub/themes/dls-neon-<asset-hash>", "/" + DROPIN,
                               "/" + CONFIG, "/" + STATE],
                    "preserves": ["distribution boot entries", "EFI files and NVRAM", "/etc/default/grub"],
                    "reboot": False}, indent=2))
                return
        if os.geteuid() != 0:
            parser.error("run this action with sudo; install --dry-run does not need sudo")
        manager = Manager()
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
