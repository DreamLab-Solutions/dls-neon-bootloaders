# Build and test

End users should download a package from
[Releases](https://github.com/DreamLab-Solutions/dls-neon-grub/releases).
Docker images are development environments, not installation prerequisites or
release assets. Ready-to-run packages do not contain Docker, QEMU, firmware or
bootloader test binaries.

## Native Debian / Ubuntu build

Build dependencies:

```sh
sudo apt install python3 python3-pil grub-common grub-efi-amd64-bin grub2-common \
  xorriso mtools qemu-system-x86 ovmf dpkg-dev make
git clone https://github.com/DreamLab-Solutions/dls-neon-grub.git
cd dls-neon-grub
make package
make limine-package
make setup-package
python3 scripts/release.py
```

The first three targets produce GRUB portable/deb, Limine and combined packages
under `dist/`. The final command stages the four current-version packages,
`SHA256SUMS` and English release notes under `dist/release/` after integrity and
documentation checks. Never mix different versions in one release.

## Optional isolated development container

```sh
docker build -t dls-neon-test -f packaging/Dockerfile.test .
docker run --rm --network none --cap-drop ALL \
  --security-opt no-new-privileges -v "$PWD:/src" dls-neon-test \
  python3 -m unittest discover -s tests -v
```

Use an isolated development checkout: build commands write `build/` and `dist/`.
Do not pass `/boot`, EFI variables or host block devices into a container or VM.
The old `dls-neon-gui-test` image belongs to the retired Tk frontend and is not
needed for the console installer.

## Native bootloader previews

```sh
python3 scripts/preview.py --headless --theme synaptic-cosmos
python3 scripts/limine_preview.py --theme synaptic-cosmos --limine-dir /path/to/limine-binary
```

The GRUB tool uses its own disposable ISO/FAT media and OVMF. Obtain the pinned
Limine test archive using the URL/hash in `.github/workflows/limine.yml`; the
Limine preview uses disposable FAT media too. Never attach a host disk. A menu
capture is not an OS boot test. View and compare selection, submenus, console,
scrolling and the expected resolution before updating evidence.

The combined packager checks the three AI GRUB screenshots against their recorded
theme manifest and image hashes. Regenerate native evidence if those assets
change; never bypass a mismatched proof to ship stale previews.

## Documentation

English is canonical. Keep concise Italian user help under `docs/it/`; technical
evidence and release notes stay in English. Use existing verified native captures
from `docs/screenshots/` and label VM/hardware scope accurately. The packagers
include referenced screenshots and preserve relative links for offline reading.
Do not add private hardware photos, configuration reports, backups or credentials.
