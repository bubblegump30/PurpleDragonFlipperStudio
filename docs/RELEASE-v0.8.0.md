# PurpleDragonFlipperStudio v0.8.0 — GPIO Workbench

Neon GUI v0.8.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Digital GPIO controls in the existing neon GPIO Lab.
- Explicit read-only support check after CLI identification; no SD card needed.
- Eight regular header pins, input/read, confirmed Output starting LOW, armed LOW/HIGH.
- Optional one-second input polling, confirmed response labels and 500-line exportable history.
- Shared worker exclusion, worker-side mode checks, session invalidation and error handling.

## Use

Identify in CLI mode → GPIO Lab → Check GPIO support → select pin → Input → Read. Enable polling for repeated input samples. For output, confirm Output (starts LOW), then arm LOW/HIGH. Input returns that selected pin to input. Disconnect attached development boards/drivers before changing wiring. Use 3.3 V compatible circuitry, common ground, and no competing outputs.

## Limits and state

PA7/2, PA6/3, PA4/4, PB3/5, PB2/6, PC3/7, PC1/15, PC0/16 only. No debug/UART/internal pins, power rails, analog voltage reads, PWM, pulse sequences or automatic mode restoration. Labels are the last confirmed CLI response, not continuous hardware verification.

Changing pins disarms and stops polling. Polling also stops on navigation away, manual console sends, identity refresh, errors and disconnect. Busy jobs are skipped. Local setups never apply hardware state. Manual sends invalidate GPIO tracking.

**Disconnect/cancel does not reset physical outputs; they may remain active.** Use Input explicitly while connected when appropriate. Failed operations disconnect to avoid reusing an uncertain CLI stream. Reconnect, identify and check support again.

## Install and validation

Extract the complete Windows-x64 ZIP; run the executable beside _internal. Source users run Setup.bat then Start.bat. 143 automated tests pass locally, including synthetic GPIO command framing, mode gates, response validation, confirmation/arming, polling, queue exclusion, stale replies and bounded history. Physical GPIO behavior and Windows interactive hardware testing remain pending.
