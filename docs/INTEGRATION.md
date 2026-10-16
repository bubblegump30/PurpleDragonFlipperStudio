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
