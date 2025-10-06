#!/usr/bin/env bash
# Compile the key examples from the repo root
# Usage: ./scripts/compile_examples.sh
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "Compiling example-run.typ..."
typst compile example-run.typ

echo "Compiling examples/run-basic.typ with --root . ..."
typst compile --root . examples/run-basic.typ

echo "Compiling examples/basic.typ with --root . ..."
typst compile --root . examples/basic.typ

echo "Compiling example-config.typ..."
typst compile --root . example-config.typ

echo "Compiling sample-config-with-features.typ..."
typst compile --root . sample-config-with-features.typ

echo "Compiling thesis.typ..."
typst compile --root . thesis.typ

echo "Compiling sample-chapter.typ..."
typst compile --root . sample-chapter.typ

echo "All specified examples compiled. PDFs are in the repository root or examples/ as appropriate."