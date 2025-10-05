#!/usr/bin/env python3
"""Preflight checks for the University of Melbourne Typst template.

The script compiles nominated Typst documents across the configured build
profiles and performs lightweight metadata sanity checks so that issues can
be caught prior to submission. It is designed to run locally or in CI.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = REPO_ROOT / "build" / "preflight"
DEFAULT_DOCUMENT = REPO_ROOT / "thesis.typ"
DEFAULT_PROFILES = ("default",)
EXTRA_TARGETS = (
    REPO_ROOT / "test-layout-only.typ",
    REPO_ROOT / "sample-chapter.typ",
)
PLACEHOLDER_STRINGS = {
    "<title>",
    "<author>",
    "<degree>",
    "<department>",
    "<school>",
}


class PreflightError(Exception):
    """Raised when any preflight check fails."""


def run(command: List[str], *, cwd: Path | None = None) -> Tuple[int, str]:
    """Execute a command and return its exit status and combined output."""
    process = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    return process.returncode, process.stdout


def ensure_typst_available() -> None:
    if shutil.which("typst") is None:
        raise PreflightError(
            "Typst CLI not found in PATH. Install Typst or activate the toolchain "
            "before running the preflight check."
        )


def compile_document(path: Path, profile: str) -> Path:
    if not path.exists():
        raise PreflightError(f"Document '{path}' does not exist.")

    output_dir = BUILD_DIR / profile
    output_dir.mkdir(parents=True, exist_ok=True)
    suffix = "" if profile == "default" else f"-{profile}"
    output_path = output_dir / f"{path.stem}{suffix}.pdf"

    command = ["typst", "compile", str(path), str(output_path)]
    if profile != "default":
        command.extend(["--input", f"profile={profile}"])

    status, output = run(command, cwd=REPO_ROOT)
    if status != 0:
        raise PreflightError(
            f"Typst compilation failed for '{path}' (profile '{profile}').\n{output}"
        )
    return output_path


def scan_for_placeholders(path: Path) -> List[str]:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PreflightError(f"Failed to read '{path}': {exc}") from exc

    issues: List[str] = []
    for placeholder in PLACEHOLDER_STRINGS:
        if placeholder in content:
            issues.append(f"Placeholder '{placeholder}' found in {path.name}")
    return issues


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Typst template preflight checks.")
    parser.add_argument(
        "--document",
        type=Path,
        default=DEFAULT_DOCUMENT,
        help="Path to the primary Typst document (default: thesis.typ)",
    )
    parser.add_argument(
        "--profile",
        dest="profiles",
        action="append",
        help="Build profile to compile (can be supplied multiple times).",
    )
    parser.add_argument(
        "--extra",
        dest="extra_targets",
        action="append",
        type=Path,
        help="Additional Typst sources to compile alongside the primary document.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        help="Emit results as JSON (useful for CI integrations).",
    )
    return parser.parse_args(list(argv))


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    ensure_typst_available()

    profiles = tuple(args.profiles) if args.profiles else DEFAULT_PROFILES
    extra = tuple(args.extra_targets) if args.extra_targets else EXTRA_TARGETS

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    compiled: List[Path] = []
    metadata_warnings: List[str] = []

    # Metadata placeholder checks on the main document only
    metadata_warnings.extend(scan_for_placeholders(args.document))

    for profile in profiles:
        compiled.append(compile_document(args.document, profile))
        for extra_target in extra:
            if extra_target.exists():
                compiled.append(compile_document(extra_target, profile))

    result = {
        "compiled": [str(path.relative_to(REPO_ROOT)) for path in compiled],
        "metadata_warnings": metadata_warnings,
        "profiles": profiles,
    }

    if args.emit_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Preflight successful. Compiled artefacts:")
        for path in result["compiled"]:
            print(f"  - {path}")
        if metadata_warnings:
            print("Warnings:")
            for warning in metadata_warnings:
                print(f"  - {warning}")

    if metadata_warnings:
        # Return a non-zero code so CI can surface the warnings while still
        # producing artefacts for inspection. The exit code mirrors lint-like
        # tooling behaviour.
        return 2

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except PreflightError as exc:
        print(f"Preflight failed: {exc}", file=sys.stderr)
        sys.exit(1)
