# DLS Neon GRUB

Read README.md and docs/DESIGN.md before changes. The approved concept is preserved
in assets/reference. Generated artwork is in assets/backgrounds; do not overwrite
the reference. Acid yellow is exactly #D9FF00.

Keep boot entries owned by the distribution. Never run grub-install, change EFI
variables, reboot, or attach host disks to a preview VM. Installation adds a dedicated theme directory and an appearance-only generator
hook, with a retained backup and syntax-validated config. Preserve every original
config byte; never rediscover or regenerate OS entries to apply a theme. Test transaction failures and restore conflicts before changing
the installer. Do not publish or change repository visibility without user approval.
