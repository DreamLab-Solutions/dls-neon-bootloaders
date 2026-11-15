#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

download_verified() {
  local url=$1 expected=$2 destination=$3
  curl --fail --location --retry 3 --output "$destination" "$url"
  printf '%s  %s\n' "$expected" "$destination" | sha256sum --check
}

validate_privacy() (
  python3 scripts/privacy_check.py
  local tools_dir
  tools_dir=$(mktemp -d)
  trap 'rm -rf -- "$tools_dir"' EXIT
  download_verified \
    https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz \
    551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb \
    "$tools_dir/gitleaks.tar.gz"
  tar -xzf "$tools_dir/gitleaks.tar.gz" -C "$tools_dir" gitleaks
  "$tools_dir/gitleaks" git . --redact=100 --no-banner --log-opts=--all
)

validate_grub() {
  make package
  python3 scripts/preview.py --headless --profile 1080p
  python3 scripts/preview.py --headless --profile 720p
  for theme in quantum-fabric sentient-atlas synaptic-cosmos; do
    python3 scripts/preview.py --headless --theme "$theme"
  done
  make setup-package
  python3 scripts/release.py
  PYTHONPATH=tests python3 -m unittest test_setup.ConsoleTests -v
}

validate_limine() (
  local tools_dir
  tools_dir=$(mktemp -d)
  trap 'rm -rf -- "$tools_dir"' EXIT
  download_verified \
    https://github.com/Limine-Bootloader/Limine/releases/download/v12.8.0/limine-binary.tar.gz \
    e21b0a9ce1cf83e79eb0f3fa6d6de49a1b6d1288df11e2232e41c9f4916b673d \
    "$tools_dir/limine-binary.tar.gz"
  tar -xzf "$tools_dir/limine-binary.tar.gz" -C "$tools_dir"
  make limine-package
  python3 scripts/limine_preview.py --limine-dir "$tools_dir/limine-binary" --resolution 1920x1080
  for theme in quantum-fabric sentient-atlas synaptic-cosmos; do
    python3 scripts/limine_preview.py --limine-dir "$tools_dir/limine-binary" --theme "$theme"
  done
  python3 scripts/limine_preview.py --limine-dir "$tools_dir/limine-binary" \
    --theme synaptic-cosmos --resolution 1024x768
)

case "${1:-all}" in
  all)
    validate_privacy
    validate_grub
    validate_limine
    ;;
  privacy) validate_privacy ;;
  grub) validate_grub ;;
  limine) validate_limine ;;
  *) printf 'Usage: %s [all|privacy|grub|limine]\n' "${0##*/}" >&2; exit 2 ;;
esac
