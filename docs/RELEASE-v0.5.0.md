# PurpleDragonFlipperStudio v0.5.0 — SD File Manager

Neon GUI v0.5.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- New SD Files workspace with root/up navigation and folder browsing.
- Explicit SD probe after device identification; unavailable storage keeps actions disabled.
- Binary upload/download up to 4 MiB with progress and MD5 integrity verification.
- Verified atomic local downloads and staged remote uploads to new names only.
- New folders and confirmed deletion of files or empty folders.
- /ext-only path validation, serialized operations, and stale-session protection.
- Scrollable sidebar and responsive tab layout accommodate the new workspace.

## Use

Connect in CLI mode → Device Dashboard → Identify / Refresh device → SD Files → Refresh / Probe SD. An installed, mounted SD card is required for storage actions. Ctrl+9 opens the workspace.

Upload refuses existing remote names. There is no format, recursive delete, or overwrite action. Cancel & disconnect and storage failures close the port; reconnect, identify and probe before retrying. A failed upload may leave a `.pd-upload-*.part` stage or a newly created partial destination. Inspect before cleanup; device-side work may finish after disconnection.

## Install and validation

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe beside _internal. Source users run Setup.bat then Start.bat. Verify release archive checksums.

102 automated tests pass locally, including a synthetic binary CLI emulator, integrity failures, overwrite races, cancellation, framing limits, atomic replacement failures, gating, deletion confirmation and stale replies. Windows packaging is separate from physical SD-card validation, which remains pending. GPIO, IR transmission, full SD backup, app installation and battery telemetry remain unavailable.
