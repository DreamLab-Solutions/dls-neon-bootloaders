#!/usr/bin/env python3
"""Real Limine 12.8 UEFI rendering; disposable FAT image, no host disks/network."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image
from preview import QMP, find_firmware
from limine_manager import candidate

ROOT = Path(__file__).resolve().parents[1]


class Monitor(QMP):
    def screenshot(self, path):
        ppm = path.with_suffix('.ppm')
        self.command('screendump', filename=str(ppm))
        with Image.open(ppm) as screen:
            screen.save(path)
        ppm.unlink()


def submenu_steps(baseline):
    titles = [line.strip() for line in baseline.decode().splitlines() if line.lstrip().startswith('/')]
    depths = [len(title) - len(title.lstrip('/')) for title in titles]
    collapsed = None
    visible = []
    for i, title in enumerate(titles):
        depth = depths[i]
        if collapsed is not None and depth > collapsed:
            continue
        collapsed = None
        directory = i + 1 < len(titles) and depths[i + 1] > depth
        visible.append((title, directory))
        if directory and not title.lstrip('/').startswith('+'):
            collapsed = depth
    targets = [i for i, (_, directory) in enumerate(visible) if directory and i > 0]
    if not targets:
        raise RuntimeError('Preview fixture requires a visible non-first directory for navigation checks')
    return targets[0]


def branding_visible(screen):
    width, height = screen.size
    area = screen.convert('RGB').crop((int(width*.2), 0, int(width*.8), min(250, int(height*.3))))
    colors = area.getcolors(area.width * area.height) or []
    return sum(n for n, color in colors if color == (217, 255, 0)) > 30


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', choices=['1920x1080', '1280x720', '1024x768'], default='1920x1080')
    parser.add_argument('--theme', choices=['event-horizon', 'quantum-fabric', 'sentient-atlas', 'synaptic-cosmos'])
    parser.add_argument('--entry-titles', type=Path, help='Private JSON list of native titles; boot paths remain demo-only')
    parser.add_argument('--limine-dir', type=Path, default=Path('/usr/share/limine'))
    args = parser.parse_args()
    dest = ROOT / 'build' / ('limine-preview-' + ((args.theme + '-') if args.theme else '') + args.resolution)
    dest.mkdir(parents=True, exist_ok=True)
    image = dest / 'esp.img'
    with image.open('wb') as stream:
        stream.truncate(64 * 1024 * 1024)
    subprocess.run(['mformat', '-i', str(image), '-F', '::'], check=True)
    def md(path):
        subprocess.run(['mmd', '-i', str(image), '::/' + path], check=True)
    def cp(source, target):
        subprocess.run(['mcopy', '-i', str(image), str(source), '::/' + target], check=True)
    md('EFI'); md('EFI/BOOT'); md('dls-neon-limine')
    data = ROOT / 'build/themes' / args.theme if args.theme else ROOT / 'build/limine'
    key = hashlib.sha256((data / 'background.png').read_bytes()).hexdigest()[:16]
    md('dls-neon-limine/' + key)
    cp(data / 'background.png', 'dls-neon-limine/' + key + '/background.png')
    binary = args.limine_dir / 'BOOTX64.EFI'
    cp(binary, 'EFI/BOOT/BOOTX64.EFI')
    baseline = f'''timeout: no
interface_resolution: {args.resolution}
/Omarchy (DEMO — no kernel)
 protocol: efi
 path: boot():/demo-omarchy.efi
/Snapshots (DEMO)
//Omarchy snapshot 1 (DEMO)
 protocol: efi
 path: boot():/demo-snapshot.efi
//Omarchy snapshot 2 (DEMO)
 protocol: efi
 path: boot():/demo-snapshot2.efi
/Ubuntu — second disk (DEMO)
 protocol: efi
 path: boot():/demo-ubuntu.efi
/Long entry test — Omarchy kernel fallback and recovery (DEMO)
 protocol: efi
 path: boot():/demo-fallback.efi
'''.encode()
    if args.entry_titles:
        titles = json.loads(args.entry_titles.read_text())
        baseline = f'timeout: no\ninterface_resolution: {args.resolution}\n'
        for n, title in enumerate(titles):
            if not isinstance(title, str) or not title.startswith('/') or '\n' in title or '\r' in title:
                raise RuntimeError('Invalid entry title fixture')
            baseline += title + '\n'
            depth = len(title) - len(title.lstrip('/'))
            next_depth = len(titles[n+1]) - len(titles[n+1].lstrip('/')) if n+1 < len(titles) else 0
            if next_depth <= depth:
                baseline += f' protocol: efi\n path: boot():/demo-{n}.efi\n'
        baseline = baseline.encode()
    config = dest / 'limine.conf'
    config.write_bytes(candidate(baseline, (data / 'appearance.conf').read_text()))
    cp(config, 'limine.conf')
    firmware = find_firmware()
    if firmware is None:
        raise RuntimeError('OVMF firmware missing')
    qmp = dest / 'qmp.sock'
    qmp.unlink(missing_ok=True)
    variables = dest / 'OVMF_VARS.fd'
    shutil.copy2(firmware.with_name(firmware.name.replace('CODE', 'VARS')), variables)
    command = ['qemu-system-x86_64', '-machine', 'q35', '-accel', 'tcg', '-m', '256',
               '-device', 'VGA,vgamem_mb=64', '-display', 'none', '-nic', 'none',
               '-drive', f'if=pflash,format=raw,readonly=on,file={firmware}',
               '-drive', f'if=pflash,format=raw,file={variables}',
               '-drive', f'format=raw,file={image}', '-no-reboot',
               '-qmp', f'unix:{qmp},server=on,wait=off']
    with (dest / 'qemu.log').open('w') as log:
        proc = subprocess.Popen(command, stdout=log, stderr=log)
        monitor = None
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError((dest / 'qemu.log').read_text())
                if qmp.exists(): break
                time.sleep(.1)
            monitor = Monitor(qmp)
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                monitor.screenshot(dest / '01-menu.png')
                with Image.open(dest / '01-menu.png') as screen:
                    if screen.size == tuple(map(int, args.resolution.split('x'))) and branding_visible(screen):
                        break
                time.sleep(1)
            else:
                raise RuntimeError('No verified native Limine palette at requested mode')
            for _ in range(submenu_steps(baseline)):
                monitor.key('down')
            monitor.screenshot(dest / '02-selected.png')
            monitor.key('ret')
            monitor.screenshot(dest / '03-submenu.png')
            for path in [dest / '02-selected.png', dest / '03-submenu.png']:
                with Image.open(path) as screen:
                    if not branding_visible(screen):
                        raise RuntimeError('Native menu branding missing after navigation; possible demo boot panic')
            snapshots = [p.read_bytes() for p in sorted(dest.glob('0[1-3]-*.png'))]
            if len(set(snapshots)) != 3:
                raise RuntimeError('Menu, selection and submenu did not produce distinct screens')
            monitor.command('quit')
            proc.wait(timeout=10)
        finally:
            if monitor: monitor.close()
            if proc.poll() is None:
                proc.terminate(); proc.wait(timeout=10)
    evidence = {'theme': args.theme or 'event-horizon', 'resolution': args.resolution, 'limine_binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
                'qemu': subprocess.check_output(['qemu-system-x86_64', '--version'], text=True).splitlines()[0],
                'scope': 'real bootloader graphics, directory selection and submenu expansion; demo boot paths; no OS kernel or hardware boot tested',
                'submenu_navigation': 'derived from initially visible entry hierarchy; native branding verified after each action',
                'screenshots': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.glob('0[1-3]-*.png'))}}
    (dest / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence, indent=2))


if __name__ == '__main__':
    main()
