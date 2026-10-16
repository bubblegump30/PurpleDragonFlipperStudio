# PurpleDragonFlipperStudio v1.0.0 — Stable Public Release

Neon GUI v1.0.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

The 1.0 desktop release brings together the neon interface, USB serial console, digital GPIO Workbench, IR libraries, SD File Manager, verified backup/restore workflows and compatibility reporting.

## Included

- Nine workspace tabs with synchronized navigation, eight themes, saved window/panel layouts and searchable F1 help.
- Explicit device identification and per-session support checks; no automatic commands on startup or connection.
- Confirmed GPIO output, armed LOW/HIGH, input reads/polling and history.
- IR library management, validation, exports and confirmed selected-signal transmission.
- Binary SD transfers and bounded backups with verified restoration into a new folder.
- Connection isolation, cancellation, error recovery and identifier-free compatibility reports.
- New public quick start and dependency notices inside the Windows ZIP.
- New packaged Windows launch/render/exit check and offline archive verifier in the release workflow.

## Install

Download the Windows-x64 ZIP. Extract the entire archive into a new folder and run PurpleDragonFlipperStudio.exe. Keep _internal beside it. Read README-FIRST.txt. No separate Python installation or administrator rights are required.

Source users run Setup.bat, then Start.bat. Release files include SHA256SUMS.txt and release-manifest.json. Verify archive hashes against the trusted release. The included verify_release.py checks hashes, archive structure, version and commit metadata without extracting or running the ZIP contents; it is not code signing.

## Upgrade

Export a settings backup and separately export IR libraries before replacing an older install. Extract 1.0 into a new folder; existing local settings are reused. Keep the old application folder for rollback. Restoring settings replaces the included preferences/presets after confirmation; not every local store is included in that schema.

## Compatibility and known limits

**Stable Public Release describes the desktop software milestone. Physical GPIO, IR, SD and firmware behavior remain unverified on hardware.** Supported adapters require device_info major 2, Flipper Zero target 7, documented responses and a plain unprefixed >: prompt. Firmware versions alone do not establish support.

Disconnect/cancel does not reset physical GPIO outputs, recall emitted IR or undo SD changes. Interrupted writes may leave partial new data. No automatic reconnection or replay. Manual console sends invalidate identity and workspace support checks; identify and check again.

No app installation, battery telemetry, ADC, PWM, power switching or Wi-Fi-board flashing. Existing limits remain: SD 4 MiB/file, backups 256 MiB/2,000 entries, ten IR libraries/2 MB total text. This is an independent companion, not an official Flipper Devices product.

## Validation

172 automated tests cover the UI, transport, protocol adapters, queue/session lifecycle, recovery, persistence, file validation and release integrity. CI additionally builds the Windows executable, launches it with isolated temporary settings, renders a screenshot, confirms clean exit, packages the matching archives and verifies them before uploading. The packaged smoke check is headless and does not replace interactive or physical-device testing.
