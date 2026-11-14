# Coding assistant guidance

[AGENTS.md](../AGENTS.md) is the canonical repository instruction file.
Read it and the relevant issue before editing; reconcile current main and open
PRs so that work is not duplicated.

Run `make verify` from the repository root and report the exact result.
Use [CONTRIBUTING.md](../CONTRIBUTING.md) for tool versions, focused validation
commands and coverage scope. Do not claim a command ran when the environment
was unavailable.

Keep thesis interfaces compatible, examples synthetic, Actions pinned and
publishing tag-only. Retain zero mandatory human approvals and the documented
owner recovery path. Preserve the conditional offline-security work in PR #9.

Use [SECURITY.md](../SECURITY.md) for sensitive reports and
[docs/maintenance.md](../docs/maintenance.md) for live settings and drift evidence.
Do not copy private thesis content, research data or credentials into PRs or logs.
