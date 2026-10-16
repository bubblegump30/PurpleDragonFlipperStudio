# PurpleDragonFlipperStudio v0.7.0 — IR Workspace

Neon GUI v0.7.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Named local IR libraries with save/load/rename/confirmed removal.
- Stronger .ir header, duplicate-field/name and payload validation.
- Whole-file and selected-signal export without transmission.
- Explicit read-only IR capability probing on an identified CLI session.
- Confirmed single-command parsed/raw transmission through the existing worker.
- Byte-order/range checks, operation exclusion, disconnect and error handling.

## Use

Load a .ir file in IR Remote Studio. For device transmission, identify in CLI mode, Check IR support, select a valid supported signal, then Transmit selected signal and confirm. No SD card is required. The CLI returning without error does not confirm the appliance responded. Firmware may emit protocol-defined repeat frames. Cancellation cannot recall IR already emitted.

## Limits

Ten local libraries, 2 MB total text, 1 MB/file, 512 named signals/file. Raw CLI transmission supports up to 512 timings, two seconds total duration, whole-percent duty and 960 command characters. Valid files outside CLI limits can still be saved/exported. Libraries are not in the existing settings-backup schema; export .ir files separately. No automatic, bulk or universal brute-force transmit action is included.

## Install and validation

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe beside _internal. Source users run Setup.bat then Start.bat. Verify archive checksums.

128 automated tests pass locally, including IR parsing, byte order, ranges, capability probing, single-command framing, device errors, library persistence/corruption/rename/removal/export, confirmation and stale replies. Physical IR transmission and appliance behavior remain unverified.
