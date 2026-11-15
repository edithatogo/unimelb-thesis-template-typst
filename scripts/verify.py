#!/usr/bin/env python3
"""Verify shipped PDFs and the bounded COR-01 corpus with one command runner."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "verification"
TIMEOUT_SECONDS = 60
DOCUMENTS = ("thesis.typ", "sample-chapter.typ")
ORACLES = "tests/rendered/cor01/oracles.py"


class VerificationError(Exception):
    """A required verification command or PDF contract failed."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def run(command: list[str], log_name: str, commands=None, *, combined=False) -> str:
    """Retain each command, exit, diagnostic and timeout before reporting failure."""
    log_path = OUTPUT / log_name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "command": command,
        "cwd": str(ROOT),
        "environment_overrides": {"SOURCE_DATE_EPOCH": "0"},
        "timeout_seconds": TIMEOUT_SECONDS,
        "log": str(log_path.relative_to(ROOT)),
        "exit_code": None,
        "timed_out": False,
    }
    started = time.monotonic()
    stdout = stderr = ""
    failure = None
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
        stdout, stderr = result.stdout, result.stderr
        record["exit_code"] = result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = _text(exc.stdout), _text(exc.stderr)
        record["timed_out"] = True
        failure = f"command exceeded its {TIMEOUT_SECONDS}s time budget"
    except OSError as exc:
        failure = f"command could not start: {exc}"
    record["duration_seconds"] = time.monotonic() - started
    record["stdout_sha256"] = hashlib.sha256(stdout.encode("utf-8")).hexdigest()
    record["stderr_sha256"] = hashlib.sha256(stderr.encode("utf-8")).hexdigest()
    if failure:
        record["error"] = failure
    log_path.write_text(
        f"Command: {command!r}\nExit: {record['exit_code']}\n"
        f"Timed out: {record['timed_out']}\n"
        f"Stdout:\n{stdout}\nStderr:\n{stderr}\n"
        + (f"Error: {failure}\n" if failure else ""),
        encoding="utf-8",
    )
    record["log_sha256"] = digest(log_path)
    if commands is not None:
        commands.append(record)
    if failure:
        raise VerificationError(f"{log_name}: {failure}; see {log_path}")
    if record["exit_code"] != 0:
        raise VerificationError(
            f"{log_name}: command failed with exit {record['exit_code']}; see {log_path}"
        )
    return stdout + stderr if combined else stdout


def clear_previous_outputs():
    """Delete only generated verifier outputs, never the retained COR-01 baseline."""
    for directory in (OUTPUT, OUTPUT / "cor01"):
        directory.mkdir(parents=True, exist_ok=True)
        for path in directory.iterdir():
            if path.suffix in {".pdf", ".txt", ".log"} and (path.is_file() or path.is_symlink()):
                path.unlink()


def verify_pdf(source: str, pdf: Path, log_prefix: str, commands, compile_options=()):
    """Use the same compiler/PDF checks for shipped and synthetic documents."""
    pdf.unlink(missing_ok=True)
    text_path = pdf.with_suffix(".txt")
    text_path.unlink(missing_ok=True)
    source_path = ROOT / source
    if not source_path.is_file():
        raise VerificationError(f"Required document source not found: {source}")
    source_hash = digest(source_path)
    run(
        ["typst", "compile", "--root", ".", *compile_options, source, str(pdf)],
        log_prefix + "-compile.log",
        commands,
    )
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise VerificationError(f"{source}: compiler produced no PDF")
    run(["qpdf", "--check", str(pdf)], log_prefix + "-qpdf.log", commands)
    info = run(["pdfinfo", str(pdf)], log_prefix + "-pdfinfo.log", commands)
    page_match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if page_match is None or int(page_match.group(1)) < 1:
        raise VerificationError(f"{source}: PDF has no readable page count")
    extracted = run(
        ["pdftotext", "-layout", str(pdf), "-"], log_prefix + "-pdftotext.log", commands,
    )
    text_path.write_text(extracted, encoding="utf-8")
    if not extracted.strip():
        raise VerificationError(f"{source}: PDF contains no extractable text")
    return {
        "source": source,
        "source_sha256": source_hash,
        "pdf": str(pdf.relative_to(ROOT)),
        "pdf_sha256": digest(pdf),
        "text": str(text_path.relative_to(ROOT)),
        "text_sha256": digest(text_path),
        "pages": int(page_match.group(1)),
        "bytes": pdf.stat().st_size,
    }, extracted


def verify_cor01(report, oracle):
    specimens = oracle["specimens"]()
    expected_count = oracle["EXPECTED_SPECIMEN_COUNT"]
    if len(specimens) != expected_count or expected_count != 14:
        raise VerificationError("The bounded COR-01 corpus must contain all 14 specimens")
    identifiers = [case["id"] for case in specimens]
    if len(set(identifiers)) != len(identifiers) or any(
        not re.fullmatch(r"[a-z0-9-]+", identifier) for identifier in identifiers
    ):
        raise VerificationError("COR-01 specimen identities are invalid or duplicated")
    corpus = report["rendered_corpus"]
    corpus["expected_specimen_count"] = expected_count
    corpus["creation_timestamp"] = oracle["CREATION_TIMESTAMP"]
    corpus["source_sha256"] = {
        source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]
    }
    corpus["oracle_sha256"] = digest(ROOT / ORACLES)
    corpus["result"] = "fail"
    for case in specimens:
        identifier = case["id"]
        entry = {
            "id": identifier,
            "fixture": case["fixture"],
            "inputs": case["inputs"],
            "result": "fail",
            "commands": [],
            "errors": [],
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "cor01"):
                raise VerificationError("COR-01 fixture escapes the controlled fixture directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(
                json.dumps(case["inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            options = [
                "--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"],
            ]
            for key, value in sorted(case["inputs"].items()):
                options.extend(["--input", f"{key}={value}"])
            details, extracted = verify_pdf(
                case["fixture"], OUTPUT / "cor01" / (identifier + ".pdf"),
                "cor01/" + identifier, entry["commands"], options,
            )
            entry.update(details)
            assertions = oracle["check_text"](case, extracted, details["pages"])
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        # Failed compilations may still leave partial outputs. Bind them as
        # failure evidence, without allowing them to count as a successful PDF.
        for suffix, key in ((".pdf", "pdf"), (".txt", "text")):
            artifact = OUTPUT / "cor01" / (identifier + suffix)
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    if corpus["passed_count"] != expected_count:
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("COR-01 rendered checks failed: " + ", ".join(failures))
    corpus["result"] = "pass"


def write_report(report):
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {
        "schema_version": 1,
        "passed": False,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version.split()[0],
        "command_timeout_seconds": TIMEOUT_SECONDS,
        "verifier_sha256": digest(Path(__file__)),
        "commands": [],
        "documents": [],
        "rendered_corpus": {
            "requirement": "COR-01",
            "scope": "Bounded synthetic declaration, table, footnote and appendix-reference text",
            "result": "unexecuted",
            "specimens": [],
        },
    }
    # An interrupted invocation must not leave a previous successful receipt.
    write_report(report)
    try:
        clear_previous_outputs()
        oracle = runpy.run_path(str(ROOT / ORACLES))
        report["executables"] = {}
        for executable in ("typst", "qpdf", "pdfinfo", "pdftotext"):
            resolved = shutil.which(executable)
            if resolved is None:
                raise VerificationError(f"Required executable not found: {executable}")
            report["executables"][executable] = {
                "path": resolved, "sha256": digest(Path(resolved)),
            }
        with (ROOT / "typst.toml").open("rb") as source:
            expected_version = tomllib.load(source)["tool"]["typst"]["version"]
        report["typst_manifest_sha256"] = digest(ROOT / "typst.toml")
        version = run(["typst", "--version"], "typst-version.log", report["commands"]).strip()
        if version.split()[:2] != ["typst", expected_version]:
            raise VerificationError(
                f"Expected Typst {expected_version} from typst.toml, got {version!r}"
            )
        report["compiler"] = version
        report["tool_versions"] = {"typst": version}
        for name, arguments in (
            ("qpdf", ["qpdf", "--version"]),
            ("pdfinfo", ["pdfinfo", "-v"]),
            ("pdftotext", ["pdftotext", "-v"]),
        ):
            value = run(arguments, name + "-version.log", report["commands"], combined=True).strip()
            report["tool_versions"][name] = value.splitlines()[0] if value else ""
        report["source_revision"] = None
        report["source_dirty"] = None
        if (ROOT / ".git").exists() and shutil.which("git"):
            report["source_revision"] = run(
                ["git", "rev-parse", "HEAD"], "source-revision.log", report["commands"],
            ).strip()
            report["source_dirty"] = bool(run(
                ["git", "status", "--porcelain"], "source-state.log", report["commands"],
            ).strip())
        for source in DOCUMENTS:
            name = Path(source).stem
            entry = {"source": source, "result": "fail", "commands": []}
            report["documents"].append(entry)
            try:
                details, _extracted = verify_pdf(
                    source, OUTPUT / f"{name}.pdf", name, entry["commands"],
                )
                entry.update(details)
                entry["result"] = "pass"
            except Exception as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
                raise
        verify_cor01(report, oracle)
        report["passed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"Verification failed: {exc}", file=sys.stderr)
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_report(report)
    if report["passed"]:
        print("Verified thesis/sample PDFs and 14 COR-01 specimens; evidence: build/verification/report.json")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
