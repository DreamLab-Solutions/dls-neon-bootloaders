#!/usr/bin/env python3
"""Build the combined console installer; never reads host boot configuration."""
import hashlib
import json
import re
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
THEMES = {'event-horizon':'Event Horizon','quantum-fabric':'Quantum Fabric',
          'sentient-atlas':'Sentient Atlas','synaptic-cosmos':'Synaptic Cosmos'}



def copy_docs(target):
    # Runtime keeps documentation and directly linked screenshots; bulk test captures stay in Git.
    shutil.copytree(ROOT/'docs',target,ignore=shutil.ignore_patterns('*.png'))
    for document in (ROOT/'docs').rglob('*.md'):
        for name in re.findall(r'\((screenshots/[^)]+\.png)\)',document.read_text()):
            source=ROOT/'docs'/name
            if source.is_file():
                destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(source,destination)


def main():
    version=(ROOT/'VERSION').read_text().strip()
    target=ROOT/'build'/f'dls-neon-setup-{version}'
    if target.exists(): shutil.rmtree(target)
    target.mkdir(parents=True)
    for src,dst in [('dls_setup.py','dls-neon-setup'),('theme_manager.py','grub_manager.py'),('limine_manager.py','limine_manager.py')]:
        shutil.copy2(ROOT/'scripts'/src,target/dst)
    catalog={}
    for backend in ('grub','limine'):
        src=ROOT/'build'/('grub-themes' if backend=='grub' else 'themes')
        shutil.copytree(src,target/backend/'themes')
        (target/'previews'/backend).mkdir(parents=True)
    for slug,title in THEMES.items():
        catalog[slug]={'title':title,'preview':{}}
        for backend in ('grub','limine'):
            catalog[slug][backend]=f'{backend}/themes/{slug}'
            name=f'{backend}-1080p.png' if slug=='event-horizon' else f'{backend}-{slug}-1080p.png'
            source=ROOT/'docs/screenshots'/name
            if backend=='grub' and slug!='event-horizon':
                proof=json.loads(source.with_name(name.replace('.png','-evidence.json')).read_text())
                actual=hashlib.sha256(source.read_bytes()).hexdigest()
                if proof['theme']!=slug or actual!=proof['screenshots']['01-menu.png']:
                    raise RuntimeError('Unverified GRUB preview: '+slug)
                theme_manifest=ROOT/'build/grub-themes'/slug/'manifest.json'
                if proof['theme_manifest_sha256']!=hashlib.sha256(theme_manifest.read_bytes()).hexdigest():
                    raise RuntimeError('GRUB theme changed since rendering: '+slug)
            shutil.copy2(source,target/'previews'/backend/(slug+'.png'))
            catalog[slug]['preview'][backend]=f'previews/{backend}/{slug}.png'
    (target/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    for name in ('LICENSE','LICENSE-MIT','ARTWORK-LICENSE.md'):
        shutil.copy2(ROOT/name,target/name)
    readme=(ROOT/'docs/INSTALLER.md').read_text().replace('(OMARCHY.md)','(docs/OMARCHY.md)').replace('(RECOVERY.md)','(docs/RECOVERY.md)')
    (target/'README.md').write_text(readme)
    copy_docs(target/'docs')
    files={str(p.relative_to(target)):hashlib.sha256(p.read_bytes()).hexdigest()
           for p in sorted(target.rglob('*')) if p.is_file()}
    (target/'manifest.json').write_text(json.dumps(files,indent=2)+'\n')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    archive=dist/(target.name+'.tar.gz')
    with tarfile.open(archive,'w:gz') as t: t.add(target,arcname=target.name)
    (dist/'SHA256SUMS-setup').write_text(hashlib.sha256(archive.read_bytes()).hexdigest()+'  '+archive.name+'\n')
    print(archive)


if __name__=='__main__':main()
