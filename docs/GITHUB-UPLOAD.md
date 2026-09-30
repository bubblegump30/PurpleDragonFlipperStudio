# Initial GitHub upload

Target: https://github.com/bubblegump30/PurpleDragonFlipperStudio

The connected repository was empty when this package was prepared. No remote changes have been made.

Extract this package, open PowerShell inside its top-level folder, and run:

```powershell
git init -b main
git add .
git status --short
git commit -m "Add PurpleDragonFlipperStudio v0.3.0"
git remote add origin https://github.com/bubblegump30/PurpleDragonFlipperStudio.git
git push -u origin main
```

Git may ask for your author identity and GitHub sign-in. Set your preferred identity if prompted. If the repository has acquired commits since preparation, fetch and review them before uploading; do not force-push.

After upload, open Actions → Windows build → Run workflow. The workflow runs the tests, builds on Windows, and provides a Windows executable-folder artifact. A successful workflow is packaging evidence, not physical-device verification.

Create a draft/pre-release for tag v0.3.0 using docs/RELEASE-v0.3.0.md only when ready. Attach the complete source ZIP. Attach a Windows artifact only after reviewing the build and testing it locally.

Suggested About description: Neon-themed Windows desktop companion for Flipper serial workflows, local GPIO presets, IR inspection, settings backups and diagnostics.

Suggested website: https://www.purpledragonfoundationltd.xyz/

Suggested topics: flipper-zero, python, pyside6, windows, serial, uart, desktop-app, neon-ui.

No project license was selected in the supplied source. Decide the distribution license before advertising this as open source; dependencies and supplied artwork retain their applicable rights.
