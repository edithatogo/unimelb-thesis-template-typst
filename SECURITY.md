# Security

Report vulnerabilities in template tooling, dependencies, CI or release
automation confidentially. Do not publish credentials, unpublished thesis
content, personal data or exploit details in an ordinary issue.

## Reporting

If GitHub private vulnerability reporting is enabled for this repository, use
[Report a vulnerability](https://github.com/edithatogo/unimelb-thesis-template-typst/security/advisories/new).
Its availability must be checked; this policy does not assert that it is enabled.

If that route is unavailable, open an issue asking the maintainer for a
confidential reporting channel. Include no vulnerability details or sensitive
attachments in that request. Provide details only after a private channel is
established. No response deadline or monitored email address is promised here.

## Trust boundaries

- Treat Typst source, imported packages, fonts, images and bibliography files as
  untrusted build inputs. Review versions and sources before using them.
- Compile with an explicit project root. Do not expand the root to a home
  directory or a location containing credentials or unrelated private files.
- Build untrusted material in an isolated environment without publication
  credentials. Keep test fixtures synthetic.
- Keep Actions pinned to full commit SHAs and restrict token permissions to the
  jobs that need them. Coverage uploads use OIDC; do not commit upload tokens.
- Keep release publication limited to version tags. Do not grant dependency bots
  a bypass of the automated checks.
- Preserve existing privacy and secret scans. Offline-security checks remain
  subject to their documented runner, scanner and integration prerequisites.

A coverage report demonstrates exercised Python paths, not a security audit or
a guarantee that a document is safe. A successful local policy check validates
desired configuration; live GitHub enforcement requires a separate observation.

For changes and owner recovery, follow [the maintenance guide](docs/maintenance.md).
Record any emergency bypass and restore normal automated checks afterwards.
