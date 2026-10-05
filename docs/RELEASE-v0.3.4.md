# PurpleDragonFlipperStudio v0.3.4 — Workspace Polish

Neon GUI v0.3.4 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Draggable GPIO panel dividers with separate saved compact and wide proportions.
- Compact layouts stack panels vertically; wide layouts use horizontal dividers.
- Ctrl+Shift+0 resets panel sizes without changing presets or appearance.
- Ctrl+K opens the workspace selector; Ctrl+F reveals Console search; Ctrl+L reveals the command draft.
- Added accessible control names and clearer input, pause, pin, and panel tooltips.
- Cached multiple-resolution icons for sharper high-DPI rendering.
- Fixed transient horizontal overflow when switching to compact layout.

Panel sizes persist locally and are not included in settings backups. The established neon design and existing workspace functions are retained.

## Install

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe with _internal beside it. For source development, run Setup.bat then Start.bat. Export a settings backup before upgrading and verify the archive checksums.

## Validation

77 automated tests passed locally, including panel orientation/persistence/reset, invalid-size recovery, keyboard focus, and no horizontal workspace overflow. Offscreen workspace checks passed at 150% and 200% scaling. Native Windows build validation is separate from on-device hardware testing; hardware backend integration remains unverified.
