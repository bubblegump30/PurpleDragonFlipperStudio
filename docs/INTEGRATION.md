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
