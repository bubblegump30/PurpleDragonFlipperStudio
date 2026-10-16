# PurpleDragonFlipperStudio v0.6.0 — Backup & Restore Center

Neon GUI v0.6.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Back up /ext or the current SD folder, preserving files and empty directories.
- Remote transfer integrity checks plus a SHA-256 payload manifest.
- Publish a completed backup only after verification; failed backups stay .incomplete.
- Verify and preview restore paths, counts, sizes and destination before confirmation.
- Revalidate approved backups before restoring into a NEW folder under /ext.
- Progress, cancellation and disconnect protection through the existing worker.

## Use and limits

Identify in CLI mode → SD Files → Refresh / Probe SD → Backup & Tools. Choose a local parent directory for backup. To restore, choose the completed backup, enter a new SD folder name, Verify & preview, then confirm.

Limits: 4 MiB/file, 256 MiB total, 2,000 entries. Nothing is skipped. Restore never merges into existing folders, overwrites pre-existing files, or formats the card. Restored files do not automatically replace active app data. This is a file-level snapshot; stop other device writes first. Failures/cancellation disconnect and may leave an incomplete local backup or partial new SD destination for inspection.

## Install and validation

Extract the whole Windows-x64 ZIP and run PurpleDragonFlipperStudio.exe beside _internal. Source users run Setup.bat then Start.bat. Verify archive checksums.

114 automated tests pass locally, including synthetic backup/restore round trips, binary payloads, empty directories, corrupt manifests/payloads, changed previews, path validation, strict preflight limits, cancellation, partial failure reporting and confirmation gates. Physical SD-card backup/recovery validation remains pending.
