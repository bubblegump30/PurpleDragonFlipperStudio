# Program audit — v1.0.2

Date: 2026-10-16. Baseline: v1.0.1. Scope: desktop source, serial lifecycle, identity, GPIO/IR adapters, SD transfers, backup/restore, persisted stores/imports/exports, layout/paint controls, setup and release packaging. Existing tests were retained; fixes add 22 targeted regressions.

## Findings and repairs

| Area | Finding | Repair and evidence |
| --- | --- | --- |
| Presets | Delete could turn a corrupt saved store into an empty object; export could silently export empty presets | All preset mutations/exports guard store validity; regression confirms original raw data remains |
| JSON | Deep nesting could escape handling; duplicate keys silently replaced earlier fields; non-finite values and escaped surrogates were accepted | Shared bounded parser converts nesting/Unicode failures to validation errors, rejects duplicates/non-finite numbers/overlong integers; imports read at most limit+1 bytes |
| Store schema | Unvalidated extra preset fields could persist; aggregate size had no bound | Pin/notes-only schema and 5 MB store bound; invalid data is preserved |
| Startup | Malformed saved geometry and numeric appearance settings could raise Qt/Python conversion errors | Typed fallbacks and range checks; corrupt-store startup regression |
| Exports | Unicode encoding failure escaped the generic export handler | Visible failure feedback; atomic temporary-file cleanup remains |
| Backup verification | Local hashing checked cancellation only after the entire manifest/payload set | Callback checks throughout local validation, including restore preflight and payload snapshots; no remote writes after cancellation regression |
| Downloads | Cancellation after checksum verification could still replace an existing local destination | Checks before local write and atomic replacement; existing destination preservation test |
| SD mutations | Unknown nonempty replies could count as successful mkdir/remove/copy | Empty documented success response required; source contract checked against official storage CLI |
| Serial writes | Console writes did not finish partial writes; invalid write counts could misbehave | Shared bounded write loop; zero/negative/noninteger counts rejected; partial-write and mid-cancel tests |
| Shutdown | A refused close could leave controls active while the worker stopped; intentional cancellation could be shown as a transport fault | Mark closing/invalidate capabilities before waiting; suppress intentional cancellation faults; latch interruption on thread exit |
| Session UI | Old workspace errors remained after reconnect; reset IR support could leave a capability flag | Clear old errors on fresh connection/identity, remove IR flag on reset |
| Restore UI | A queue rejection could leave a stale preview visible | Clear previous preview before starting a replacement job |
| Layout | Long saved names could inflate combo sizing | Minimum-content sizing, full-name tooltips, compact long-name regression |
| Visuals/help | Disabled hardware controls remained vividly colored; some Unicode headings lacked font glyphs; Getting started topic duplicated | Muted disabled surfaces/text, plain section headings, duplicate removed; actual Qt render reviewed |
| Local checks | Command favorites were absent from local store health reporting | Favorite-store validation added without exposing command contents |

## Verification

- 199 automated tests (177 existing plus 22 audit regressions).
- Actual Qt pages checked at 980×760 and 1672×941 at 200% scaling; no horizontal page overflow. Long stored names also have a targeted compact-layout test.
- Windows CI must pass unit tests, packaged executable launch/render/exit, release packaging and archive verification before handoff.
- Existing identity UID64, no-automatic-command, queue exclusion, stale-session, GPIO confirmation/arming, IR validation, binary transfer and new-folder-only restoration tests remain.

Official protocol source reviewed: https://github.com/flipperdevices/flipperzero-firmware/blob/dev/applications/services/storage/storage_cli.c . Its read output is byte-preserved with a Size header; mkdir/remove/copy print errors and no success body.

## Limits and remaining validation

No physical Flipper device is attached to this build environment. USB/firmware timing, GPIO electrical state, optical IR reception and SD-card behavior still need device testing. Windows launch is headless; manual interaction on the user's display remains useful. This is a source review and regression-testing pass, not an exhaustive security certification or a guarantee of zero defects. Existing adapter limits and unsupported features remain documented. No destructive automatic cleanup, command replay, or automatic reconnection was introduced.
