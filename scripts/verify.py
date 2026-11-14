#!/usr/bin/env python3
"""Compile the two shipped documents and validate their PDFs with bounded commands."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "verification"
TIMEOUT_SECONDS = 60
DOCUMENTS = ("thesis.typ", "sample-chapter.typ")


class VerificationError(Exception):
    """A required verification command or PDF contract failed."""


def run(command: list[str], log_name: str) -> str:
    """Save complete diagnostic output and fail on errors or timeouts."""
    log_path = OUTPUT / log_name
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        log_path.write_text(
            f"Command timed out after {TIMEOUT_SECONDS}s: {command!r}\n"
            f"Partial stdout: {exc.stdout!r}\nPartial stderr: {exc.stderr!r}\n",
            encoding="utf-8",
        )
        raise VerificationError(f"{log_name}: command exceeded its time budget") from exc
    log_path.write_text(
        f"Command: {command!r}\nExit: {result.returncode}\n"
        f"{result.stdout}\n{result.stderr}",
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise VerificationError(
            f"{log_name}: command failed with exit {result.returncode}; see {log_path}"
        )
    return result.stdout


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "passed": False,
        "command_timeout_seconds": TIMEOUT_SECONDS,
        "documents": [],
    }
    try:
        for executable in ("typst", "qpdf", "pdfinfo", "pdftotext"):
            if shutil.which(executable) is None:
                raise VerificationError(f"Required executable not found: {executable}")
        with (ROOT / "typst.toml").open("rb") as source:
            expected_version = tomllib.load(source)["tool"]["typst"]["version"]
        version = run(["typst", "--version"], "typst-version.log").strip()
        if version.split()[:2] != ["typst", expected_version]:
            raise VerificationError(
                f"Expected Typst {expected_version} from typst.toml, got {version!r}"
            )
        report["compiler"] = version
        for source in DOCUMENTS:
            name = Path(source).stem
            pdf = OUTPUT / f"{name}.pdf"
            # A stale successful PDF must never stand in for this invocation.
            pdf.unlink(missing_ok=True)
            run(
                ["typst", "compile", "--root", ".", source, str(pdf)],
                f"{name}-compile.log",
            )
            if not pdf.is_file() or pdf.stat().st_size == 0:
                raise VerificationError(f"{source}: compiler produced no PDF")
            run(["qpdf", "--check", str(pdf)], f"{name}-qpdf.log")
            info = run(["pdfinfo", str(pdf)], f"{name}-pdfinfo.log")
            page_match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
            if page_match is None or int(page_match.group(1)) < 1:
                raise VerificationError(f"{source}: PDF has no readable page count")
            extracted = run(
                ["pdftotext", str(pdf), "-"], f"{name}-pdftotext.log"
            )
            if not extracted.strip():
                raise VerificationError(f"{source}: PDF contains no extractable text")
            report["documents"].append({
                "source": source,
                "pdf": str(pdf.relative_to(ROOT)),
                "pages": int(page_match.group(1)),
                "bytes": pdf.stat().st_size,
            })
        report["passed"] = True
    except (VerificationError, OSError, KeyError, tomllib.TOMLDecodeError) as exc:
        report["error"] = str(exc)
        print(f"Verification failed: {exc}", file=sys.stderr)
    finally:
        (OUTPUT / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    if report["passed"]:
        print("Verified thesis and sample PDFs; evidence: build/verification/report.json")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
