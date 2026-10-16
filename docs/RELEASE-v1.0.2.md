# PurpleDragonFlipperStudio v1.0.2 — Audit & Polish

Neon GUI v1.0.2 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

- Preserves corrupt preset data across delete/rename/duplicate/export instead of replacing it with empty data.
- Adds shared bounded UTF-8/JSON imports, duplicate-key checks, nesting and numeric limits, and invalid-Unicode handling.
- Makes local backup validation cancellation-aware and prevents a cancelled download from replacing an existing local file.
- Requires recognized SD mutation replies and handles partial/invalid serial writes correctly.
- Disables device work while shutdown waits, suppresses cancellation-as-fault messages, and clears old workspace errors after reconnect.
- Clears stale restore previews and IR capability flags.
- Handles malformed saved geometry/numbers, adds command-favorite local checks, and prevents long names from widening compact pages.
- Gives disabled GPIO buttons neutral styling, removes unsupported heading glyphs/duplicate help text, and improves long-name/activity tooltips.

199 automated tests include 22 new audit regressions. All workspace pages were inspected at compact and desktop sizes at 200% scaling without horizontal page overflow. Windows CI builds, launches, packages and verifies the actual executable and matching source archive. See AUDIT-v1.0.2.md for scope and evidence.

Install by extracting the complete Windows-x64 ZIP into a new folder and running the executable beside _internal. Export settings and IR libraries before upgrading. Invalid stores remain preserved; recover them from a valid backup before editing. The UID64 identity fix from 1.0.1 remains included.

Physical GPIO/IR/SD and firmware testing remains pending. This software audit and automated testing do not establish that every bug is eliminated. Disconnect does not undo GPIO writes, IR emission or SD changes already performed.
