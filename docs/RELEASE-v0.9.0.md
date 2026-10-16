# PurpleDragonFlipperStudio v0.9.0 — Reliability & Compatibility

Neon GUI v0.9.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Device Dashboard compatibility table with current-session capability status and next steps.
- Read-only local checks and identifier-free compatibility JSON export; included in diagnostics.
- Session-bound transport callbacks ignore late signals from old connections.
- Cancellation stays latched before thread startup; interrupted workers reject new work.
- Failed identity queries close the session; operation failures preserve their cause through shutdown.
- Manual console sends invalidate identity, workspace support, GPIO tracking/arming and restore previews.
- Queued request payloads are copied; strict shared CLI echo/prompt framing preserves response errors.

## Use

Connect in CLI mode → Device Dashboard → Identify / Refresh device. Run each required workspace support check. The compatibility table reflects those responses; Run local checks only checks local data. Export compatibility report includes runtime versions, state, contracts and recovery guidance. No device names, hardware UIDs, USB serials, transcripts, notes or raw error text are exported in that report.

After a manual Send, identify and repeat support checks. After an identity/operation failure, reconnect explicitly. No automatic retries, reconnection or command replay.

## Compatibility and limits

Device_info major 2, Flipper Zero target 7 and documented workspace CLI signatures are required. Exact command echoes and an unprefixed >: prompt on its own line are supported; customized/named prompts fail closed. Firmware version alone never enables a capability. Existing SD, backup, IR and GPIO limits remain.

Disconnect does not reset physical GPIO outputs or undo commands already executed. Partial SD writes may remain; IR already emitted cannot be recalled. Physical hardware compatibility remains unverified.

## Validation and installation

160 automated tests pass locally, including 17 new reliability/compatibility tests, cancellation before port access, immutable queue payloads, identity timeout/USB error closure, command framing, real Qt signal connections across replacement sessions, capability invalidation, error persistence, report privacy and local store checks. Actual Qt layouts were inspected at 980×760 and 1672×941 at 200% scaling without horizontal page overflow.

Extract the whole Windows-x64 ZIP and keep _internal beside the executable. Source users run Setup.bat then Start.bat. Verify archive checksums. Windows CI packaging and physical hardware validation are separate checks; no physical testing is claimed.
