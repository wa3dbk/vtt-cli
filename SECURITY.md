# Security Policy

## Supported Versions

Only the latest minor version on `main` receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✓         |
| < 0.1   | ✗         |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security problems.

Report privately via GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability) on this repository, or by opening a draft advisory under the **Security** tab.

Please include:

- A description of the issue and its impact.
- Steps to reproduce (a minimal VTT fixture is ideal).
- The affected version or commit SHA.
- Any suggested mitigation.

You can expect an initial acknowledgement within 7 days. We aim to ship a fix or a documented workaround within 30 days for confirmed vulnerabilities, and will credit reporters in the release notes unless they prefer to remain anonymous.

## Scope

In scope:

- Crashes, hangs, or unbounded resource consumption triggered by crafted VTT input.
- Path traversal, arbitrary file write, or command injection via CLI arguments, taxonomy YAML, or pipeline YAML.
- Information disclosure in emitted outputs beyond what the input contains.

Out of scope:

- Issues that require the attacker to already control the process environment or write arbitrary files to the user's machine.
- Correctness bugs in normalization (please file a regular issue).
