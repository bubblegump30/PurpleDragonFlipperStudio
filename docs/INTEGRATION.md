# v1.0.1 identity compatibility correction

Official f7 `furi_hal_version_uid_size()` returns 64/8 bytes; `furi_hal_info_get` prints those bytes as two hex digits each. The adapter's previous 24-character requirement rejected that 16-character UID64. It now accepts 16 or the previous 24 hex characters without relaxing hardware model/target or firmware/format checks.

The worker distinguishes a complete, bounded response ending in protobuf_version_minor from a timeout/transport/oversize failure. If a complete response fails identity validation it emits ok=false,recoverable=true and releases the query lock without interrupting serial. The GUI retains the unsupported reason and console connection but grants no device capabilities. Timeout/oversize/USB failures remain fatal; they are not converted to recoverable results. No automatic retry or alternative hardware command is sent.

Sources inspected 2026-10-16:
- https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/f7/furi_hal/furi_hal_version.c
- https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/f7/furi_hal/furi_hal_info.c
- https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/cli/cli_main_commands.c

# v0.9.0 reliability and compatibility

`compatibility.py` builds a bounded local snapshot from current adapter state. UI support rows are not a firmware allowlist: only current response checks enable capabilities. Local checks validate settings status and the two local data stores without mutation or hardware commands. Report fields are explicitly selected; no device names/UIDs/USB serials, notes, transcript or raw errors. Export is explicit and diagnostics embeds the snapshot.

The serial worker now has a threading.Event stop latch alongside Qt interruption; cancellation before start is retained and run returns before serial access. All queue APIs reject interrupted workers. Queued operation data is deep-copied before pending state is set. Incomplete or transport-failed identity operations mark interruption before publishing their failure; the loop exits without reading again. No retry or replay occurs.

Opened/received/fault/finished callbacks capture the worker and are delivered only while it is the current session. Operation failures are routed to their workspace, then invalidate all capabilities and retain the original cause in connection recovery. Manual console sends reset identity, SD availability/restore preview, IR support and GPIO tracking before another workspace operation can start. The next device operation requires fresh identification/support checks.

All CLI workspaces share the same strict plain prompt regex. An error line ending in >: without a line boundary cannot be swallowed as a hostname. Echo matching requires the complete command, optionally preceded by the exact plain prompt. Unknown/custom prompt formats are unsupported; the adapter does not guess. This narrows the older SD prompt behavior deliberately. IR/GPIO already used this strict prompt contract. No universal firmware, optical, electrical or SD hardware validation is implied.

# v0.8.0 digital GPIO integration

`gpio_protocol.py` validates eight non-debug pin names and exact GPIO CLI acknowledgements. `gpio_workbench.py` integrates existing neon controls. `gpio_probe` sends only `gpio` usage; it requires the documented mode/set/read signatures and explicit 0=input, 1=output mapping. Only then is the connection-scoped `gpio_digital` capability enabled.

The serial worker retains GPIO support and confirmed modes across jobs. Read requires a confirmed Input; set requires Output. Probe, device_info refresh and manual console writes invalidate worker tracking. UI output requires per-Output confirmation and per-selected-pin arming. Output mode firmware initializes the latch LOW before push-pull initialization. Input is an explicit command, not automatic cleanup. Each operation is bounded by the existing client deadlines and strict unprefixed prompt framing. Unexpected replies/errors close the session.

No SD probing is required. Shared busy state excludes console/identity/SD/backup/IR interleaving. Polling is a user-started 1-second Qt timer for one selected input, skipping busy jobs rather than queuing a backlog. Pin changes, navigation away, manual sends, refresh and disconnect stop it. History is bounded to 500 blocks. Late results after disconnect are ignored. Saved setups remain local notes/pin selection only.

The regular pins are PA7/2, PA6/3, PA4/4, PB3/5, PB2/6, PC3/7, PC1/15, PC0/16. Debug, UART, internal and power pins are excluded. No ADC/PWM/power-control integration. State is last-confirmed CLI state and may be changed by other device code; voltage is never inferred. Disconnect does not reset hardware outputs and cancellation cannot undo a command already executed. Physical validation is pending.

Protocol sources inspected 2026-10-16:
- https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/cli/cli_command_gpio.c
- https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/f7/furi_hal/furi_hal_resources.c

# v0.7.0 IR integration

`ir_protocol.py` validates payloads and performs read-only capability probing or one explicit transmit command through the existing `StorageClient` framing and `SerialSession` worker. `ir_workspace.py` owns local libraries and the UI. IR requires an identified CLI session but not an SD probe. The common worker exclusion blocks console sends, identity, SD and backup operations while IR work is pending.

## Protocol contract

`ir` prints usage and Available protocols without transmitting. The adapter intersects advertised protocols with the known protocol bit-width table and checks whether RAW syntax is advertised. The UI keeps this support state per connection; reconnect/re-identification clears it.

Parsed .ir addresses and commands are four hexadecimal bytes interpreted little-endian, as in the official signal file implementation. Supported names and widths are NEC, NECext, NEC42, NEC42ext, Samsung32, RC5, RC5X, RC6, SIRC, SIRC15, SIRC20, Kaseikyo, RCA and Pioneer. Out-of-range fields and extra/duplicate fields are refused.

Raw CLI commands require frequency 10,000–1,000,000 Hz, exact integer percent duty (converted from file fraction), 1–512 positive timings no larger than one second each, at most two seconds in total, and at most 960 command characters. These are bounded adapter limits, not a claim to support every valid raw file. Local raw validation supports up to 1,024 uint32 timings and fractional duty; export preserves those fields without converting them to CLI data.

Transmission is one explicitly confirmed `ir tx` command using a snapshot of the selected validated signal. Firmware controls its normal minimum repeat frames. No universal/brute-force or continuous replay commands are generated. The adapter requires the standard unprefixed CLI prompt and an empty response body on completion. Busy, argument errors, unexpected output, unsupported prompts and timeouts fail/close the session rather than claiming success. Completion does not verify optical output or appliance action. Cancellation disconnects; already emitted IR cannot be recalled.

## Libraries and validation

Files are bounded to 1 MB and 512 signals. Duplicate names/fields, header problems and malformed payloads generate warnings; a warning-free file is required for transmission or saving a library. Valid signals that are incompatible with CLI conversion remain saveable/exportable. The QSettings library store holds at most ten named libraries and 2 MB of file text, with a 2.1 MB encoded JSON limit. Full-store validation occurs before writes; malformed existing data is preserved. Loading, renaming, export and clipboard actions never transmit. Libraries are excluded from the older settings-backup schema and can be exported independently as .ir files.

## Primary sources and remaining validation

- [Official IR CLI arguments, errors and transmit behavior](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/main/infrared/infrared_cli.c)
- [File byte order and payload validation](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/infrared/signal/infrared_signal.c)
- [Protocol implementations and bit-width tables](https://github.com/flipperdevices/flipperzero-firmware/tree/dev/lib/infrared/encoder_decoder)
- [Hardware carrier range](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/furi_hal_include/furi_hal_infrared.h)

Synthetic CLI fixtures cover parsing/framing/error handling. Actual Flipper IR output, target behavior, firmware compatibility and cancellation need hardware validation.

---

# v0.6.0 backup and restore integration

`backup_service.py` implements verified folder backups and previewed restoration through the same `StorageClient` and serial worker. `backup_center.py` adds the UI in Backup & Tools. Backup, restore_preview, and restore use the existing operation exclusion, cancellation, stale-session checks and progress signals.

## Backup format and publication

Backups scan canonical /ext paths recursively and preserve files plus empty folders. Preflight refuses any file over 4 MiB, totals over 256 MiB, or more than 2,000 entries before payload downloads. Local free space is checked. Files are downloaded with existing remote MD5 checks into flat `data/NNNNNN.bin` objects, avoiding Windows path/name collisions. The schema-1 manifest maps validated relative SD paths to object names, sizes and SHA-256 digests. No device UID is included. A 2 MiB maximum manifest and bounded payload reads constrain imported backups.

A unique .incomplete directory is created locally. Only after all files download, the manifest is flushed and all payloads are revalidated is it renamed to the completed backup directory. Incomplete directories are refused by restore. Failures preserve partial data and report the staging location; the app does not claim they are completed backups. The SD snapshot is not atomic across files: other device writes should be stopped, and detected size/hash inconsistencies abort the job.

## Preview and restore contract

A preview verifies every local payload, rejects traversal, duplicate/case-conflicting paths, missing parents, invalid sizes/hashes, symlink payloads and invalid object references, and checks that a new direct child of /ext does not already exist. The preview includes the raw-manifest SHA-256 digest and complete destination paths.

Confirmation passes the exact previewed folder, target and digest. The worker validates them again before creating the new target. Each payload is verified into a bounded private temporary snapshot before upload. Existing staged-upload integrity and create-new semantics remain in force. There is no merge, overwrite, formatting or automatic replacement of active app data. A failed/cancelled restore leaves only newly created destination data/stages and reports the target for inspection.

Both backup and restore have a 30-minute overall deadline; individual echo/write/prompt timeouts remain bounded. SD availability and preview approval are cleared on disconnect. Console sends and identity queries remain excluded while a job is active. Original backups and pre-existing remote files are preserved.

Tests use a synthetic CLI emulator, not real hardware. Validate missing/full/read-only cards, nested and empty folders, real file checksums, cancellation/unplug, oversized preflight and restore confirmation on disposable SD data before relying on this for recovery.

---

# v0.5.0 SD integration

`sd_protocol.py` owns synchronous, bounded binary CLI framing; `SerialSession` executes operations on its existing worker thread. `sd_manager.py` owns the UI and connection-scoped SD availability. There is one serial port owner and no second reader.

SD controls require an identified CLI session. Refresh / Probe SD explicitly lists `/ext`; a successful listing adds the implemented `sd_files` capability. Nothing probes storage automatically on connection or identity discovery. Failures, disconnects, and re-identification clear availability and stale directory entries. Late-session results are ignored.

## Protocol and bounds

Commands require a matching echoed command line and a completed CLI prompt. Downloads use the declared Size header and an exact byte count; payloads are never UTF-8 decoded, ANSI-filtered, or searched for prompt delimiters. Uploads use write_chunk with an exact byte count and the Ready handshake. Short serial writes are handled. Transfers are limited to 4 MiB, listings to 2,000 entries and 64 KiB of textual response. Command echo and writes have 10-second deadlines; prompt completion has 30 seconds; each operation has a 120-second overall deadline.

Downloads verify remote MD5 before writing a sibling temporary file and atomically replacing the selected destination. Uploads use a unique sibling `.pd-upload-*.part`, verify its MD5, copy with the firmware's create-new destination semantics, verify the destination, then remove the stage. Firmware rename is deliberately unused because it can remove an existing destination. The create-new copy protects against a destination appearing after the initial listing. MD5 is used for integrity, not trust/authentication.

Only canonical `/ext` paths are accepted; traversal, root mutation, command separators, quotes, backslashes and control characters are rejected. Delete uses storage remove, without recursive deletion. Formatting, internal storage, and remote overwrite are not exposed.

Any storage failure or cancellation closes the serial session so incomplete binary framing cannot become console text. Queued and new text sends/identity queries are excluded while storage is pending. Cancellation does not promise to undo a device operation already executing. Interrupted uploads/copies may leave a stage or a newly created partial destination, never an automatically removed pre-existing destination. The UI preserves a reported staging path when available; otherwise inspect `.pd-upload-*.part` in the chosen directory.

## Primary firmware references

- [Storage commands and byte-counted framing](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/storage/storage_cli.c)
- [Create-new copy versus replacing rename](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/storage/storage_external_api.c)
- [CLI prompt formatting](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/lib/toolbox/cli/shell/cli_shell_line.c)

Tests use a synthetic CLI emulator, not real card captures. Hardware validation must cover missing card, non-ASCII names, folders, zero/binary files, checksums, unplug/cancel during read/write/copy, non-empty folder deletion, read-only/full card, and reconnect. Use disposable test files first.

---

# v0.4.0 device integration foundation

`device_protocol.py` implements a read-only CLI metadata adapter; `backend.py` owns the serial port and executes the explicit query in its existing QThread. There is no second connection or reader. The adapter is separate from the unimplemented RC7 hardware action boundary.

## Request lifecycle

Device Dashboard → Identify / Refresh device is available only for an open CLI connection. It queues exactly `device_info` followed by carriage return. No identification runs on startup, connection, or UART Bridge sessions. Queued console sends must finish first; new sends are excluded while querying. The worker preserves incoming text in the console, limits responses to 64 Ki characters and waits at most four seconds for the response after sending. Disconnect requests interruption; a serial fault ends the transport normally.

The parser accepts underscore device_info major 2 responses, model Flipper Zero, hardware target 7, a 24-digit hexadecimal hardware UID, firmware version/commit, and numeric protobuf version fields. The final newline-terminated protobuf_version_minor field marks completion. Duplicate keys and malformed or incomplete required fields are rejected. Other firmware formats are unsupported until covered by explicit fixtures.

The UI handles only a result from its current session and pending query. States are unverified, querying, identified, and unsupported. Each query clears prior values; connection loss/fault clears identity and capabilities. The sole implemented capability is device_info. Protocol identity is device-reported and is not authentication. No GPIO/IR/storage/app capabilities are inferred from firmware command availability.

The local dashboard shows queried fields; diagnostics contain only identity state and implemented capability names. A requested query's output is retained in the console and can include the device UID; users choose whether to export that transcript. Battery and storage values remain unknown.

## Primary protocol references

- [Official CLI command registration and formatting](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/cli/cli_main_commands.c)
- [Official device_info fields and final-field marker](https://github.com/flipperdevices/flipperzero-firmware/blob/dev/targets/f7/furi_hal/furi_hal_info.c)

Synthetic protocol fixtures exercise this contract. No physical-device success is claimed. Verify Identify, timeout/retry, unplug during query, UART refusal, cancellation, and reconnect on the actual Flipper before declaring hardware compatibility.

---

# Connect the GUI to GPIO & UART Lab RC7

This package reproduces the neon workspace arrangement of the supplied design reference. The new layout is in `window.py`, its painted controls are in `neon.py`, and shared serial/local workflows are in `base_window.py`. RC7 source was unavailable, so existing device behavior has not been migrated or modified.

## Preferred integration path

1. Keep the current backend working independently. Identify its port discovery, connection lifecycle, CLI/UART mode selection, GPIO controller, IR service, backup manager and telemetry services.
2. Add a concrete adapter derived from `HardwareAdapter` in `purple_dragon/backend.py`. Instantiate it and pass it into `MainWindow(adapter=...)` in `app.py`.
3. Replace the generic `SerialSession` connection ownership with the existing connection service if RC7 already manages serial. There must be **one owner** of a serial port. Avoid two simultaneous readers or two independent connections.
4. Expose backend events through Qt signals: connected, disconnected, incoming text, errors, telemetry, GPIO readings, operation progress and completion.
5. Route results to widgets on the GUI thread. Put blocking reads, writes, backups and firmware queries into workers, with timeouts, cancellation and shutdown handling.
6. Enable each control only after its service is implemented and the required mode, connection and capabilities are verified. The base adapter and current GPIO handler are intentionally inactive; merely setting a capability flag does not enable anything.

## GPIO requirements

Move your documented pin mapping into a shared schema and verify the dropdown against the supported board/firmware. Preserve RC7's Input-before-Read behavior. LOW/HIGH must require a successful Output operation plus an explicit arm toggle. Disarm on connection loss, pin change, mode change or output failure. Polling must stop on disconnect and page shutdown. Do not infer successful output from a click: wait for a device response.

`MainWindow.gpio_action()` is the view handler to replace with the controller call. The initial package intentionally leaves every hardware GPIO button disabled. Add the arm/poll state and backend result widgets while integrating the real controller.

## UART / CLI requirements

The current mode selector records the user's choice; it does not issue a bridge command or configure device pins. Preserve RC7's actual mode transitions and restore behavior when connecting the existing service. Sending text is explicit and enabled only after the generic serial open succeeds. Incoming UTF-8 is decoded incrementally; non-text binary UART protocols require a separate binary/hex console.

## Other pages

| Page | Integration work |
| --- | --- |
| Device Dashboard | Verify device identity, then retrieve firmware, name, battery and storage; show unknown or stale data explicitly |
| IR Remote Studio | Parse `.ir` into named signals, validate signal data, connect transmission and completion/errors |
| Backup & Tools | Implement device storage access, backup progress, cancellation, integrity checks and explicit restore flow |
| Apps & NFC | Current links open in the default browser; no scraping, app downloads or device installs occur |
| Live Log | Record controller lifecycle and results without logging sensitive payloads by default |

## Tkinter RC7 applications

If RC7 uses Tkinter, migrate its backend functions into UI-independent services. Do not embed a Tkinter mainloop inside the Qt event loop. Keep this GUI as a separate prototype until the behavior has been transferred and verified.

## Windows release checks

Use the native Windows build recipe; test on a clean Windows 11 account. Confirm reconnect after USB removal, busy-port errors, no-port startup, cancellation during connection, shutdown during active I/O, saved-port disappearance, 100/150/200% scaling and 4K displays. Check every migrated GPIO/IR/backup action on your hardware before calling it an RC7 replacement.
