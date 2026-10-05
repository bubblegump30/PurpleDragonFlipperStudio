# Release procedure

1. Commit the release changes on main and allow the Windows build workflow to pass.
2. Download the Actions artifact. Extract it to obtain the Source ZIP, Windows-x64 ZIP, SHA256SUMS.txt, and release-manifest.json.
3. Confirm the manifest commit matches the successful workflow commit. Test the Windows ZIP after extracting it, keeping _internal beside the executable.
4. In PowerShell, run `Get-FileHash *.zip -Algorithm SHA256` and compare both archive hashes with SHA256SUMS.txt.
5. Create a release tag at that exact commit. Paste the matching release notes and attach all four files. Never attach an older source ZIP to a newer Windows build.

The repository is MIT licensed. Dependencies retain their upstream licenses. Hardware integration is separate from executable packaging and remains unverified.

Local source-only packaging: `python scripts/package_release.py --output release-assets`.
Local packaging with an existing Windows build: `python scripts/package_release.py --windows dist/PurpleDragonFlipperStudio --output release-assets`.

Packaging requires committed tracked changes. Source archives include only Git-tracked files. Untracked files and local settings are excluded.
