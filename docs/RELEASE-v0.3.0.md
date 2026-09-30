# v0.3.0 — QoL Release & Help Center

PurpleDragonFlipperStudio is a neon-themed Windows desktop companion interface for serial workflows and local Flipper-related files.

## Included

- Saved workspace, window placement, appearance and per-port mode/baud preferences.
- Keyboard navigation, console command recall, transcript search and scroll controls.
- Local GPIO presets with duplication, rename and collision handling.
- Searchable/severity-filtered logs with full and filtered export.
- Validated local settings backup/restore and diagnostic reports.
- IR signal-name browsing with basic structure warnings.
- Searchable Help Center through F1 or Backup & Tools.

## Install and upgrade

Extract the complete source package into a new folder. Run Setup.bat, then Start.bat. Standard 64-bit CPython 3.10–3.14 is supported by setup. Export a settings backup before upgrading; existing user preferences are reused.

Build-Windows.bat produces dist/PurpleDragonFlipperStudio/PurpleDragonFlipperStudio.exe. Keep the entire folder, including _internal, together. Source packages do not include a Windows executable.

## Validation and limits

61 automated tests passed on Python 3.12 / Qt offscreen in Linux. Native Windows packaging, physical serial hardware and multi-monitor verification remain outstanding. This is a source preview release, not a hardware-stable release.

GPIO device operations, IR transmission, SD backup, app installation and telemetry require RC7 integration. Opening serial transport does not verify Flipper identity. Local IR checks do not validate payload compatibility.

Created by KyleAustin85 · https://www.purpledragonfoundationltd.xyz/
