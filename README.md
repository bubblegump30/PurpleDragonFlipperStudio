# PurpleDragonFlipperStudio

Neon GUI v0.3.4 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

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
| GPIO setups | Named local experiments, pin choice, notes, save/delete, JSON import/export |
| GPIO workspace | Reference-based controls, pin information, response area and exportable history pane |
| Appearance | Eight themes, inline theme switching, glow, Matrix controls, persistent settings |
| Local IR | Open and preview `.ir` files |
| Local tools | Console, setup and session-log exports |
| Navigation | Last-workspace restore, synchronized selectors, keyboard shortcuts, session Back/Forward history |
| Apps | Official catalog, NFC category, community directory and Foundation website |

Hardware GPIO reads/writes, IR transmission, SD backup, app installation and device telemetry still need the existing RC7 device services. Their controls/data remain gated or unavailable; opening a serial port does not verify Flipper identity. This package does not send automatic device commands. See [docs/INTEGRATION.md](docs/INTEGRATION.md).

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
tests/                        77 GUI, setup, navigation, connection, console, layout and packaging checks
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

[GitHub](https://github.com/bubblegump30/PurpleDragonFlipperStudio) · [v0.3.4 release notes](docs/RELEASE-v0.3.4.md) · [MIT license](LICENSE)

The Windows build workflow runs tests, builds the executable, and uploads matching release files as an Actions artifact. It does not publish a release automatically. See [release instructions](docs/GITHUB-UPLOAD.md).

## v0.3.2 — Connection Center

The connected serial port is checked every 1.5 seconds. A disappeared port disables sending and stops the worker; a discovery error alone does not disconnect it. Retry checks the selected port without switching to another device. Manual disconnect offers Reconnect. Device → Connection details shows selectable status, metadata, and the original error, with guidance for busy ports and timeouts. Reconnection never sends commands automatically.

## v0.3.3 — Console QoL

Save up to 50 local command favorites; Load fills the draft and never sends it. Receive timestamps label serial chunks without modifying raw captured text. Pause display continues capture and Resume shows retained data. Retention is bounded to 200,000 characters and 2,000 receive chunks; the display also keeps at most 2,000 text blocks. Export raw text or timestamped JSON, including paused data. JSON reports whether capture was trimmed. Clear console clears the retained capture. Favorites and timestamp preferences persist locally; the existing settings backup format does not include them.

## v0.3.4 — Workspace Polish

Drag the GPIO panel dividers to resize Pin Control/Presets and Response/Pin Information. Compact windows stack them vertically; wide windows place them side by side. Each layout keeps separate local proportions. Ctrl+Shift+0 resets panel sizes. Ctrl+K opens the workspace selector, Ctrl+F opens Console search, and Ctrl+L reveals the command draft. Added accessible control names, focused tooltips, and cached icons rendered at multiple resolutions for high-DPI displays. Panel proportions are not included in settings backups.
