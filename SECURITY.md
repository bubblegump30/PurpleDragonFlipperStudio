# Security Policy

## Supported versions

Security fixes target the latest code on `main` and the latest published release, currently v0.3.0. Earlier versions are not separately maintained. There is no guaranteed response or patch deadline.

## Reporting a vulnerability

Do not disclose exploitable vulnerabilities, credentials, private logs, or proof-of-concept attacks in public issues.

If the repository's Security tab offers **Report a vulnerability**, use it to submit a private report. Otherwise, use a private contact method listed by the repository owner, [bubblegump30](https://github.com/bubblegump30), or request a private reporting channel without posting vulnerability details.

Include:

- Affected version or commit and operating system.
- A description of the vulnerability and its impact.
- Minimal reproduction steps and any relevant sanitized evidence.
- Whether hardware or a particular firmware version is required.

Allow the maintainer time to investigate and coordinate disclosure. The project does not currently offer a bug bounty.

## Scope and safe testing

Relevant areas include serial input handling, imported IR files, settings backups, diagnostics, local file operations, dependency vulnerabilities, and release packaging. Test only systems and hardware you own or have permission to assess.

Never include passwords, tokens, personal file paths, private device identifiers, or sensitive serial output in a public report. Download releases from this repository and keep the packaged executable together with its required support files.
