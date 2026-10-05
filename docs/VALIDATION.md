# Validation — Neon GUI v0.3.0

Executed with Python 3.12, PySide6 6.10.2, pySerial 3.5, and Qt's offscreen platform in the Linux execution environment.

## Passed: 61 tests

The 14 prior checks remain passing: navigation/no-port startup; eight themes and preference persistence; setup save/export/import; malformed setup rejection; IR preview and transcript export; unavailable saved COM port; busy-port failure recovery; real pySerial UTF-8 loopback and worker shutdown; Python compatibility range; interpreter fallback; compatible environment reuse; preservation/rebuild; preservation when no compatible Python exists; and subprocess probing of the installed interpreter.

Five additional checks verify sidebar/tab/workspace synchronization, inline theme changes across painted panels/buttons and Matrix rain, no horizontal page overflow at 980×760 and 1672×941, GPIO controls gated while disconnected and selected-pin information updates, and history export.

## Visual verification

Rendered and inspected the actual app against the supplied design reference. Replaced the previous large welcome-card layout with the reference's illustrated header, compact connection strip, workspace tabs and GPIO console. Corrected clipped sidebar/tab labels, dropdown arrows, button text spacing, initial keyboard-focus decoration, and smaller-screen stacking. All nine unique pages were rendered at 980×760 without horizontal overflow.

Preview-Desktop.png is the Qt-rendered application at 1672×941. Preview-4K.png is the actual application at 3840×2160 with Qt scale factor 2. These are application captures, not new concept mockups.

## Remaining external checks

Windows batch execution, native Windows PyInstaller packaging, Windows font/titlebar/multi-monitor scaling, actual Python 3.14 execution, physical serial connection and RC7 hardware integration were not executed here. Python detection/recovery Windows cases use controlled mocks. Hardware GPIO, IR transmit, app installation, SD backup and telemetry are not active in this GUI package.

## v0.2.1 polish validation

Three additional tests passed: actual Qt window-geometry save/restore; nonempty button tooltips and disabled-action explanations; and compact-layout usability. Desktop and 4K captures were regenerated and the desktop render inspected. Windows-native placement across physical monitors and packaging remain to be tested on Windows.

## v0.2.2 navigation validation

Five additional checks passed: last-workspace restoration with synchronized controls and no connection; invalid-workspace fallback; Back/Forward and history branching; repeated Home/GPIO selections without duplicate history; and actual Qt keyboard events for workspace selection, console focus and Home. The complete suite passed all 27 tests. Desktop and 4K captures were regenerated for v0.2.2.

## v0.2.3 connection validation

Five additional checks verify per-port mode/baud restoration across selection and refresh, selected-port metadata before connecting, discovery-failure recovery without stale metadata, persistent serial-error feedback after worker completion, and cancellation handling for a late open signal. All 32 checks passed. Existing busy-port and serial loopback checks also remain passing. Desktop and 4K captures were regenerated. Physical USB unplug/replug behavior and Windows-native serial drivers remain external checks.

## v0.2.4 console validation

Six new checks verify Qt Up/Down recall and draft recovery without additional sends; queue rejection preserving input; bounded, deduplicated and clearable command history; forward/backward search and wrap with missing-text feedback; saved line-ending/scroll preferences and exact queued payload; and selection preservation during incoming text with Auto scroll disabled. All 38 tests passed. Console layout and regenerated desktop captures were inspected. Windows and physical hardware checks remain outstanding.

## v0.2.5 preset validation

Five new tests cover unique duplicates with saved-field preservation, rename with original-key removal and selection synchronization, New without deleting saved data, rename collision and declined overwrite without mutation, and the duplicate limit. All 43 tests passed. Desktop/4K previews were regenerated and the updated preset panel inspected. Windows and hardware checks remain outstanding.

## v0.2.6 log validation

Four new tests cover combined case-insensitive text/severity filters without data loss, full versus filtered export and clipboard copying, retention at 1000 entries and clearing, and incoming serial errors appearing in the filtered view. All 47 tests passed. Live Log layout was inspected and release previews regenerated. Windows and physical hardware checks remain outstanding.

## v0.2.7 backup validation

Four new tests cover settings/preset roundtrip with persistence and no connection, invalid schema/preference values without mutation, declined restoration preserving settings, and malformed JSON reporting a failure. All 51 tests passed. Backup & Tools layout was inspected and release previews regenerated. Windows and physical hardware checks remain outstanding.

## v0.2.8 IR validation

Three new checks cover parsed/raw entries and library headers; missing/duplicate field warnings; and BOM file loading, filtered signal selection, line navigation and preservation after an invalid UTF-8 open. All 54 tests passed. IR layout was inspected and release previews regenerated. Windows and hardware checks remain outstanding.

## v0.2.9 reliability validation

Four new checks verify diagnostic metadata without user-content disclosure, atomic export replacement failure preserving the original and cleaning temporary files, corrupt-preset preservation and recovery through settings restore, and export-failure feedback. All 58 tests passed. Backup & Tools layout was inspected and release previews regenerated. Windows and physical hardware checks remain outstanding.

## v0.3.0 release validation

Three Help Center tests cover reusable dialog opening without changing workspace, cross-topic search/no-match/clear behavior, and accurate capability guidance without opening a serial session. All 61 tests passed. The diagnostics version test now follows the actual application version. Help Center layout was inspected and release previews regenerated. Windows packaging, multi-monitor behavior and physical hardware remain unverified; this release is not declared hardware-stable.

## Windows compact-layout correction

The initial Windows build found 34 pixels of horizontal overflow in GPIO Lab at the compact size. Pin controls now wrap into a three-column grid and the checkbox labels stack on compact windows. The desktop row is restored when expanding. A regression test covers both arrangements. All 62 tests pass locally. Windows Actions run 36694327173 passed the test suite, built the executable folder and uploaded the Windows artifact. Physical-device and interactive Windows checks remain outstanding.

## v0.3.1 validation — 2026-10-05

63 automated tests passed with Qt offscreen on Linux. Release packaging regression checks verify matching commit metadata, both archive checksums, Windows support files, exclusion of untracked data, and rejection of uncommitted tracked changes. Windows v0.3.1 packaging and on-device validation remain pending.
