# DLS Neon Bootloaders

Read README.md and docs/DESIGN.md before changes. The original concept is retained privately outside Git. Do not reintroduce
reference images, private chat links or host reports. Generated runtime artwork
is in assets/backgrounds. Acid yellow is exactly #D9FF00.

Keep boot entries owned by the distribution. Never run grub-install, change EFI
variables, reboot, or attach host disks to a preview VM. Installation adds a dedicated theme directory and an appearance-only generator
hook, with a retained backup and syntax-validated config. Preserve every original
config byte; never rediscover or regenerate OS entries to apply a theme. Test transaction failures and restore conflicts before changing
the installer. Do not publish or change repository visibility without user approval.

Run scripts/privacy_check.py before publishing source or packages.
For agent installation follow docs/AI-INSTALL.md; documentation work does not
authorize boot writes on this machine.
