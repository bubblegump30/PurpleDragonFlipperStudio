# Contributing to PurpleDragonFlipperStudio

Neon GUI v0.3.0 · Created by KyleAustinHillier @PurpleDragonFoundationLtd

Thank you for helping improve the desktop app. Read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

## Report a bug or suggest an improvement

Search existing issues first, then use the bug report or feature request template. Include the app version, operating system, screen resolution and display scaling for layout bugs, reproduction steps, and expected versus actual behavior. Redact personal information from screenshots and logs.

Report vulnerabilities using [SECURITY.md](SECURITY.md), rather than a public bug report.

## Set up a development environment

Use standard 64-bit CPython 3.10–3.14.

On Windows, run `Setup.bat`, then `Start.bat`. For a manual development environment:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
python -m unittest discover -s tests -v
```

For a headless Qt test run on Linux, set `QT_QPA_PLATFORM=offscreen`. Windows packaging uses `Build-Windows.bat` and the GitHub Actions workflow.

## Submit a pull request

1. Fork the repository and create a focused branch from current `main`.
2. Make a focused change and explain the user-visible benefit.
3. Run the relevant tests; for behavioral changes, add a regression test where useful.
4. For UI changes, check both compact and desktop layouts and include screenshots with display scaling.
5. Describe validation results, limitations, and any hardware or firmware used.
6. Update relevant documentation when behavior changes.

Keep generated builds, virtual environments, private logs, credentials, and local settings out of commits. Avoid unrelated reformatting and new dependencies unless they are necessary.

## Hardware integration

A serial connection does not establish device identity or confirm a working hardware feature. GPIO, IR transmission, SD backup, app installation, and telemetry remain gated until the backend supports and validates them. Preserve these capability checks. Do not claim hardware validation without testing the relevant device and firmware; use hardware you own or are authorized to test.

## License and attribution

Project contributions are provided under the [MIT License](LICENSE). Only submit work you have permission to contribute. Retain required third-party notices; the project license does not replace the licenses of dependencies or grant rights to third-party trademarks.
