# PurpleDragonFlipperStudio v1.0.1 — Device Identity Hotfix

Neon GUI v1.0.1 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

Fixed the identity parser requiring a 24-digit hardware UID. Official Flipper f7 firmware returns an 8-byte UID64, represented by 16 hexadecimal digits. The parser now accepts that official length as well as the previously supported 24-digit representation, while preserving model, target, firmware, format and hexadecimal checks.

A fully received, bounded identity reply that fails compatibility validation now leaves USB serial open, shows its reason, and keeps every hardware capability disabled. The console and Identify remain available. A timeout, oversized response, cancellation or USB/transport failure still closes the session to avoid reusing an uncertain response stream.

Extract the complete Windows-x64 ZIP into a new folder and keep _internal beside the executable. Start 1.0.1, connect in CLI mode and select Identify / Refresh device again. No settings migration is needed.

177 automated tests cover the existing workflows plus UID64/previous UID96, invalid identity lengths/characters/target, chunked official-format replies, recoverable unsupported replies and UI connection/capability gates. Windows CI additionally builds, launches, packages and verifies the release. A physical retest on the reported device is still needed; no hardware success is claimed.
