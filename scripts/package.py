#!/usr/bin/env python3
"""Create a portable archive and a Debian package that never activates itself."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tarfile
from setup_package import copy_docs

ROOT = Path(__file__).resolve().parents[1]


def main():
    version = (ROOT / "VERSION").read_text().strip()
    name = f"dls-neon-grub-{version}"
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    stage = ROOT / "build/package" / name
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    shutil.copytree(ROOT / "build/theme", stage / "theme")
    shutil.copytree(ROOT / "build/grub-themes", stage / "themes")
    copy_docs(stage / "docs")
    for file in ["README.md", "LICENSE", "LICENSE-MIT", "ARTWORK-LICENSE.md", "VERSION"]:
        shutil.copy2(ROOT / file, stage / file)
    shutil.copy2(ROOT / "scripts/theme_manager.py", stage / "dls-neon-theme")
    (stage / "dls-neon-theme").chmod(0o755)
    (stage / "install.sh").write_text('''#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$HERE/dls-neon-theme" install --source "$HERE/theme" "$@"
''')
    (stage / "install.sh").chmod(0o755)
    with tarfile.open(dist / f"{name}.tar.gz", "w:gz") as archive:
        archive.add(stage, arcname=name)
    deb = ROOT / "build/debian"
    if deb.exists():
        shutil.rmtree(deb)
    (deb / "DEBIAN").mkdir(parents=True)
    data = deb / "usr/share/dls-neon-grub"
    data.mkdir(parents=True)
    shutil.copytree(ROOT / "build/theme", data / "theme")
    shutil.copytree(ROOT / "build/grub-themes", data / "themes")
    doc = deb / "usr/share/doc/dls-neon-grub"
    copy_docs(doc / "docs")
    shutil.copy2(ROOT / "README.md", doc / "README.md")
    shutil.copy2(ROOT / "LICENSE", doc / "LICENSE")
    shutil.copy2(ROOT / "LICENSE", doc / "copyright")
    shutil.copy2(ROOT / "LICENSE-MIT", doc / "LICENSE-MIT")
    shutil.copy2(ROOT / "ARTWORK-LICENSE.md", doc / "ARTWORK-LICENSE.md")
    binary = deb / "usr/bin/dls-neon-theme"
    binary.parent.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/theme_manager.py", binary)
    binary.chmod(0o755)
    (deb / "DEBIAN/control").write_text(f'''Package: dls-neon-grub
Version: {version}
Section: misc
Priority: optional
Architecture: all
Maintainer: DreamLab Solutions <info@dreamlab.solutions>
Depends: python3, grub-common, grub2-common
Homepage: https://github.com/DreamLab-Solutions/dls-neon-bootloaders
Description: DreamLab space and AI theme collection for GNU GRUB (preview)
 Native GRUB theme with teal, purple and acid yellow accents.
 Installing the package only stages files; activate explicitly using
 dls-neon-theme install. Includes transactional backup and restore.
''')
    subprocess.run(["dpkg-deb", "--root-owner-group", "--build", str(deb),
                    str(dist / f"dls-neon-grub_{version}_all.deb")], check=True)
    outputs = [dist / f"{name}.tar.gz", dist / f"dls-neon-grub_{version}_all.deb"]
    (dist / "SHA256SUMS").write_text("".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in outputs))
    for p in outputs:
        print(f"{p} ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
