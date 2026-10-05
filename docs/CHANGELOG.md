# QoL release history

## v0.2.1 — Interface Polish

Window size, position and maximized state restore on launch. Off-screen saved windows are moved back onto an available display. Button labels have default tooltips; disabled actions use quieter lighting and muted text. The GPIO workspace explicitly explains why hardware controls and polling are unavailable. Neon design, themes and existing serial/local workflows are preserved.

## v0.2.2 — Navigation & Workspace Memory

The last workspace restores on launch. Missing or invalid saved pages fall back to Home. Restoration never opens a serial connection. Sidebar, tabs and workspace selector stay synchronized when using shortcuts or history.

| Shortcut | Action |
| --- | --- |
| Ctrl+1 through Ctrl+8 | Open the corresponding workspace tab, from left to right |
| Alt+Left / Alt+Right | Back / Forward through this session's workspace history |
| Ctrl+Home | Home / GPIO workspace |
| Ctrl+L | UART Console and command-input focus |
| Ctrl+, | Appearance settings |
| F5 | Refresh serial ports while disconnected |
| F1 | Beginner guide |

History holds up to 64 entries during the current session. Repeated selection of the same workspace does not add an entry. Choosing a new workspace after going Back clears the forward branch. Window placement and appearance preferences from v0.2.1 remain saved.

## v0.2.3 — Connection Experience

Selected-port metadata is available before connecting in Device Dashboard and the port tooltip. Baud rate and mode are remembered separately for each port. Explicit Connecting, Disconnecting and Connection Error states show progress. Errors remain visible after the worker closes, with a Retry button and USB/port recovery guidance; full text appears on hover and in Live Log. Discovery failures clear stale port metadata and disable Connect until discovery succeeds. Cancelling a connection disables Send immediately and ignores a late open notification.

Connect and Retry remain manual. Port discovery does not identify a Flipper device, and remembering UART Bridge mode does not configure the device hardware.

## v0.2.4 — Console QoL

UART Console adds Up/Down recall of successfully queued commands, keeping the unsent draft when returning past the newest entry. History is limited to 100 commands, skips consecutive duplicates, stays only in memory for the current session, and can be cleared. Recall never sends automatically; Enter or Send still transmits explicitly. Queue rejection keeps your input intact.

Find transcript text with Previous/Next or Enter; search wraps and shows Match/No match feedback. Auto scroll can be switched off to read and select older text while incoming data continues to be captured. Line ending and Auto scroll preferences persist. Transcript export and existing receive limits remain available.

## v0.2.5 — Setup & Preset QoL

New clears the preset editor for another setup. Duplicate creates a uniquely named copy of the selected saved preset, preserving its saved pin and notes. Rename uses the name entered in the selector and preserves the saved contents; choose a unique name. Save Setup stores the current editor contents. Saving to the name of a different existing preset asks before replacing it. Feedback beneath the preset controls confirms local saves, copies and renames. The 200-preset limit remains enforced. These actions manage local configuration only.

## v0.2.6 — Live Log QoL

Live Log has case-insensitive text filtering and All/Info/Warning/Error filters, combined when both are selected. Serial faults and discovery failures are tagged Error; a full send queue is tagged Warning. Other activity defaults to Info. The count shows visible and retained entries. Up to 1000 entries are retained during this session.

Export log includes all retained entries. Export visible and Copy visible include only the filtered view. Clear log clears all retained entries, including hidden ones. Auto scroll can be turned off while reading older entries; filtering and new activity preserve the scrollbar position when it is off. Logs are held in memory until you export them.

## v0.2.7 — Settings Backup & Restore

Backup & Tools now exports a versioned JSON backup of saved local GPIO presets, appearance options, line ending, console Auto scroll and selected workspace. Restore validates the schema, preference types/ranges and all presets before asking to replace these settings. Valid settings apply immediately and persist across launches. Export a current backup first if you want a rollback copy.

Backups are limited to 5 MB. They exclude window geometry, per-port connection preferences, transcripts, session logs and command history. Restore leaves the current serial session alone and never opens a connection or sends a device command. This is local application settings backup; device SD backup still requires RC7 integration.

## v0.2.8 — IR File QoL

IR Remote Studio now indexes named signals, filters names without regard to case, and jumps to a selected signal in the original file text. Copy file text copies the full loaded preview. UTF-8 BOM files are supported. A failed open preserves the previous preview. The 1 MB file limit remains.

The summary shows signal count and basic structure warnings; hover for up to 50 warning details. Checks cover the header/version, supported parsed/raw structure, required field presence, duplicate fields and empty names. Payload numbers, protocols, timing limits and hardware compatibility are not validated. Source: https://github.com/flipperdevices/flipperzero-firmware/blob/dev/documentation/file_formats/InfraredFileFormats.md . Transmission remains disabled pending RC7 integration.

## v0.2.9 — Reliability & Diagnostics

Backup & Tools adds Export diagnostic report. The JSON report includes application/runtime versions, workspace/theme, connection state, detected-port count, settings status, preset-store health, buffer counts and available backend capabilities. It excludes preset names/notes, serial port identifiers, received text, command contents, log messages, file paths and raw error strings. Review any report before sharing it.

Exports now write and flush a temporary file in the destination directory, then replace the target. A failed replacement preserves the original and cleans up temporary files. This does not guarantee recovery from power loss or external filesystem failures.

Invalid saved preset data is preserved: saving/importing presets and exporting settings backups are blocked until a valid settings backup is restored. Diagnostic export remains available to report the problem. This reliability release does not certify Windows packaging or hardware integration.

## v0.3.0 — QoL Release & Help Center

Consolidates v0.2.1–v0.2.9 and adds a searchable, reusable Help Center from F1 or Backup & Tools. Topics cover setup, shortcuts, presets, backups, console/log tools, IR inspection, troubleshooting, diagnostics and current integration limits. README is consolidated; prior details remain in this changelog. Native Windows and hardware verification remain outstanding.

## v0.3.1 — Release Cleanup

Corrected release installation guidance and creator credit; added matching source/Windows archive packaging with SHA-256 checksums and commit manifest. Updated Help Center release information.

## v0.3.2 — Connection Center

Added port-loss monitoring, send disablement on loss, manual Retry/Reconnect, pre-open selected-port checks, actionable error guidance, selectable Connection details, and explicit diagnostic connection states.

## v0.3.3 — Console QoL

Added persistent command favorites, receive timestamp toggle, bounded capture while display is paused, resume catch-up, raw text and timestamped JSON exports, capture trimming metadata, and exact line-ending preservation in atomic exports.

## v0.3.4 — Workspace Polish

Added draggable GPIO panels with compact/wide size persistence and reset, workspace/search focus shortcuts, accessible control names, helpful tooltips, and cached multi-resolution icons. Fixed transient compact-layout overflow.
