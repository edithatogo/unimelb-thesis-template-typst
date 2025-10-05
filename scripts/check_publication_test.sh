#!/usr/bin/env bash
# Quick check script for publication/test to be used in CI or locally.
set -euo pipefail

# Build PDF
typst compile test-publications.typ test-publications.pdf

# Extract text
pdftotext -f 1 -l 5 test-publications.pdf - | sed -n '1,200p' > /tmp/test-publications.txt

# Grep for suspicious serialized layout fragments
if grep -E "set text\(|text\(\[|line\(|counter\(|show raw|show link" /tmp/test-publications.txt >/dev/null; then
  echo "WARNING: suspicious layout-like strings found in extracted PDF text"
  grep -nE "set text\(|text\(\[|line\(|counter\(|show raw|show link" /tmp/test-publications.txt || true
  exit 2
else
  echo "OK: no obvious serialized layout fragments found in extracted PDF text"
fi
