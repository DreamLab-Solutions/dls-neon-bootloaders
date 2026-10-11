#!/usr/bin/env python3
"""Boot real GRUB in a diskless UEFI VM, optionally save QMP screenshots."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RESOLUTIONS = {"720p": "1280x720", "1080p": "1920x1080", "1440p": "2560x1440", "4k": "3840x2160"}


def find_firmware():
    candidates = [os.environ.get("OVMF_CODE", ""),
                  "/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/ovmf/OVMF.fd"]
    return next((Path(p) for p in candidates if p and Path(p).is_file()), None)


def make_iso(profile, resolution):
    dest = ROOT / "build" / f"preview-{profile}-{resolution}"
    tree = dest / "iso"
    boot = tree / "boot/grub"
    boot.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "build/theme", boot / "themes/dls-neon", dirs_exist_ok=True)
    fonts = "\n".join(f"loadfont ($root)/boot/grub/themes/dls-neon/{p.name}"
                      for p in sorted((ROOT / "build/theme").glob("*.pf2")))
    config = f'''insmod all_video
insmod gfxterm
insmod gfxmenu
insmod png
set gfxmode={resolution}
{fonts}
terminal_output gfxterm
set theme=($root)/boot/grub/themes/dls-neon/theme-{profile}.txt
export theme
set default=0
set timeout=120
menuentry 'Ubuntu' {{
  echo 'Preview only: no host disk is attached.'
  sleep --interruptible 3
}}
submenu 'Advanced options for Ubuntu' {{
  menuentry 'Ubuntu, Linux (preview)' {{ echo 'Preview only'; sleep 3; }}
  menuentry 'Ubuntu, recovery mode (preview)' {{ echo 'Preview only'; sleep 3; }}
}}
menuentry 'UEFI Firmware Settings' {{ echo 'Preview only'; sleep 3; }}
menuentry 'Memory test (preview)' {{ echo 'Preview only'; sleep 3; }}
submenu 'Scrolling test (preview)' {{
'''
    for number in range(1, 13):
        config += f"  menuentry 'Ubuntu test entry {number:02}' {{ echo 'Preview only'; sleep 1; }}\n"
    config += "}\n"
    (boot / "grub.cfg").write_text(config)
    subprocess.run(["grub-script-check", str(boot / "grub.cfg")], check=True)
    iso = dest / "preview.iso"
    subprocess.run(["grub-mkrescue", "-d", "/usr/lib/grub/x86_64-efi", "-o", str(iso), str(tree)], check=True,
                   stdout=subprocess.DEVNULL)
    return dest, iso


class QMP:
    def __init__(self, path):
        self.sock = socket.socket(socket.AF_UNIX)
        self.sock.settimeout(10)
        self.sock.connect(str(path))
        self.stream = self.sock.makefile("rwb", buffering=0)
        self.stream.readline()
        self.command("qmp_capabilities")

    def command(self, name, **arguments):
        self.stream.write((json.dumps({"execute": name, "arguments": arguments}) + "\n").encode())
        while True:
            reply = json.loads(self.stream.readline())
            if "error" in reply:
                raise RuntimeError(reply["error"])
            if "return" in reply:
                return reply["return"]

    def key(self, code):
        self.command("human-monitor-command", **{"command-line": "sendkey " + code})
        time.sleep(0.8)

    def screenshot(self, path):
        self.command("screendump", filename=str(path), format="png")

    def close(self):
        self.stream.close()
        self.sock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=RESOLUTIONS, default="1080p")
    parser.add_argument("--resolution", choices=[*RESOLUTIONS.values(), "1024x768"], help="Test a firmware fallback")
    parser.add_argument("--headless", action="store_true", help="Capture actual GRUB screens then exit")
    parser.add_argument("--iso-only", action="store_true")
    args = parser.parse_args()
    dest, iso = make_iso(args.profile, args.resolution or RESOLUTIONS[args.profile])
    if args.iso_only:
        print(iso)
        return
    firmware = find_firmware()
    if firmware is None:
        raise SystemExit("Install ovmf / ovmf-generic, or set OVMF_CODE to its firmware path")
    qemu = os.environ.get("QEMU", "qemu-system-x86_64")
    qmp = dest / "qmp.sock"
    qmp.unlink(missing_ok=True)
    command = [qemu, "-machine", "q35", "-accel", "tcg", "-m", "256", "-vga", "std",
               "-cdrom", str(iso), "-boot", "d", "-nic", "none",
               "-no-reboot", "-qmp", f"unix:{qmp},server=on,wait=off"]
    if "CODE" in firmware.name:
        variables = Path(os.environ.get("OVMF_VARS", str(firmware.with_name(firmware.name.replace("CODE", "VARS")))))
        if not variables.is_file():
            raise SystemExit("Matching OVMF_VARS file missing; set OVMF_VARS explicitly")
        disposable = dest / "OVMF_VARS.fd"
        shutil.copy2(variables, disposable)
        command.extend(["-drive", f"if=pflash,format=raw,readonly=on,file={firmware}",
                        "-drive", f"if=pflash,format=raw,file={disposable}"])
    else:
        command.extend(["-bios", str(firmware)])
    if os.environ.get("QEMU_DATA"):
        command.extend(["-L", os.environ["QEMU_DATA"]])
    if args.headless:
        command.extend(["-display", "none"])
    else:
        command.extend(["-display", "gtk", "-name", "DLS Neon — GRUB preview"])
    print("Diskless UEFI preview; no host drives, network, or persistent firmware variables.", flush=True)
    if not args.headless:
        subprocess.run(command, check=True)
        return
    with (dest / "qemu.log").open("w") as log:
        proc = subprocess.Popen(command, stdout=log, stderr=log)
        monitor = None
        try:
            for _ in range(100):
                if proc.poll() is not None:
                    raise RuntimeError((dest / "qemu.log").read_text())
                if qmp.exists():
                    break
                time.sleep(0.1)
            monitor = QMP(qmp)
            time.sleep(18)
            monitor.screenshot(dest / "01-menu.png")
            monitor.key("down")
            monitor.screenshot(dest / "02-selected.png")
            monitor.key("ret")
            monitor.screenshot(dest / "03-submenu.png")
            monitor.key("esc")
            monitor.key("c")
            monitor.screenshot(dest / "04-console.png")
            monitor.key("esc")
            monitor.key("end")
            monitor.key("ret")
            monitor.key("end")
            monitor.screenshot(dest / "05-scrolling.png")
            monitor.command("quit")
            proc.wait(timeout=10)
        finally:
            if monitor:
                monitor.close()
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=10)
    print(f"Captured real GRUB screens in {dest}")


if __name__ == "__main__":
    main()
