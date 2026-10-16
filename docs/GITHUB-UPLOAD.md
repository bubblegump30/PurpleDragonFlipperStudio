# Release procedure — 1.0

1. Commit release changes on main and wait for Windows build to succeed, including tests, packaged GUI smoke test and archive verification.
2. Download/extract the Actions artifact. It contains the Source ZIP, Windows-x64 ZIP, SHA256SUMS.txt and release-manifest.json.
3. Confirm the manifest commit equals the successful workflow commit. In PowerShell, run `Get-FileHash *.zip -Algorithm SHA256` and compare with the trusted checksum list.
4. From source, optionally run `python scripts/verify_release.py PATH-TO-EXTRACTED-ARTIFACT --expected-commit COMMIT --require-windows`. The verifier reads ZIPs without extracting/executing them. It checks integrity and metadata consistency, not code signatures or trust in an untrusted manifest.
5. Extract the Windows ZIP into a new folder and test the actual GUI interactively, keeping _internal beside the executable. Check 100%/200% display scaling and your hardware/firmware before making hardware compatibility claims.
6. Create tag v1.0.1 at the exact verified commit. Paste docs/RELEASE-v1.0.1.md and attach all four files. Do not mix artifacts from different builds. Publication is a separate action; the build workflow never publishes automatically.

Windows ZIP contents include README-FIRST.txt, LICENSE.txt, DEPENDENCIES.md, RELEASE-NOTES.md, licenses/, release-info.json, the executable and _internal. Package metadata records the packaging commit; it is not a digital signature of the binary. CI builds and packages from one checkout.

Local source-only packaging: `python scripts/package_release.py --output release-assets`.

Local Windows checks: `python scripts/smoke_windows.py dist/PurpleDragonFlipperStudio/PurpleDragonFlipperStudio.exe`, then `python scripts/package_release.py --windows dist/PurpleDragonFlipperStudio --output release-assets`, then the verifier.

Packaging requires committed tracked changes; source archives contain tracked files only. Export settings and IR libraries separately before upgrades. The project is MIT licensed; dependencies retain their own terms. Physical hardware validation is separate from packaging.
