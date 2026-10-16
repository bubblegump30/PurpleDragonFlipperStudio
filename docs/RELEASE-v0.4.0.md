# PurpleDragonFlipperStudio v0.4.0 — Device Integration Foundation

Neon GUI v0.4.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Explicit read-only Identify / Refresh device action in Device Dashboard for CLI connections.
- Connection-scoped adapter checks Flipper-compatible device_info responses and reports implemented capabilities.
- Shows queried name, firmware, hardware and protocol fields; unavailable values are not invented.
- Serial queries share the existing worker, block interleaved console sends, and enforce timeout/response limits.
- Rejects unsupported, incomplete, duplicate-field and wrong-model responses; ignores stale-session replies.
- Clears identity data on disconnect and transport errors; excludes device identifiers from diagnostics.

## Use

Connect the Flipper USB port in CLI mode, open Device Dashboard and click Identify / Refresh device. Let other CLI commands finish first. Nothing is sent automatically on connection. The query sends device_info followed by carriage return. Disconnect cancels; failed queries can be retried.

Only device_info is implemented. GPIO, IR transmission, SD/storage backup, app operations and battery queries remain unavailable. Identity checking is based on device-reported fields, not cryptographic authentication. No SD query is needed. This does not query the Wi-Fi Developer Board.

## Install and validation

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe beside _internal. Source users run Setup.bat then Start.bat. Verify archive checksums and export a settings backup before upgrading.

86 automated tests passed locally using synthetic device responses and mocked serial streams. Native Windows workflow validation and physical Flipper validation are separate. Physical integration remains unverified until tested on hardware.
