#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-$(command -v python3 || command -v python)}"
if [[ -z "$PYTHON" ]]; then
  echo "Python is required to run this script" >&2
  exit 1
fi

APPLY=false
if [[ ${1:-} == "--apply" ]]; then
  APPLY=true
fi

"$PYTHON" - <<'PY'
import json
import pathlib
import sys
import urllib.request

WORKFLOW = pathlib.Path('.github/workflows/ci-cd.yml')
if not WORKFLOW.exists():
    print("Workflow file not found", file=sys.stderr)
    sys.exit(1)

with urllib.request.urlopen("https://api.github.com/repos/typst/typst/releases/latest") as response:
    data = json.load(response)
LATEST = data.get("tag_name", "v0.0.0").lstrip('v')

content = WORKFLOW.read_text(encoding="utf-8")
CURRENT = "unknown"
for line in content.splitlines():
    if "typst-version:" in line and "latest" not in line:
        CURRENT = line.split(":", 1)[1].strip().strip("'")
        break

print(f"Current workflow Typst version: {CURRENT}")
print(f"Latest Typst release: {LATEST}")

if not bool(${APPLY!s}):
    print("Run with --apply to update the workflow file.")
    sys.exit(0)

if CURRENT == LATEST:
    print("Workflow already matches the latest Typst release.")
    sys.exit(0)

new_lines = []
for line in content.splitlines():
    if "typst-version:" in line and "latest" not in line:
        prefix, _ = line.split(":", 1)
        new_lines.append(f"{prefix}: '{LATEST}'")
    else:
        new_lines.append(line)

WORKFLOW.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"Updated {WORKFLOW} to Typst {LATEST}.")
PY
