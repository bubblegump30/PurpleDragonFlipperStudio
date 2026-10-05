# PurpleDragonFlipperStudio v0.3.3 — Console QoL

Neon GUI v0.3.3 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Save, load, and remove up to 50 persistent local command favorites; loading never sends.
- Toggle receive timestamps without changing raw captured text.
- Pause display while continuing bounded capture, then Resume to catch up.
- Export raw UTF-8 text or JSON with receive timestamps and retention status, including paused data.
- Preserve original line endings in text exports on Windows.
- Clear console clears both display and retained capture.

Retention is limited to 200,000 characters and 2,000 receive chunks. The display also keeps up to 2,000 text blocks. Receive timestamps describe chunks, not protocol messages or guaranteed complete lines. Favorites and timestamp preferences persist locally but are not included in the existing settings backup format. Pause state resets on launch.

## Install

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe with _internal beside it. For source development, run Setup.bat then Start.bat. Export a settings backup before upgrading and verify the release archive checksums.

## Validation and hardware

73 automated tests pass locally. Windows build and packaging must pass before distribution. Physical hardware integration remains unverified; GPIO, IR transmission, SD backup, app installation, and telemetry still require the backend adapter.
