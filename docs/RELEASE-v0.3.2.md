# PurpleDragonFlipperStudio v0.3.2 — Connection Center

Neon GUI v0.3.2 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Detects a disappeared connected serial port and disables sending immediately when detected.
- Adds explicit connection states and manual Retry/Reconnect controls.
- Checks that the selected port is available before opening; never silently switches devices.
- Adds selectable Connection details on the Device page, including original errors.
- Provides focused recovery guidance for busy ports, missing devices, and timeouts.
- Retains matching source/Windows archive packaging and SHA-256 checksums.

## Install

Extract the whole Windows-x64 ZIP, then run PurpleDragonFlipperStudio.exe with _internal beside it. For source development, run Setup.bat then Start.bat. Export a settings backup before upgrading and verify archive hashes against SHA256SUMS.txt.

## Limits

Reconnection is manual. Port monitoring runs every 1.5 seconds while connected; serial errors can also report connection loss. A successful serial open does not verify device identity. GPIO hardware operations, IR transmission, SD backup, app installation, and telemetry still require backend integration. Physical unplug/replug behavior needs validation on Windows hardware.

## Validation

67 automated tests passed locally, including unplug handling, late-open protection, temporary discovery failures, missing-port retry, and recovery guidance. Publish after the Windows build workflow succeeds and the package has been tested on Windows.
