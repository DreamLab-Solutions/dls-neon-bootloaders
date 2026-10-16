# Design and provenance

DreamLab Boot Themes uses teal, purple and acid yellow `#D9FF00`. Boot labels,
selection and operational text are rendered by the bootloader, never embedded
into the three AI universe backgrounds. See the [gallery](THEMES.md).

## Composition

Event Horizon retains the approved portal concept. Its GRUB menu is positioned
on the left; Limine's native centred menu prompted the three newer compositions.
Quantum Fabric, Sentient Atlas and Synaptic Cosmos keep a quiet central area
for both bootloaders. Synaptic Cosmos is the console's default selection.

GRUB uses native `boot_menu` widgets, nine-slice selection/scrollbar assets,
DejaVu Sans Mono PF2 fonts and an opaque console. Font/layout profiles cover
720p, 1080p, 1440p and 4K. Limine uses its own menu/bitmap typography and
appearance keys. It cannot reproduce GRUB's arbitrary positioning or fonts.
The source artwork is 1672×941; scaling is not a new native 4K master.

## Artwork sources

The original concept is retained unmodified in a private archive outside Git.
Event Horizon's runtime `assets/backgrounds/portal.png` was generated/edited
with OpenAI image generation to remove simulated menu content; the recorded
prompt remains in `artwork-prompt.txt`. The supplied concept itself is not
covered by the runtime artwork grant and is not distributed in this repository.

The user selected proposals 2–4 for the package on 2026-10-16. Exact prompts,
palette values and image hashes are recorded in
[ai-artwork-provenance.json](ai-artwork-provenance.json). The original Limine
screenshot was used as a layout reference. Runtime artwork pixels are copied
without retouching; the installer adapts native appearance settings.

Code/documentation and runtime artwork have separate grants; consult the
component licensing files included in every package. AI provenance is disclosed;
exclusive copyright, human-only authorship and third-party clearance are not
claimed. DreamLab marks remain reserved.

## Project boundaries

The canonical repository is
[DreamLab-Solutions/dls-neon-grub](https://github.com/DreamLab-Solutions/dls-neon-grub),
maintained by DreamLab Solutions. Private design links and local host paths
are excluded from publication history.
It is an independent DreamLab product. It does not modify the DreamLab web
platform, Sunnyday foundations or EzRider components. Durable cross-environment
decisions are recorded through the shared Project Registry; source and detailed
validation evidence remain in this repository.
