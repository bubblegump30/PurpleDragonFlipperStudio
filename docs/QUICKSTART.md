# PurpleDragonFlipperStudio 1.0 — Start here

Neon GUI v1.0.1 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

## Install and open

Download the Windows-x64 ZIP from the project's GitHub release. Extract the entire ZIP to a new folder. Run PurpleDragonFlipperStudio.exe and keep _internal beside it. No separate Python installation or administrator rights are required. Source users run Setup.bat, then Start.bat; Debug-Launch.bat shows launch errors.

Repository and releases: https://github.com/bubblegump30/PurpleDragonFlipperStudio

## First connection

1. Use a USB data cable. Close qFlipper and other programs using the serial port.
2. Refresh ports, select the Flipper's port, choose CLI mode, then Connect.
3. Open Device Dashboard → Identify / Refresh device.
4. Run the support check in the workspace you want to use. Device Dashboard lists the checks completed in this connection.

Opening a port does not identify a device. Nothing is sent automatically at startup or connection. GPIO/IR do not require an SD card; SD file and backup operations do. The Wi-Fi Developer Board is not required for these USB CLI features. Disconnect attached boards/drivers before changing GPIO wiring.

## Workspaces

- GPIO Lab: Check GPIO support → Input → Read. Output requires confirmation, starts LOW, and LOW/HIGH require arming. Eight regular header pins only. Use compatible 3.3 V circuitry and common ground; no competing outputs. Input explicitly returns a selected pin to input mode.
- IR Remote Studio: Open .ir → save/export local libraries. For transmission: Check IR support, select a valid signal, Transmit and confirm. Completion does not confirm appliance response.
- SD Files: Refresh / Probe SD → browse, upload/download files up to 4 MiB, create folders, or confirm non-recursive deletion. Uploads create new files and do not overwrite existing destinations.
- Backup & Tools: Back up /ext or the selected SD folder. Restore verifies and previews a completed backup, then creates a new SD folder after confirmation. Limits: 4 MiB/file, 256 MiB total, 2,000 entries.
- UART Console: Sends exactly your draft plus the selected line ending. A manual Send invalidates identity and all device support checks. Identify and check support again before using other workspaces.
- Device Dashboard: Run local checks and export compatibility JSON. These actions send no device commands.

Press F1 for the searchable Help Center. Ctrl+K selects a workspace. Ctrl+L opens the console draft. Ctrl+Home opens GPIO Lab.

## Recovery and upgrades

A complete unsupported identity response leaves serial open and device controls disabled; see its reason in Device Dashboard. Timeouts and transport errors still close the session. Reconnect explicitly after those errors, identify, then repeat support checks. No automatic reconnection or replay occurs. Cancel & disconnect closes the serial transport; commands already executing may finish. **Disconnect does not reset physical GPIO outputs.** IR already emitted cannot be recalled. Interrupted SD writes/restores may leave partial new data; inspect them before retrying.

Before upgrading, export a settings backup and separately export IR libraries (.ir). Copy any command favorites you want to preserve outside local settings. The existing settings-backup schema covers presets and included preferences, not every local store. Install into a new folder; existing user settings are reused. Keep the older application folder if you need to return to it. Restoring a settings backup replaces its included fields after confirmation.

For a report, use Device Dashboard → Export compatibility report or Backup & Tools → Export diagnostic report. Compatibility/diagnostic snapshots exclude hardware identifiers, notes and transcripts. Console/log exports may contain private data; review before sharing.

## Release verification

SHA256SUMS.txt and release-manifest.json accompany the download. In PowerShell, run Get-FileHash *.zip -Algorithm SHA256 and compare with the published hashes. Source users can run:

python scripts/verify_release.py PATH-TO-RELEASE-FILES --require-windows

This checks archive integrity, structure and package metadata; it is not a code signature or proof of hardware compatibility. The archive files and manifest should come from the same trusted release.

## Scope

This is an independent Flipper Zero companion. The 1.0 desktop software release consolidates tested UI, transport and protocol workflows; physical GPIO, IR, SD and firmware compatibility remain unverified on hardware. Supported adapters require device_info major 2, Flipper Zero target 7, documented command responses and a plain unprefixed >: prompt. No app installation, battery telemetry, ADC, PWM or power switching. No wireless-board flashing is performed by these workflows.

Project code: MIT. See LICENSE.txt, DEPENDENCIES.md and licenses/ for dependency notices.
