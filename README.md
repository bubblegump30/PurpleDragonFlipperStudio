# PurpleDragonFlipperStudio

Neon GUI v0.8.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

Rebuilt around your supplied neon-console design: the illustrated brush-style header, dragon and Flipper artwork, compact connection bar, sidebar and horizontal workspace tabs, purple outer frame, blue inner frames, multicolor illuminated GPIO buttons, and two-column GPIO layout. This is a runnable Qt desktop interface with real controls and live Matrix rain.

![PurpleDragonFlipperStudio desktop](assets/Preview-Desktop.png)

## Run on Windows

Download the Windows x64 ZIP from [Releases](https://github.com/bubblegump30/PurpleDragonFlipperStudio/releases). Extract the entire archive into a new folder, then run **PurpleDragonFlipperStudio.exe**. Keep **_internal** beside the executable. No separate Python installation is required for that package.

For source development, use the matching Source ZIP, run **Setup.bat**, then **Start.bat**. Setup supports standard 64-bit CPython **3.10–3.14**. **Debug-Launch.bat** displays launch errors. No administrator rights are needed.

Export a settings backup before upgrading. Existing saved user settings are reused.

## Visual design

- Home opens the GPIO workspace from the reference.
- Eight workspace tabs and the sidebar follow the selected page.
- The compact connection bar includes a live theme selector with color swatches.
- Custom painted buttons have colored light bloom, inset gradients, line icons and keyboard focus feedback.
- Panels have layered neon edges and dark glass surfaces.
- GPIO controls use purple, cyan, blue, slate and red accents.
- The title, dragon, device and chip artwork are rendered from the supplied reference as decorative assets. The application is not a screenshot with click targets: its controls, layouts, console, forms and animation are implemented in Qt.
- Matrix rain moves behind the interface, pauses while minimized, and supports brightness, speed and reduced-motion settings.
- Compact screens stack the GPIO panels and wrap the tab row. The full header artwork appears when there is enough width.

## Working features

| Area | Available now |
| --- | --- |
| Serial | USB serial-port discovery, open/close, bounded text receive, explicit text send with selectable line endings |
| SD backups | Recursive /ext or selected-folder backups with manifests, checksums, restore previews and confirmed restoration to a new SD folder |
| SD File Manager | Explicit /ext probe, folder browsing, binary upload/download with integrity checks, folder creation and confirmed non-recursive deletion |
| Device information | Explicit CLI device_info query, checked Flipper-compatible identity fields, device name/firmware/hardware/protocol values, connection-scoped device_info capability |
| GPIO setups | Named local experiments, pin choice, notes, save/delete, JSON import/export |
| GPIO Workbench | Explicit CLI support check, input/output modes, digital reads, armed LOW/HIGH, input polling and bounded exportable history |
| Appearance | Eight themes, inline theme switching, glow, Matrix controls, persistent settings |
| IR Workspace | Validated .ir files, named local libraries, whole-file/selected-signal export, explicit capability check and confirmed single-command transmission |
| Local tools | Console, setup and session-log exports |
| Navigation | Last-workspace restore, synchronized selectors, keyboard shortcuts, session Back/Forward history |
| Apps | Official catalog, NFC category, community directory and Foundation website |

GPIO digital controls, IR transmission, SD files and bounded backups use explicit support checks after CLI identification. App installation and battery telemetry still need integration. Opening a serial port does not verify Flipper identity. No startup hardware commands are sent; optional GPIO polling starts only when explicitly enabled. See [docs/INTEGRATION.md](docs/INTEGRATION.md).

## Build an executable

Run **Build-Windows.bat** on Windows. It produces:

`dist/PurpleDragonFlipperStudio/PurpleDragonFlipperStudio.exe`

Distribute the entire output folder, including `_internal`. This source ZIP does not contain a prebuilt Windows executable. Windows packaging passed for v0.3.0; each new package must pass its build checks. Physical device integration remains unverified.

## Files

```text
app.py                         Application entry point
setup_bootstrap.py             Python selection and setup recovery
purple_dragon/window.py        Neon console layout and navigation
purple_dragon/neon.py          Painted controls, icons and artwork rendering
purple_dragon/base_window.py   Shared serial and local-workflow services
purple_dragon/matrix.py        Live bounded Matrix rain
purple_dragon/theme.py         Eight palettes and field styling
purple_dragon/backend.py       Serial worker and RC7 integration boundary
assets/design-reference.png   Your visual source of truth
assets/dragon.png / dragon.ico Dragon branding and Windows icon
assets/Preview-Desktop.png     Actual app render at 1672×941
assets/Preview-4K.png          Actual app render at 3840×2160
PurpleDragon.spec              PyInstaller Windows build recipe
tests/                        143 GUI, GPIO, IR, backup/restore, storage and protocol checks
```

Run tests: `python -m unittest discover -s tests -v`.

Website: https://www.purpledragonfoundationltd.xyz/

Dependency references: https://doc.qt.io/qtforpython-6/ and https://pyserial.readthedocs.io/en/latest/ . Dependencies retain their upstream licenses. This independent companion GUI is not an official Flipper Devices product.

## v0.3.0 — QoL Release & Help Center

Press **F1** or open **Backup & Tools → Help Center** for searchable local guidance. This release includes workspace/window memory, keyboard navigation, per-port settings, command recall, transcript search, preset duplication/rename, filtered logs, settings backups, IR signal browsing and diagnostic export.

[Release history](docs/CHANGELOG.md) · [Validation and remaining checks](docs/VALIDATION.md) · [Hardware integration](docs/INTEGRATION.md)

To upgrade, extract into a new folder. Existing user settings are reused. Export a settings backup before changing installations. Restoring a backup replaces its included settings and presets after confirmation. Source and Windows release archives should come from the same commit. Physical device integration remains unverified.

## v0.3.1 — Release Cleanup

Corrected installation guidance, updated creator credits and Help Center text, and added release packaging that produces source and Windows ZIPs from one clean Git commit. Each build includes archive SHA-256 checksums and a manifest identifying the commit.

## Repository and release

[GitHub](https://github.com/bubblegump30/PurpleDragonFlipperStudio) · [v0.8.0 release notes](docs/RELEASE-v0.8.0.md) · [MIT license](LICENSE)

The Windows build workflow runs tests, builds the executable, and uploads matching release files as an Actions artifact. It does not publish a release automatically. See [release instructions](docs/GITHUB-UPLOAD.md).

## v0.3.2 — Connection Center

The connected serial port is checked every 1.5 seconds. A disappeared port disables sending and stops the worker; a discovery error alone does not disconnect it. Retry checks the selected port without switching to another device. Manual disconnect offers Reconnect. Device → Connection details shows selectable status, metadata, and the original error, with guidance for busy ports and timeouts. Reconnection never sends commands automatically.

## v0.3.3 — Console QoL

Save up to 50 local command favorites; Load fills the draft and never sends it. Receive timestamps label serial chunks without modifying raw captured text. Pause display continues capture and Resume shows retained data. Retention is bounded to 200,000 characters and 2,000 receive chunks; the display also keeps at most 2,000 text blocks. Export raw text or timestamped JSON, including paused data. JSON reports whether capture was trimmed. Clear console clears the retained capture. Favorites and timestamp preferences persist locally; the existing settings backup format does not include them.

## v0.3.4 — Workspace Polish

Drag the GPIO panel dividers to resize Pin Control/Presets and Response/Pin Information. Compact windows stack them vertically; wide windows place them side by side. Each layout keeps separate local proportions. Ctrl+Shift+0 resets panel sizes. Ctrl+K opens the workspace selector, Ctrl+F opens Console search, and Ctrl+L reveals the command draft. Added accessible control names, focused tooltips, and cached icons rendered at multiple resolutions for high-DPI displays. Panel proportions are not included in settings backups.

## v0.4.0 — Device Integration Foundation

Connect the Flipper USB serial port in **CLI** mode, open **Device Dashboard**, and click **Identify / Refresh device**. This explicitly sends the read-only `device_info` command through the existing serial worker. Nothing is queried automatically on connect. Console Send pauses during the query, which has a four-second response timeout and can be cancelled by disconnecting.

The adapter validates the device_info format, Flipper model, hardware target, UID structure, firmware fields, and complete response marker. This is a compatibility check of a device-reported identity, not cryptographic authentication. The initial capability is `device_info`; SD files, IR transmission and digital GPIO require their separate explicit support checks. App operations and battery queries remain unavailable. Information is cleared on disconnect or transport error. Device identifiers are shown locally and appear in the explicitly requested console capture, but are excluded from diagnostics.

This works without an SD-card query. The Wi-Fi Developer Board is not identified through this action; select the Flipper USB CLI port. If the connection is streaming output or running another CLI command, let it return to its prompt before querying.

## v0.5.0 — SD File Manager

Connect in **CLI** mode → **Device Dashboard → Identify / Refresh device** → **SD Files → Refresh / Probe SD**. File actions enable only after a successful `/ext` listing. Double-click folders to browse; use Up or SD root to navigate. Ctrl+9 opens SD File Manager.

Uploads and downloads support binary files up to **4 MiB**, show byte progress, and check remote MD5 for transfer integrity. Downloads replace the chosen local destination only after verification. Uploads stage a uniquely named `.pd-upload-*.part` file, check it, copy to a new destination using the firmware's create-new operation, verify again, then remove the stage. Existing remote destinations are refused; there is no overwrite or formatting action. Delete requires confirmation and removes only a file or empty folder. All paths stay inside `/ext`.

**Cancel & disconnect** stops host transfer work and closes the serial session. All storage failures also disconnect to avoid returning binary input to the text console. Reconnect, identify and probe before retrying. Failed/cancelled uploads may leave a stage or a newly created partial destination; inspect them before removing anything. No existing remote file is automatically deleted during failure cleanup. Device operations already executing may finish after disconnection.

The same serial worker owns the connection throughout. Console Send and identity queries pause during storage work. Responses are bounded to 64 KiB for text and 2,000 entries per listing; operations have a 120-second overall deadline. MD5 is an integrity check, not authentication. Physical SD-card behavior remains unverified until tested on hardware.

## v0.6.0 — Backup & Restore Center

After **CLI identification → SD Files → Refresh / Probe SD**, open **Backup & Tools**. Back up all `/ext` or the current folder from SD Files. Choose a local parent folder; the app creates a unique backup containing `manifest.json` and flat binary payload objects. Empty directories are preserved. Remote MD5 transfer checks and local SHA-256 manifest checks run before the backup is published.

Limits are **4 MiB per file, 256 MiB total, and 2,000 file/folder entries**. Oversized backups fail preflight; nothing is silently skipped. A failed/cancelled backup is left as `.incomplete` without a usable completed manifest. Backups contain SD file data; they are separate from this app's settings-export feature. This is a file snapshot, not a transactional disk image: stop other device writes first.

To restore, choose a completed backup folder and a **new folder name under `/ext`**, then **Verify & preview**. All payload checksums and paths are validated before the preview lists the destination and files. Confirming restore revalidates the backup and checks that the destination still does not exist. It creates that new folder and uploads verified payload snapshots. It never merges into existing folders, overwrites existing files, or formats the card. Files restored into the new folder do not automatically replace active app data elsewhere on the SD card.

Progress and Cancel & disconnect are available. Backup/restore operations have a 30-minute overall deadline while individual serial command deadlines remain bounded. Cancellation/failure closes the serial session; a partial restore may remain in the new destination. Reconnect, identify and probe before retrying. Physical SD-card validation remains pending.

## v0.7.0 — IR Workspace

Open **IR Remote Studio** to load `.ir` files, filter/select signals, and save named local libraries. Libraries can be loaded, renamed, removed after confirmation, and exported as standard `.ir` files. Whole-file and selected-signal export never transmit. The store is limited to ten libraries and 2 MB total IR text; individual files are limited to 1 MB and 512 named signals. Corrupt saved stores are preserved rather than overwritten. IR libraries are saved locally and are **not included in the existing settings-backup format**; export `.ir` files to back them up.

For device use: **identify in CLI mode → IR Remote Studio → Check IR support → select a valid signal → Transmit selected signal → confirm**. The explicit read-only `ir` usage query discovers supported formats. No SD card is required. One `ir tx` command is sent through the existing worker; firmware may emit protocol-defined repeat frames. No automatic playback, bulk transmission, or universal brute-force action is provided.

Parsed signals validate four-byte little-endian address/command fields against documented protocol bit widths. Raw CLI transmission is limited to 10,000–1,000,000 Hz, exact one-percent duty steps, at most 512 timings, two seconds total timing duration, and a 960-character command. Valid files outside those CLI limits can still be saved/exported. File-format raw validation accepts up to 1,024 timings. Selected-signal tooltips explain unavailable transmission.

The UI requires a current identified session, a successful IR probe, a warning-free file, a supported selected signal, an idle worker and confirmation. Busy-device, error and unexpected responses fail the operation; disconnect clears capability state. Command completion means the CLI returned without an error, **not that the target appliance responded**. Cancel disconnects and cannot recall IR already emitted. Physical transmission validation remains pending.

## v0.8.0 — GPIO Workbench

Identify the Flipper in CLI mode, open **GPIO Lab → Check GPIO support**. Only the eight regular pins PA7/2, PA6/3, PA4/4, PB3/5, PB2/6, PC3/7, PC1/15 and PC0/16 are supported. Debug/UART/internal pins and power rails are excluded. No SD card is required. Disconnect attached development boards/drivers before changing wiring; use 3.3 V compatible circuitry and common ground, and never connect competing outputs.

Select **Input** before **Read**. Optional one-second polling reads only the selected input; busy serial jobs are skipped. Polling stops on pin changes, leaving GPIO Lab, manual console sends, errors, disconnects or identity refresh. The history keeps at most 500 lines and can be exported.

**Output** requires confirmation and starts LOW (push-pull), as defined by firmware. After a successful response, check **Arm LOW/HIGH** to enable writes for the selected pin. Selecting another pin disarms. **Input** explicitly returns a selected output to input mode. Saved setups contain only pin selection and notes; loading never configures hardware or arms outputs.

Mode/state labels show the last confirmed CLI response in the current session, not continuous hardware monitoring or measured voltage. External apps or circuits can change conditions. Disconnect/cancel does not send a reset and **physical outputs may remain active**. Tracking and arming are cleared; reconnect, identify, check support and deliberately configure pins again. This release has no analog reads, PWM, pulse sequences, power switching or automatic restore of GPIO modes. Physical GPIO validation remains pending.
