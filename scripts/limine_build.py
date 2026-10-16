#!/usr/bin/env python3
"""Package data only; does not inspect or modify host boot files."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
THEMES = {
    'event-horizon': ('portal.png', 'Event Horizon'),
    'quantum-fabric': ('quantum-fabric.png', 'Quantum Fabric'),
    'sentient-atlas': ('sentient-atlas.png', 'Sentient Atlas'),
    'synaptic-cosmos': ('synaptic-cosmos.png', 'Synaptic Cosmos'),
}


def appearance(asset, title="Event Horizon"):
    return f'''# DreamLab {title} — native Limine 12.8 interface
wallpaper: boot():/dls-neon-limine/{asset}/background.png
wallpaper_style: stretched
interface_branding: DreamLab | {title}
interface_branding_color: D9FF00
interface_help_color: 00A49A
interface_help_color_bright: D9FF00
term_background: B0071723
term_foreground: E7F2EE
term_foreground_bright: D9FF00
term_background_bright: 071723
term_palette: 071723;E06C75;00A49A;D9FF00;7AA2F7;8B5CF6;56B6C2;E7F2EE
term_palette_bright: 273743;FF7A85;30D4BA;D9FF00;9AC2FF;AB7CFF;76D6E2;FFFFFF
term_margin: 100
term_margin_gradient: 8
'''


def build_data(out, filename, title):
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy2(ROOT / 'assets/backgrounds' / filename, out / 'background.png')
    key = hashlib.sha256((out / 'background.png').read_bytes()).hexdigest()[:16]
    (out / 'appearance.conf').write_text(appearance(key, title))
    manifest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(out.iterdir())}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {'title': title, 'asset': key, 'source_pixels': [1672, 941]}


def main():
    from setup_package import copy_docs
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--theme', choices=THEMES, default='event-horizon')
    args = parser.parse_args()
    catalog = {}
    for slug, (filename, title) in THEMES.items():
        catalog[slug] = build_data(ROOT / 'build/themes' / slug, filename, title)
    out = ROOT / 'build/limine'
    build_data(out, *THEMES[args.theme])
    (ROOT / 'build/catalog.json').write_text(json.dumps(catalog, indent=2) + '\n')
    version = (ROOT / 'VERSION').read_text().strip()
    stage = ROOT / 'build/limine-package' / ('dls-neon-limine-' + version)
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    shutil.copytree(out, stage / 'data')
    shutil.copytree(ROOT / 'build/themes', stage / 'themes')
    shutil.copy2(ROOT / 'build/catalog.json', stage / 'catalog.json')
    shutil.copy2(ROOT / 'scripts/limine_manager.py', stage / 'dls-neon-limine')
    shutil.copy2(ROOT / 'scripts/limine_backup.py', stage / 'backup-read-only.py')
    for name in ['LICENSE', 'LICENSE-MIT', 'ARTWORK-LICENSE.md']:
        shutil.copy2(ROOT / name, stage / name)
    shutil.copy2(ROOT / 'README.md', stage / 'README.md')
    shutil.copy2(ROOT / 'VERSION', stage / 'VERSION')
    copy_docs(stage / 'docs')
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / (stage.name + '.tar.gz')
    with tarfile.open(archive, 'w:gz') as tar:
        tar.add(stage, arcname=stage.name)
    (dist / 'SHA256SUMS-limine').write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + '  ' + archive.name + '\n')
    print(archive)


if __name__ == '__main__':
    main()
