# PurpleDragonFlipperStudio v0.3.1 — Release Cleanup

Neon GUI v0.3.1 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Corrected Windows executable and source installation instructions.
- Updated the application credit and searchable Help Center release guidance.
- Added matching source and Windows archive packaging from one commit.
- Added archive SHA-256 checksums and a release manifest identifying the source commit.
- Retained the compact GPIO layout correction and existing neon interface.

## Install

Extract the entire Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe. Keep _internal beside it. Python is not required for the Windows package. For source development, extract the Source ZIP, run Setup.bat, then Start.bat.

Export a settings backup before upgrading. Verify the archive hashes against SHA256SUMS.txt.

## Hardware support

Serial text transport and local tools are available. GPIO hardware operations, IR transmission, SD backup, app installation, and telemetry still require backend integration. Opening a serial port does not verify device identity. Physical hardware integration remains unverified.

## Validation

Publish only after the Windows workflow tests and packaging pass and the packaged app has been checked on Windows. Packaging success is not hardware validation.
