#!/usr/bin/env python3
"""Verify shipped PDFs and bounded content, navigation, configuration and privacy and optional-section corpora."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import signal
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "build" / "verification"
TIMEOUT_SECONDS = 60
CLEANUP_TIMEOUT_SECONDS = 5
DOCUMENTS = ("thesis.typ", "sample-chapter.typ")
ORACLES = "tests/rendered/cor01/oracles.py"
NAVIGATION_ORACLES = "tests/rendered/cor02/oracles.py"
CONFIGURATION_ORACLES = "tests/rendered/cor03/oracles.py"
BLIND_ORACLES = "tests/rendered/cor04/oracles.py"
TERMS_ORACLES = "tests/rendered/terms/oracles.py"
IMAGE_ORACLES = "tests/rendered/images/oracles.py"
LAYOUT_ORDER_ORACLES = "tests/rendered/layout-order/oracles.py"
OPTIONAL_ORACLES = "tests/rendered/cor05/oracles.py"
NATIVE_EVIDENCE = "scripts/native_evidence.py"
NATIVE_ORACLES = "tests/rendered/native/oracles.py"


class VerificationError(Exception):
    """A required verification command or PDF contract failed."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def _stop_command(process):
    """Terminate the command's own POSIX group, even after its leader exits."""
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
    except ProcessLookupError:
        pass


def run(command: list[str], log_name: str, commands=None, *, combined=False, expected_exit=0) -> str:
    """Retain each command, exit, diagnostic and timeout before reporting failure."""
    log_path = OUTPUT / log_name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "command": command,
        "cwd": str(ROOT),
        "environment_overrides": {"SOURCE_DATE_EPOCH": "0"},
        "timeout_seconds": TIMEOUT_SECONDS,
        "cleanup_timeout_seconds": CLEANUP_TIMEOUT_SECONDS,
        "process_isolation": "posix-session" if os.name == "posix" else "direct-process",
        "log": str(log_path.relative_to(ROOT)),
        "exit_code": None,
        "expected_exit_code": expected_exit,
        "timed_out": False,
    }
    started = time.monotonic()
    stdout = stderr = ""
    failure = None
    process = None
    cleanup_deadline = None
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env={**os.environ, "SOURCE_DATE_EPOCH": "0"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=os.name == "posix",
        )
        try:
            stdout, stderr = process.communicate(timeout=TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            stdout, stderr = _text(exc.stdout), _text(exc.stderr)
            record["timed_out"] = True
            failure = f"command exceeded its {TIMEOUT_SECONDS}s time budget"
            cleanup_deadline = time.monotonic() + CLEANUP_TIMEOUT_SECONDS
            _stop_command(process)
            try:
                stdout, stderr = process.communicate(
                    timeout=max(0, cleanup_deadline - time.monotonic()),
                )
            except subprocess.TimeoutExpired as cleanup:
                stdout, stderr = _text(cleanup.stdout), _text(cleanup.stderr)
                record["cleanup_error"] = "Output pipes did not close within the cleanup budget"
                failure += "; " + record["cleanup_error"]
    except OSError as exc:
        failure = f"command could not start or be controlled: {exc}"
    finally:
        if process is not None:
            if process.poll() is None:
                cleanup_deadline = cleanup_deadline or time.monotonic() + CLEANUP_TIMEOUT_SECONDS
                try:
                    _stop_command(process)
                    process.wait(timeout=max(0, cleanup_deadline - time.monotonic()))
                except (OSError, subprocess.TimeoutExpired) as exc:
                    record["cleanup_error"] = f"Command could not be reaped: {exc}"
                    failure = (failure + "; " if failure else "") + record["cleanup_error"]
            record["exit_code"] = process.returncode
            for pipe in (process.stdout, process.stderr):
                if pipe is not None:
                    pipe.close()
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
    if record["exit_code"] != expected_exit:
        raise VerificationError(
            f"{log_name}: exit {record['exit_code']} != expected {expected_exit}; see {log_path}"
        )
    return stdout + stderr if combined else stdout


def clear_previous_outputs():
    """Delete generated verifier outputs without touching retained baselines."""
    for directory in (OUTPUT, OUTPUT / "cor01", OUTPUT / "cor02", OUTPUT / "cor03", OUTPUT / "cor04", OUTPUT / "terms", OUTPUT / "images", OUTPUT / "layout-order", OUTPUT / "cor05", OUTPUT / "native"):
        directory.mkdir(parents=True, exist_ok=True)
        suffixes = {".pdf", ".txt", ".log"}
        if directory in (OUTPUT / "cor02", OUTPUT / "cor03", OUTPUT / "cor04", OUTPUT / "terms", OUTPUT / "images", OUTPUT / "layout-order", OUTPUT / "cor05", OUTPUT / "native"):
            suffixes.update({".json", ".html", ".xml"})
        for path in directory.iterdir():
            if path.suffix in suffixes and (path.is_file() or path.is_symlink()):
                path.unlink()
    package_gate = runpy.run_path(str(ROOT / "scripts/verify_package.py"))
    package_gate["clean_output"](ROOT, OUTPUT / "package")


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


def verify_cor02(report, oracle):
    """Inspect native PDF navigation only for the three controlled specimens."""
    identifiers = oracle["EXPECTED_SPECIMENS"]
    if identifiers != ("navigation", "appendix-pages", "appendix-layout"):
        raise VerificationError("The bounded COR-02 corpus must contain all three specimens")
    corpus = report["navigation_corpus"]
    corpus["expected_specimen_count"] = len(identifiers)
    corpus["creation_timestamp"] = oracle["CREATION_TIMESTAMP"]
    corpus["source_sha256"] = {
        source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]
    }
    corpus["oracle_sha256"] = digest(ROOT / NAVIGATION_ORACLES)
    corpus["result"] = "fail"
    for identifier in identifiers:
        source = f"tests/rendered/cor02/{identifier}.typ"
        pdf = OUTPUT / "cor02" / (identifier + ".pdf")
        structure = pdf.with_suffix(".qpdf.json")
        boxes = pdf.with_suffix(".bbox.html")
        assertions_path = pdf.with_suffix(".oracle.json")
        entry = {"id": identifier, "fixture": source, "result": "fail", "commands": [], "errors": []}
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / source
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "cor02"):
                raise VerificationError("COR-02 fixture escapes the controlled fixture directory")
            entry["fixture_sha256"] = digest(fixture)
            for artifact in (structure, boxes, assertions_path):
                artifact.unlink(missing_ok=True)
            details, extracted = verify_pdf(
                source, pdf, "cor02/" + identifier, entry["commands"],
                ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"]],
            )
            entry.update(details)
            native = run(
                ["qpdf", "--json", str(pdf)], f"cor02/{identifier}-qpdf-json.log", entry["commands"],
            )
            structure.write_text(native, encoding="utf-8")
            bounding_boxes = run(
                ["pdftotext", "-bbox-layout", str(pdf), "-"],
                f"cor02/{identifier}-bbox.log", entry["commands"],
            )
            boxes.write_text(bounding_boxes, encoding="utf-8")
            assertions = oracle["analyze"](json.loads(native), extracted, identifier, bounding_boxes)
            assertions_path.write_text(
                json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            checks = assertions.get("checks", [])
            if not checks or not all(check.get("passed") is True for check in checks):
                if not entry["errors"]:
                    entry["errors"].append("COR-02 oracle has missing or failed assertions")
            if assertions.get("passed") is not True and not entry["errors"]:
                entry["errors"].append("COR-02 oracle did not explicitly pass")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        # Native structures and partial outputs remain failure evidence if a
        # later command, parse or semantic assertion fails.
        for artifact, key in (
            (pdf, "pdf"), (pdf.with_suffix(".txt"), "text"),
            (structure, "pdf_structure"), (boxes, "bounding_boxes"),
            (assertions_path, "oracle_report"),
        ):
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    if corpus["passed_count"] != len(identifiers):
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("COR-02 rendered checks failed: " + ", ".join(failures))
    corpus["result"] = "pass"


def verify_cor03(report, oracle):
    """Exercise typed legacy options and rendered effects, including rejections."""
    specimens = oracle["specimens"]()
    expected_count = oracle["EXPECTED_SPECIMEN_COUNT"]
    identifiers = [case["id"] for case in specimens]
    if expected_count != 34 or len(specimens) != expected_count:
        raise VerificationError("The bounded COR-03 corpus must contain all 34 specimens")
    if len(set(identifiers)) != expected_count or any(
        not re.fullmatch(r"[a-z0-9-]+", identifier) for identifier in identifiers
    ):
        raise VerificationError("COR-03 specimen identities are invalid or duplicated")
    if sum(case["expected_error"] is not None for case in specimens) != 11:
        raise VerificationError("The bounded COR-03 corpus requires 11 diagnostic rejections")
    corpus = report["configuration_corpus"]
    corpus["expected_specimen_count"] = expected_count
    corpus["creation_timestamp"] = oracle["CREATION_TIMESTAMP"]
    corpus["source_sha256"] = {
        source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]
    }
    corpus["resource_sha256"] = {
        source: digest(ROOT / source) for source in oracle["RESOURCE_FILES"]
    }
    corpus["oracle_sha256"] = digest(ROOT / CONFIGURATION_ORACLES)
    corpus["result"] = "fail"
    directory = OUTPUT / "cor03"
    directory.mkdir(parents=True, exist_ok=True)
    for case in specimens:
        identifier = case["id"]
        pdf = directory / (identifier + ".pdf")
        structure = pdf.with_suffix(".qpdf.json")
        assertions_path = pdf.with_suffix(".oracle.json")
        entry = {
            "id": identifier, "fixture": case["fixture"], "inputs": case["inputs"],
            "expected_error": case["expected_error"], "result": "fail",
            "commands": [], "errors": [], "color_streams": [],
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "cor03"):
                raise VerificationError("COR-03 fixture escapes the controlled fixture directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(
                json.dumps(case["inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for artifact in (pdf, pdf.with_suffix(".txt"), structure, assertions_path):
                artifact.unlink(missing_ok=True)
            for artifact in directory.glob(identifier + "-stream*.txt"):
                artifact.unlink()
            options = ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"]]
            for key, value in sorted(case["inputs"].items()):
                options.extend(["--input", f"{key}={value}"])
            if case["expected_error"] is not None:
                diagnostics = run(
                    ["typst", "compile", "--root", ".", *options, case["fixture"], str(pdf)],
                    f"cor03/{identifier}-compile.log", entry["commands"],
                    combined=True, expected_exit=1,
                )
                command = entry["commands"][-1]
                assertions = oracle["check_rejection"](
                    case, diagnostics, exit_code=command["exit_code"],
                    timed_out=command["timed_out"], pdf_exists=pdf.exists(),
                )
            else:
                details, extracted = verify_pdf(
                    case["fixture"], pdf, "cor03/" + identifier, entry["commands"], options,
                )
                entry.update(details)
                streams = []
                page_number = oracle["color_page"](case, extracted)
                if page_number is not None:
                    native = run(
                        ["qpdf", "--json", str(pdf)], f"cor03/{identifier}-qpdf-json.log", entry["commands"],
                    )
                    structure.write_text(native, encoding="utf-8")
                    pages = json.loads(native)["pages"]
                    if len(pages) != details["pages"] or not 1 <= page_number <= len(pages):
                        raise VerificationError("COR-03 colour page is outside the PDF page inventory")
                    references = pages[page_number - 1]["contents"]
                    if not references:
                        raise VerificationError("COR-03 colour page has no content stream")
                    for reference in references:
                        if not isinstance(reference, str) or not re.fullmatch(r"[1-9][0-9]* 0 R", reference):
                            raise VerificationError("COR-03 colour stream reference is malformed")
                        object_id = reference.split()[0]
                        name = f"{identifier}-stream{object_id}"
                        stream = run(
                            ["qpdf", "--show-object=" + object_id, "--filtered-stream-data", str(pdf)],
                            "cor03/" + name + ".log", entry["commands"],
                        )
                        path = directory / (name + ".txt")
                        path.write_text(stream, encoding="utf-8")
                        entry["color_streams"].append({
                            "physical_page": page_number, "reference": reference,
                            "path": str(path.relative_to(ROOT)), "sha256": digest(path),
                        })
                        streams.append(stream)
                assertions = oracle["check_text"](
                    case, extracted, details["pages"], color_streams=streams,
                )
            assertions_path.write_text(
                json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            checks = assertions.get("checks", [])
            if not checks or not all(check.get("passed") is True for check in checks):
                if not entry["errors"]:
                    entry["errors"].append("COR-03 oracle has missing or failed assertions")
            if assertions.get("passed") is not True and not entry["errors"]:
                entry["errors"].append("COR-03 oracle did not explicitly pass")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        for artifact, key in (
            (pdf, "pdf"), (pdf.with_suffix(".txt"), "text"),
            (structure, "pdf_structure"), (assertions_path, "oracle_report"),
        ):
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    if corpus["passed_count"] != expected_count:
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("COR-03 configuration checks failed: " + ", ".join(failures))
    corpus["result"] = "pass"


def verify_cor04(report, oracle):
    """Project managed identity and retain real failures for residual controls."""
    specimens = oracle["specimens"]()
    expected_ids = (
        "structured-identified", "structured-blind", "authored-identified", "authored-blind",
        "custom-identified", "custom-blind", "authored-reviewed-blind", "index-identified",
        "index-blind", "blind-string-rejected",
    )
    if oracle["EXPECTED_SPECIMEN_COUNT"] != 10 or tuple(case["id"] for case in specimens) != expected_ids:
        raise VerificationError("The bounded COR-04 corpus must contain all ten specimens")
    if sum(case["expected_error"] is not None for case in specimens) != 1:
        raise VerificationError("COR-04 requires one strict boolean rejection")
    if sum(case["identity"] == "blind" and case["expected_scan_pass"] is False for case in specimens) != 3:
        raise VerificationError("COR-04 requires three explicit residual-identity failures")
    corpus = report["blind_corpus"]
    corpus.update({
        "expected_specimen_count": 10, "creation_timestamp": oracle["CREATION_TIMESTAMP"],
        "source_sha256": {source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]},
        "resource_sha256": {source: digest(ROOT / source) for source in oracle["RESOURCE_FILES"]},
        "oracle_sha256": digest(ROOT / BLIND_ORACLES), "result": "fail",
        "reviewer_ready_certified": False,
        "evidence_boundary": "Internal synthetic provenance; this report is not a reviewer-safe manifest",
    })
    directory = OUTPUT / "cor04"
    directory.mkdir(parents=True, exist_ok=True)
    for case in specimens:
        identifier = case["id"]
        pdf = directory / (identifier + ".pdf")
        structure = pdf.with_suffix(".qpdf.json")
        xmp = pdf.with_suffix(".xmp.xml")
        diagnostics_path = pdf.with_suffix(".diagnostics.json")
        dependencies = pdf.with_suffix(".dependencies.json")
        assertions_path = pdf.with_suffix(".oracle.json")
        artifacts = (
            (pdf, "pdf"), (pdf.with_suffix(".txt"), "text"), (structure, "pdf_structure"),
            (xmp, "xmp"), (diagnostics_path, "review_diagnostics"),
            (dependencies, "dependencies"), (assertions_path, "oracle_report"),
        )
        entry = {
            "id": identifier, "fixture": case["fixture"], "inputs": case["inputs"],
            "identity": case["identity"], "expected_error": case["expected_error"],
            "expected_scan_pass": case["expected_scan_pass"], "result": "fail",
            "commands": [], "errors": [], "reviewer_ready_certified": False,
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "cor04"):
                raise VerificationError("COR-04 fixture escapes the controlled fixture directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(
                json.dumps(case["inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for artifact, _key in artifacts:
                artifact.unlink(missing_ok=True)
            inputs = []
            for key, value in sorted(case["inputs"].items()):
                inputs.extend(["--input", f"{key}={value}"])
            options = ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"], *inputs]
            if case["expected_error"] is not None:
                diagnostics = run(
                    ["typst", "compile", "--root", ".", *options, case["fixture"], str(pdf)],
                    f"cor04/{identifier}-compile.log", entry["commands"], combined=True, expected_exit=1,
                )
                command = entry["commands"][-1]
                assertions = oracle["check_rejection"](
                    case, diagnostics, exit_code=command["exit_code"],
                    timed_out=command["timed_out"], pdf_exists=pdf.exists(),
                )
            else:
                details, extracted = verify_pdf(
                    case["fixture"], pdf, "cor04/" + identifier, entry["commands"],
                    [*options, "--deps", str(dependencies), "--deps-format", "json"],
                )
                entry.update(details)
                native = run(
                    ["qpdf", "--json", str(pdf)], f"cor04/{identifier}-qpdf-json.log", entry["commands"],
                )
                structure.write_text(native, encoding="utf-8")
                metadata = run(
                    ["pdfinfo", "-meta", str(pdf)], f"cor04/{identifier}-xmp.log", entry["commands"],
                )
                xmp.write_text(metadata, encoding="utf-8")
                query = run(
                    ["typst", "query", "--root", ".", "--ignore-system-fonts", *inputs,
                     case["fixture"], "<blind-review-diagnostics>", "--field", "value"],
                    f"cor04/{identifier}-review-diagnostics.log", entry["commands"],
                )
                diagnostics_path.write_text(query, encoding="utf-8")
                entry["dependency_inventory"] = capture_dependencies(dependencies, details, entry["commands"])
                assertions = oracle["analyze"](
                    case, json.loads(native), extracted, metadata, json.loads(query), details["pages"],
                )
                # Preserve the scanner's actual result. Expected residual PDFs
                # remain failed scans even when the regression assertion passes.
                entry["public_surface_scan"] = assertions["public_surface_scan"]
                entry["author_review_required"] = assertions["author_review_required"]
            assertions_path.write_text(
                json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            checks = assertions.get("checks", [])
            if not checks or not all(check.get("passed") is True for check in checks):
                if not entry["errors"]:
                    entry["errors"].append("COR-04 oracle has missing or failed assertions")
            if assertions.get("passed") is not True and not entry["errors"]:
                entry["errors"].append("COR-04 oracle did not explicitly pass")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        for artifact, key in artifacts:
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
        write_report(report)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    corpus["clean_blind_pdf_count"] = sum(
        case["identity"] == "blind" and case.get("public_surface_scan", {}).get("passed") is True
        for case in corpus["specimens"]
    )
    corpus["residual_blind_pdf_count"] = sum(
        case["identity"] == "blind" and case.get("public_surface_scan", {}).get("passed") is False
        for case in corpus["specimens"]
    )
    if corpus["passed_count"] != 10:
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("COR-04 identity regression checks failed: " + ", ".join(failures))
    if corpus["clean_blind_pdf_count"] != 2 or corpus["residual_blind_pdf_count"] != 3:
        raise VerificationError("COR-04 did not retain both clean controls and actual residual failures")
    corpus["result"] = "pass"


def verify_terms(report, oracle, pdf_helpers):
    """Check actual term values/references and explicit unsupported-input errors."""
    specimens = oracle["specimens"]()
    expected_ids = (
        "abbreviations-table", "abbreviations-first-use", "glossary-first-use",
        "glossary-marked", "glossary-automatic", "glossary-extract", "glossary-index",
        "index-marked", "index-columns", "index-manual", "index-subentries", "index-alias",
        "pages-abbreviations", "pages-combined", "edge-cases-roman", "edge-cases-empty-index",
        "edge-cases-category", "edge-cases-hidden-pages", "edge-cases-zero-page",
        "edge-cases-reversed-range", "edge-cases-invalid-page", "edge-cases-empty-term",
        "edge-cases-automatic-index", "edge-cases-conflicting-definition", "thesis-index-supplied",
    )
    if oracle["EXPECTED_SPECIMEN_COUNT"] != 25 or tuple(case["id"] for case in specimens) != expected_ids:
        raise VerificationError("The bounded terms corpus must contain all 25 expected specimens")
    if sum(case["expected_error"] is not None for case in specimens) != 8:
        raise VerificationError("The bounded terms corpus requires eight intentional rejections")
    corpus = report["terms_corpus"]
    corpus.update({
        "expected_specimen_count": 25, "expected_document_count": 17, "expected_rejection_count": 8,
        "creation_timestamp": oracle["CREATION_TIMESTAMP"],
        "source_sha256": {source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]},
        "oracle_sha256": digest(ROOT / TERMS_ORACLES),
        "native_parser_sha256": digest(ROOT / NAVIGATION_ORACLES), "result": "fail",
    })
    directory = OUTPUT / "terms"
    directory.mkdir(parents=True, exist_ok=True)
    for case in specimens:
        identifier = case["id"]
        pdf = directory / (identifier + ".pdf")
        structure = pdf.with_suffix(".qpdf.json")
        boxes = pdf.with_suffix(".bbox.html")
        assertions_path = pdf.with_suffix(".oracle.json")
        entry = {
            "id": identifier, "fixture": case["fixture"], "inputs": case["inputs"],
            "expected_error": case["expected_error"], "result": "fail",
            "expected_outcome": "rejection" if case["expected_error"] is not None else "rendered_output",
            "document_result": "unexecuted", "commands": [], "errors": [],
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "terms"):
                raise VerificationError("Terms fixture escapes the controlled fixture directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(
                json.dumps(case["inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for artifact in (pdf, pdf.with_suffix(".txt"), structure, boxes, assertions_path):
                artifact.unlink(missing_ok=True)
            options = ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"]]
            for key, value in sorted(case["inputs"].items()):
                options.extend(["--input", f"{key}={value}"])
            if case["expected_error"] is not None:
                diagnostics = run(
                    ["typst", "compile", "--root", ".", *options, case["fixture"], str(pdf)],
                    f"terms/{identifier}-compile.log", entry["commands"], combined=True, expected_exit=1,
                )
                command = entry["commands"][-1]
                assertions = oracle["check_rejection"](
                    case, diagnostics, exit_code=command["exit_code"],
                    timed_out=command["timed_out"], pdf_exists=pdf.exists(),
                )
            else:
                details, extracted = verify_pdf(
                    case["fixture"], pdf, "terms/" + identifier, entry["commands"], options,
                )
                entry.update(details)
                native = run(
                    ["qpdf", "--json", str(pdf)], f"terms/{identifier}-qpdf-json.log", entry["commands"],
                )
                structure.write_text(native, encoding="utf-8")
                bounding_boxes = None
                if case["needs_boxes"]:
                    bounding_boxes = run(
                        ["pdftotext", "-bbox-layout", str(pdf), "-"],
                        f"terms/{identifier}-bbox.log", entry["commands"],
                    )
                    boxes.write_text(bounding_boxes, encoding="utf-8")
                assertions = oracle["analyze"](
                    case, extracted, details["pages"], json.loads(native), bounding_boxes, pdf_helpers,
                )
            assertions_path.write_text(
                json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8",
            )
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            checks = assertions.get("checks", [])
            if not checks or not all(check.get("passed") is True for check in checks):
                if not entry["errors"]:
                    entry["errors"].append("Terms oracle has missing or failed assertions")
            if assertions.get("passed") is not True and not entry["errors"]:
                entry["errors"].append("Terms oracle did not explicitly pass")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        if entry["result"] == "pass":
            entry["document_result"] = "rejected" if case["expected_error"] is not None else "validated"
        else:
            entry["document_result"] = "failed"
        for artifact, key in (
            (pdf, "pdf"), (pdf.with_suffix(".txt"), "text"), (structure, "pdf_structure"),
            (boxes, "bounding_boxes"), (assertions_path, "oracle_report"),
        ):
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    corpus["validated_document_count"] = sum(case["document_result"] == "validated" for case in corpus["specimens"])
    corpus["rejected_input_count"] = sum(case["document_result"] == "rejected" for case in corpus["specimens"])
    if (corpus["passed_count"], corpus["validated_document_count"], corpus["rejected_input_count"]) != (25, 17, 8):
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("Terms checks failed: " + ", ".join(failures))
    corpus["result"] = "pass"


def verify_cor05(report, oracle):
    """Verify public optional sections, typed rejections and authored residuals."""
    specimens = oracle["specimens"]()
    identifiers = [case["id"] for case in specimens]
    if oracle["EXPECTED_SPECIMEN_COUNT"] != 47 or len(specimens) != 47:
        raise VerificationError("The bounded COR-05 corpus must contain all 47 specimens")
    if len(set(identifiers)) != 47 or any(not re.fullmatch(r"[a-z0-9-]+", name) for name in identifiers):
        raise VerificationError("COR-05 specimen identities are invalid or duplicated")
    if sum(case["expected_error"] is not None for case in specimens) != 26:
        raise VerificationError("COR-05 requires 26 typed or private-log rejections")
    corpus = report["optional_corpus"]
    corpus.update({
        "expected_specimen_count": 47, "creation_timestamp": oracle["CREATION_TIMESTAMP"],
        "source_sha256": {source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]},
        "sample_sha256": {source: digest(ROOT / source) for source in oracle["SAMPLE_FILES"]},
        "oracle_sha256": digest(ROOT / OPTIONAL_ORACLES), "result": "fail",
        "policy_or_approval_certified": False, "reviewer_ready_certified": False,
    })
    directory = OUTPUT / "cor05"
    directory.mkdir(parents=True, exist_ok=True)
    samples = {ROOT / name for name in oracle["SAMPLE_FILES"]}
    for case in specimens:
        identifier = case["id"]
        pdf = directory / (identifier + ".pdf")
        structure = pdf.with_suffix(".qpdf.json")
        xmp = pdf.with_suffix(".xmp.xml")
        diagnostics_path = pdf.with_suffix(".diagnostics.json")
        dependencies = pdf.with_suffix(".dependencies.json")
        assertions_path = pdf.with_suffix(".oracle.json")
        artifacts = (
            (pdf, "pdf"), (pdf.with_suffix(".txt"), "text"), (structure, "pdf_structure"),
            (xmp, "xmp"), (diagnostics_path, "review_diagnostics"),
            (dependencies, "dependencies"), (assertions_path, "oracle_report"),
        )
        entry = {
            "id": identifier, "fixture": case["fixture"], "inputs": case["inputs"],
            "expected_error": case["expected_error"], "result": "fail", "commands": [], "errors": [],
            "expected_outcome": "rejection" if case["expected_error"] is not None else "rendered_output",
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if fixture.is_symlink() or not (
                fixture.resolve().is_relative_to(ROOT / "tests/rendered/cor05")
                or fixture in samples and fixture.resolve() == fixture
            ):
                raise VerificationError("COR-05 fixture is outside the controlled corpus or explicit sample allowlist")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(
                json.dumps(case["inputs"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for artifact, _key in artifacts:
                artifact.unlink(missing_ok=True)
            inputs = []
            for key, value in sorted(case["inputs"].items()):
                inputs.extend(["--input", f"{key}={value}"])
            options = ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"], *inputs]
            if case["expected_error"] is not None:
                diagnostics = run(
                    ["typst", "compile", "--root", ".", *options, case["fixture"], str(pdf)],
                    f"cor05/{identifier}-compile.log", entry["commands"], combined=True, expected_exit=1,
                )
                command = entry["commands"][-1]
                assertions = oracle["check_rejection"](
                    case, diagnostics, exit_code=command["exit_code"], timed_out=command["timed_out"],
                    pdf_exists=pdf.exists(),
                )
            else:
                details, extracted = verify_pdf(
                    case["fixture"], pdf, "cor05/" + identifier, entry["commands"],
                    [*options, "--deps", str(dependencies), "--deps-format", "json"],
                )
                entry.update(details)
                native = run(
                    ["qpdf", "--json", str(pdf)], f"cor05/{identifier}-qpdf-json.log", entry["commands"],
                )
                structure.write_text(native, encoding="utf-8")
                metadata = run(
                    ["pdfinfo", "-meta", str(pdf)], f"cor05/{identifier}-xmp.log", entry["commands"],
                )
                xmp.write_text(metadata, encoding="utf-8")
                query = run(
                    ["typst", "query", "--root", ".", "--ignore-system-fonts", *inputs,
                     case["fixture"], "<blind-review-diagnostics>", "--field", "value"],
                    f"cor05/{identifier}-review-diagnostics.log", entry["commands"],
                )
                diagnostics_path.write_text(query, encoding="utf-8")
                entry["dependency_inventory"] = capture_dependencies(dependencies, details, entry["commands"])
                assertions = oracle["analyze"](
                    case, json.loads(native), extracted, metadata, json.loads(query), details["pages"],
                )
                entry["public_surface_scan"] = assertions["public_surface_scan"]
            assertions_path.write_text(json.dumps(assertions, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            entry["assertions"] = assertions
            entry["errors"].extend(assertions["errors"])
            checks = assertions.get("checks", [])
            if not checks or not all(check.get("passed") is True for check in checks):
                if not entry["errors"]:
                    entry["errors"].append("COR-05 oracle has missing or failed assertions")
            if assertions.get("passed") is not True and not entry["errors"]:
                entry["errors"].append("COR-05 oracle did not explicitly pass")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        for artifact, key in artifacts:
            if artifact.is_file():
                entry[key] = str(artifact.relative_to(ROOT))
                entry[key + "_sha256"] = digest(artifact)
        write_report(report)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    corpus["rendered_pdf_count"] = sum("pdf_sha256" in case for case in corpus["specimens"])
    corpus["clean_blind_pdf_count"] = sum(
        case["id"].startswith("blind-") and (case.get("public_surface_scan") or {}).get("passed") is True
        for case in corpus["specimens"]
    )
    corpus["residual_blind_pdf_count"] = sum(
        case["id"].startswith("blind-") and (case.get("public_surface_scan") or {}).get("passed") is False
        for case in corpus["specimens"]
    )
    if corpus["passed_count"] != 47:
        failures = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("COR-05 optional-section checks failed: " + ", ".join(failures))
    if (corpus["rendered_pdf_count"], corpus["clean_blind_pdf_count"], corpus["residual_blind_pdf_count"]) != (21, 1, 1):
        raise VerificationError("COR-05 did not retain the rendered corpus and real authored residual failure")
    corpus["result"] = "pass"


def write_report(report):
    (OUTPUT / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )


def verify_images(report, oracle):
    """Check original image encoding and pixels across the four template profiles."""
    cases = oracle["specimens"]()
    expected_ids = [
        f"{profile}-{resource}" for profile in ("default", "draft", "screen", "print")
        for resource in ("png", "jpg", "svg", "native", "bytes")
    ]
    if oracle["EXPECTED_SPECIMEN_COUNT"] != 20 or [case["id"] for case in cases] != expected_ids:
        raise VerificationError("The image corpus must contain all 20 declared specimens")
    corpus = report["image_corpus"]
    corpus.update({
        "result": "fail", "expected_specimen_count": 20,
        "creation_timestamp": oracle["CREATION_TIMESTAMP"],
        "oracle_sha256": digest(ROOT / IMAGE_ORACLES),
        "source_sha256": {source: digest(ROOT / source) for source in oracle["SOURCE_FILES"]},
        "asset_sha256": {source: digest(ROOT / source) for source in oracle["ASSETS"]},
    })
    for case in cases:
        identifier = case["id"]
        pdf = OUTPUT / "images" / (identifier + ".pdf")
        native_path = pdf.with_suffix(".qpdf.json")
        oracle_path = pdf.with_suffix(".oracle.json")
        entry = {
            "id": identifier, "fixture": oracle["FIXTURE"],
            "inputs": {"profile": case["profile"], "resource": case["resource"]},
            "result": "fail", "commands": [], "errors": [],
        }
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / oracle["FIXTURE"]
            if not fixture.resolve().is_relative_to(ROOT / "tests" / "rendered" / "images"):
                raise VerificationError("Image fixture escapes its controlled directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(json.dumps(
                entry["inputs"], sort_keys=True, separators=(",", ":"),
            ).encode()).hexdigest()
            for artifact in (native_path, oracle_path):
                artifact.unlink(missing_ok=True)
            details, extracted = verify_pdf(
                oracle["FIXTURE"], pdf, "images/" + identifier, entry["commands"],
                ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"],
                 "--input", "profile=" + case["profile"], "--input", "resource=" + case["resource"]],
            )
            entry.update(details)
            native = run(
                ["qpdf", "--json", "--json-stream-data=inline", str(pdf)],
                "images/" + identifier + "-native.log", entry["commands"],
            )
            native_path.write_text(native, encoding="utf-8")
            assertions = oracle["check_native"](case, extracted, details["pages"], json.loads(native))
            expected_checks = 8 if case["resource"] == "svg" else 9
            checks = assertions["checks"]
            if (len(checks) != expected_checks
                    or any(type(check["passed"]) is not bool for check in checks)
                    or not isinstance(assertions["errors"], list)):
                raise VerificationError("Image oracle omitted or malformed required evidence")
            entry["errors"].extend(assertions["errors"])
            if any(not check["passed"] for check in checks) and not entry["errors"]:
                raise VerificationError("Image oracle contradicted its failed assertions")
            entry["check_count"] = len(checks)
            oracle_path.write_text(json.dumps(assertions, indent=2) + "\n", encoding="utf-8")
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        for artifact, name in ((pdf, "pdf"), (pdf.with_suffix(".txt"), "text"),
                               (native_path, "native_json"), (oracle_path, "oracle_report")):
            if artifact.is_file():
                entry[name] = str(artifact.relative_to(ROOT))
                entry[name + "_sha256"] = digest(artifact)
    corpus["passed_count"] = sum(case["result"] == "pass" for case in corpus["specimens"])
    if corpus["passed_count"] != 20:
        failed = [case["id"] for case in corpus["specimens"] if case["result"] != "pass"]
        raise VerificationError("Image checks failed: " + ", ".join(failed))
    corpus["result"] = "pass"


def verify_layout_order(report, oracle, navigation_oracle):
    """Verify physical output order, logical labels and measured page geometry."""
    cases = oracle["specimens"]()
    expected_ids = ["default", "draft", "screen", "print", "default-double",
                    "print-single", "no-bibliography", "custom-title", "direct-appendix"]
    if oracle["EXPECTED_SPECIMEN_COUNT"] != 9 or [c["id"] for c in cases] != expected_ids:
        raise VerificationError("The layout-order corpus requires all nine declared cases")
    corpus = report["layout_order_corpus"]
    corpus.update({
        "result": "fail", "expected_specimen_count": 9,
        "creation_timestamp": oracle["CREATION_TIMESTAMP"],
        "oracle_sha256": digest(ROOT / LAYOUT_ORDER_ORACLES),
        "native_parser_sha256": digest(ROOT / NAVIGATION_ORACLES),
        "source_sha256": {p: digest(ROOT / p) for p in oracle["SOURCE_FILES"]},
        "resource_sha256": {p: digest(ROOT / p) for p in oracle["RESOURCE_FILES"]},
    })
    for case in cases:
        identifier = case["id"]
        pdf = OUTPUT / "layout-order" / (identifier + ".pdf")
        native_path = pdf.with_suffix(".qpdf.json")
        bbox_path = pdf.with_suffix(".bbox.html")
        oracle_path = pdf.with_suffix(".oracle.json")
        entry = {"id": identifier, "fixture": case["fixture"],
                 "inputs": {"profile": case["profile"], "layout-case": case["case"]},
                 "result": "fail", "commands": [], "errors": []}
        corpus["specimens"].append(entry)
        try:
            fixture = ROOT / case["fixture"]
            if not fixture.resolve().is_relative_to(ROOT / "tests/rendered/layout-order"):
                raise VerificationError("Layout fixture escapes its controlled directory")
            entry["fixture_sha256"] = digest(fixture)
            entry["inputs_sha256"] = hashlib.sha256(json.dumps(
                entry["inputs"], sort_keys=True, separators=(",", ":"),
            ).encode()).hexdigest()
            for path in (native_path, bbox_path, oracle_path):
                path.unlink(missing_ok=True)
            details, extracted = verify_pdf(
                case["fixture"], pdf, "layout-order/" + identifier, entry["commands"],
                ["--ignore-system-fonts", "--creation-timestamp", oracle["CREATION_TIMESTAMP"],
                 "--input", "profile=" + case["profile"], "--input", "layout-case=" + case["case"]],
            )
            entry.update(details)
            native = run(["qpdf", "--json", str(pdf)],
                         "layout-order/" + identifier + "-native.log", entry["commands"])
            native_path.write_text(native, encoding="utf-8")
            bbox = run(["pdftotext", "-bbox-layout", str(pdf), "-"],
                       "layout-order/" + identifier + "-bbox.log", entry["commands"])
            bbox_path.write_text(bbox, encoding="utf-8")
            assertions = oracle["check_native"](
                case, extracted, details["pages"], navigation_oracle["PDF"](json.loads(native)),
                bbox, navigation_oracle["roman"],
            )
            expected_count = {"no-bibliography": 21, "custom-title": 7, "direct-appendix": 6}.get(identifier, 25)
            checks = assertions["checks"]
            if (len(checks) != expected_count or not isinstance(assertions["errors"], list)
                    or any(type(check["passed"]) is not bool for check in checks)):
                raise VerificationError("Layout oracle omitted or malformed required assertions")
            entry["errors"].extend(assertions["errors"])
            if any(not check["passed"] for check in checks) and not entry["errors"]:
                raise VerificationError("Layout oracle contradicts its failed assertions")
            oracle_path.write_text(json.dumps(assertions, indent=2) + "\n", encoding="utf-8")
            entry["check_count"] = len(checks)
            entry["result"] = "fail" if entry["errors"] else "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        for path, name in ((pdf, "pdf"), (pdf.with_suffix(".txt"), "text"),
                           (native_path, "native_json"), (bbox_path, "bbox"), (oracle_path, "oracle_report")):
            if path.is_file():
                entry[name] = str(path.relative_to(ROOT))
                entry[name + "_sha256"] = digest(path)
    corpus["passed_count"] = sum(x["result"] == "pass" for x in corpus["specimens"])
    if corpus["passed_count"] != 9:
        failed = [x["id"] for x in corpus["specimens"] if x["result"] != "pass"]
        raise VerificationError("Layout/order checks failed: " + ", ".join(failed))
    corpus["result"] = "pass"


def native_package_roots():
    """Declare package roots, keeping host paths out of normalized inventories."""
    roots = {}
    for label, override, xdg, fallback in (
        ("package-cache", "TYPST_PACKAGE_CACHE_PATH", "XDG_CACHE_HOME", ".cache"),
        ("package-local", "TYPST_PACKAGE_PATH", "XDG_DATA_HOME", ".local/share"),
    ):
        if os.environ.get(override):
            directory = Path(os.environ[override])
            roots[label] = (directory if directory.is_absolute() else ROOT / directory).resolve()
        elif sys.platform.startswith("linux"):
            configured = Path(os.environ.get(xdg, "."))
            directory = configured if configured.is_absolute() else Path.home() / fallback
            roots[label] = directory / "typst" / "packages"
    return roots


def capture_dependencies(path, details, commands, *, required_inputs=()):
    """Validate fresh native bytes, then retain a clearly labeled public inventory."""
    api = runpy.run_path(str(ROOT / NATIVE_EVIDENCE), run_name="scripts.native_evidence")
    if not path.is_file():
        raise VerificationError("Compile produced no native dependency file")
    raw = path.read_bytes()
    try:
        inventory = api["validate_dependencies"](
            raw.decode("utf-8"), root=ROOT, details=details, commands=commands,
            approved_external_roots=native_package_roots(), required_inputs=required_inputs,
        )
    except Exception as exc:
        # Do not publish unapproved external paths even when validation rejects them.
        rejected = {
            "schema_version": 1, "artifact_kind": "rejected-native-dependency-inventory",
            "native_report_sha256": hashlib.sha256(raw).hexdigest(), "native_report_bytes": len(raw),
            "rejection_code": getattr(exc, "code", "invalid-native-capture"),
            "raw_native_paths_retained": False, "successful_compile_inventory": False,
        }
        path.write_text(json.dumps(rejected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        raise
    # The exact native byte digest remains bound, but external machine paths do not.
    path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "artifact_kind": inventory["artifact_kind"], "native_report_sha256": inventory["native_report_sha256"],
        "path": str(path.relative_to(ROOT)), "sha256": digest(path),
        "input_count": len(inventory["inputs"]), "output_count": len(inventory["outputs"]),
        "external_paths_sanitized": True, "native_report_retained_verbatim": False,
        "font_inventory_included": False, "replay_qualified": False,
    }


def native_tool_inventory(commands):
    """Record exact executables; their shared libraries/environment are not locked."""
    from importlib.metadata import version as package_version

    tools = {}
    for name, arguments in (
        ("typst", ["typst", "--version"]), ("qpdf", ["qpdf", "--version"]),
        ("pdfinfo", ["pdfinfo", "-v"]), ("pdftotext", ["pdftotext", "-v"]),
        ("pdffonts", ["pdffonts", "-v"]),
    ):
        executable = shutil.which(name)
        if executable is None:
            raise VerificationError(f"Required native-evidence executable not found: {name}")
        value = run(arguments, f"native/{name}-version.log", commands, combined=True).strip()
        if not value:
            raise VerificationError(f"Native-evidence tool returned no version: {name}")
        tools[name] = {"version": value.splitlines()[0], "executable_sha256": digest(Path(executable))}
    with (ROOT / "typst.toml").open("rb") as source:
        version = tomllib.load(source)["tool"]["typst"]["version"]
    if tools["typst"]["version"].split()[:2] != ["typst", version]:
        raise VerificationError("Native evidence requires the compiler pinned by typst.toml")
    return {
        "schema_version": 1, "artifact_kind": "native-evidence-supplement",
        "compiler_manifest_sha256": digest(ROOT / "typst.toml"), "tools": tools,
        "python": {"version": sys.version.split()[0], "executable_sha256": digest(Path(sys.executable))},
        "schema_validator": {"name": "jsonschema", "version": package_version("jsonschema")},
        "packages": {"observed": [], "scope": "Only files emitted by the native dependency inventory; no package archive lock"},
        "fonts": {
            "requested_family": "Libertinus Serif", "system_fonts_disabled": True,
            "explicit_font_paths_environment_present": bool(os.environ.get("TYPST_FONT_PATHS")),
            "embedded_fonts_disabled_environment_present": bool(os.environ.get("TYPST_IGNORE_EMBEDDED_FONTS")),
            "native_dependency_inventory_includes_fonts": False, "source_file_digests": [],
            "scope": "PDF font names and embedding only; per-face source bytes are not qualified",
        },
        "replay_qualified": False,
        "uncollected": ["Per-face font source files", "Shared libraries", "Complete environment and package archives"],
    }


def verify_native_evidence(report):
    """Exercise fixed native eval expressions and successful/failed compile inventories."""
    api = runpy.run_path(str(ROOT / NATIVE_EVIDENCE), run_name="scripts.native_evidence")
    oracle = runpy.run_path(str(ROOT / NATIVE_ORACLES))
    directory = OUTPUT / "native"
    directory.mkdir(parents=True, exist_ok=True)
    # A focused invocation has the same stale-output protection as main().
    for path in directory.iterdir():
        if path.suffix in {".pdf", ".txt", ".log", ".json"} and (path.is_file() or path.is_symlink()):
            path.unlink()
    source = "tests/rendered/native/document.typ"
    source_files = (source, "tests/rendered/native/part.typ", "tests/rendered/native/data.json",
                    "tests/rendered/native/bad.typ", "tests/rendered/native/eval-results.schema.json",
                    NATIVE_EVIDENCE, NATIVE_ORACLES, "typst.toml", "scripts/verify.py")
    corpus = report.setdefault("native_evidence_corpus", {})
    corpus.update({
        "requirements": ["TYP-04", "TST-03"], "result": "fail", "expected_specimen_count": 16,
        "scope": "Fixed-expression synthetic semantics and source/output-bound inventories; not full replay or thesis acceptance",
        "specimens": [], "commands": [], "replay_qualified": False,
        "source_sha256_before": {name: digest(ROOT / name) for name in source_files},
    })
    write_report(report)
    supplement = native_tool_inventory(corpus["commands"])
    options = ["--ignore-system-fonts", "--creation-timestamp", "1794700800"]
    cases = oracle["specimens"]()
    expected_ids = (
        "assertion", "metadata", "headings", "references", "optional", "required-false", "required-null",
        "required-empty-string", "required-empty-array", "required-empty-object", "missing-metadata",
        "duplicate-metadata", "malformed-metadata",
    )
    if tuple(case["id"] for case in cases) != expected_ids:
        raise VerificationError("Native semantic corpus must retain all 13 declared value cases")
    cases = [{"id": "successful-compile"}, *cases, {"id": "failed-assertion"}, {"id": "failed-compile"}]
    for case in cases:
        identifier = case["id"]
        entry = {"id": identifier, "result": "fail", "commands": [], "errors": []}
        corpus["specimens"].append(entry)
        try:
            if identifier == "successful-compile":
                pdf = directory / "document.pdf"
                deps = directory / "document.dependencies.json"
                details, extracted = verify_pdf(
                    source, pdf, "native/document", entry["commands"],
                    [*options, "--deps", str(deps), "--deps-format", "json"],
                )
                entry.update(details)
                entry["dependency_inventory"] = capture_dependencies(
                    deps, details, entry["commands"], required_inputs=source_files[:3],
                )
                inventory = json.loads(deps.read_text(encoding="utf-8"))
                font_text = run(["pdffonts", str(pdf)], "native/document-fonts.log", entry["commands"])
                fonts = []
                for line in font_text.splitlines():
                    match = re.fullmatch(r"(\S+)\s+.*?\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*", line)
                    if match:
                        fonts.append(dict(zip(("name", "embedded", "subset", "unicode_map"), match.groups())))
                supplement["fonts"]["pdf_fonts"] = fonts
                flattened = " ".join(extracted.split())
                checks = [
                    {"name": "One real PDF page", "passed": details["pages"] == 1},
                    {"name": "Exact heading/body/reference", "passed": "1 NATIVE SEMANTIC CHAPTER NATIVE BODY SENTINEL. See Section 1." in flattened},
                    {"name": "Metadata remains literal data", "passed": flattened.count("#panic(123)") == 1},
                    {"name": "All three native inputs", "passed": {item["path"] for item in inventory["inputs"]} == {"project:" + name for name in source_files[:3]}},
                    {"name": "Observed embedded PDF fonts", "passed": bool(fonts) and all(item["embedded"] == "yes" for item in fonts)},
                    {"name": "Declared fixture font family", "passed": bool(fonts) and all("LibertinusSerif" in item["name"] for item in fonts)},
                ]
                entry["evidence_status"] = "validated-output"
            elif identifier == "failed-compile":
                bad_source = "tests/rendered/native/bad.typ"
                pdf = directory / "failed.pdf"
                deps = directory / "failed.dependencies.json"
                diagnostics = run(
                    ["typst", "compile", "--root", ".", *options, "--deps", str(deps),
                     "--deps-format", "json", bad_source, str(pdf)],
                    "native/failed-compile.log", entry["commands"], combined=True, expected_exit=1,
                )
                raw = deps.read_bytes().decode("utf-8")
                native = api["strict_json"](raw)
                code = None
                try:
                    api["validate_dependencies"](raw, root=ROOT, details={}, commands=entry["commands"])
                except api["EvidenceError"] as exc:
                    code = exc.code
                checks = [
                    {"name": "Intended native compile failure", "passed": re.findall(r"^error:.*$", diagnostics, re.MULTILINE) == ["error: panicked with: NATIVE INTENTIONAL COMPILER FAILURE"]},
                    {"name": "No failed PDF", "passed": not pdf.exists()},
                    {"name": "Actual native null output", "passed": native == {"inputs": [bad_source], "outputs": None}},
                    {"name": "Failed compile cannot qualify inventory", "passed": code == "compile-not-successful"},
                ]
                entry.update({"evidence_status": "rejected", "rejection_code": code,
                              "native_failure_report": str(deps.relative_to(ROOT)),
                              "native_failure_report_sha256": digest(deps), "native_outputs": None})
            elif identifier == "failed-assertion":
                expression = oracle["EXPRESSIONS"]["failed_assertion"]
                diagnostics = run(
                    ["typst", "eval", "--root", ".", *options, "--format", "json", "--in", source, expression],
                    "native/failed-assertion.log", entry["commands"], combined=True, expected_exit=1,
                )
                checks = [{"name": "Native failed assertion exits unsuccessfully", "passed": re.findall(r"^error:.*$", diagnostics, re.MULTILINE) == ["error: assertion failed: NATIVE REQUIRED ASSERTION FAILED"]}]
                entry["evidence_status"] = "rejected"
                entry["expression_sha256"] = hashlib.sha256(expression.encode("utf-8")).hexdigest()
            else:
                expression = oracle["EXPRESSIONS"][case["expression"]]
                raw = run(
                    ["typst", "eval", "--root", ".", *options, "--format", "json", "--in", source,
                     "--input", "native_mode=" + case["mode"], expression],
                    f"native/{identifier}-eval.log", entry["commands"],
                )
                result_path = directory / (identifier + ".eval.json")
                result_path.write_text(raw, encoding="utf-8")
                assertions = oracle["check_eval"](case, raw)
                checks = assertions["checks"]
                entry.update({
                    "expression_id": case["expression"], "expression_sha256": hashlib.sha256(expression.encode("utf-8")).hexdigest(),
                    "result_schema": case["schema"], "input_mode": case["mode"],
                    "native_result": str(result_path.relative_to(ROOT)), "native_result_sha256": digest(result_path),
                    "evidence_status": assertions["semantic_status"], "rejection_code": assertions["rejection_code"],
                    "native_value": assertions["native_value"],
                })
            entry["checks"] = checks
            if not checks or not all(item["passed"] is True for item in checks):
                raise VerificationError("Native evidence oracle has missing or failed assertions")
            entry["result"] = "pass"
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        write_report(report)
    corpus["source_sha256_after"] = {name: digest(ROOT / name) for name in source_files}
    corpus["source_unchanged"] = corpus["source_sha256_before"] == corpus["source_sha256_after"]
    supplement_path = directory / "supplement.json"
    supplement_path.write_text(json.dumps(supplement, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    corpus["supplement"] = {"path": str(supplement_path.relative_to(ROOT)), "sha256": digest(supplement_path)}
    corpus["passed_count"] = sum(item["result"] == "pass" for item in corpus["specimens"])
    corpus["accepted_evidence_count"] = sum(item.get("evidence_status") in ("accepted", "validated-output") and item["result"] == "pass" for item in corpus["specimens"])
    corpus["expected_rejection_count"] = sum(item.get("evidence_status") == "rejected" and item["result"] == "pass" for item in corpus["specimens"])
    if (corpus["passed_count"], corpus["accepted_evidence_count"], corpus["expected_rejection_count"], corpus["source_unchanged"]) != (16, 6, 10, True):
        failed = [item["id"] for item in corpus["specimens"] if item["result"] != "pass"]
        raise VerificationError("Native evidence checks failed or source changed: " + ", ".join(failed))
    corpus["result"] = "pass"


def verify_contract_adapter(report):
    """Retain native adapter evidence without converting it to contract acceptance."""
    corpus = report["contract_adapter_corpus"]
    corpus["result"] = "fail"
    destination = OUTPUT / "contract-adapter"
    destination.mkdir(parents=True, exist_ok=True)
    receipt = destination / "report.json"
    receipt.unlink(missing_ok=True)
    try:
        adapter_gate = runpy.run_path(str(ROOT / "scripts/verify_typst_contract_adapter.py"))
        arguments = ["--output", str(destination)]
        corpus["invocation"] = {
            "interface": "scripts.verify_typst_contract_adapter.main(argv)",
            "arguments": arguments, "external_process": False, "return_code": None,
        }
        runner = adapter_gate["verify"]
        saved = runner.ROOT, runner.OUTPUT
        try:
            status = adapter_gate["main"](arguments)
        finally:
            runner.ROOT, runner.OUTPUT = saved
        corpus["invocation"]["return_code"] = status
        if type(status) is not int or status != 0:
            raise VerificationError(f"Contract adapter gate returned {status!r}; expected 0")
        evidence = json.loads(receipt.read_text(encoding="utf-8"))
        if (evidence.get("passed") is not True
                or evidence.get("contract_acceptance") != "blocked"
                or [evidence.get(key) for key in (
                    "passed_count", "verified_rendered_outputs", "intended_rejections",
                    "explicit_unsupported_cases",
                )] != [21, 7, 9, 5]):
            raise VerificationError("Contract adapter lacks the complete bounded native result")
        corpus.update(
            result="pass", verified_rendered_outputs=7, intended_rejections=9,
            explicit_unsupported_cases=5, contract_acceptance="blocked",
        )
    finally:
        if receipt.is_file():
            corpus.update(report=str(receipt.relative_to(ROOT)), report_sha256=digest(receipt))


def verify_packaging(report):
    """Use the canonical watchdog for the isolated package consumer corpus."""
    package_gate = runpy.run_path(str(ROOT / "scripts/verify_package.py"))
    package_gate["verify"](report, globals())


def verify_submission_policy(report):
    """Keep supplied-data policy validation separate from institutional acceptance."""
    corpus = report["submission_policy_corpus"]
    corpus["result"] = "fail"
    receipt = OUTPUT / "submission-policy/report.json"
    receipt.unlink(missing_ok=True)
    try:
        gate = runpy.run_path(str(ROOT / "tests/policy/verify.py"))
        status = gate["main"]([])
        corpus["invocation"] = {"interface": "tests/policy/verify.py::main(argv)",
                                "external_process": False, "return_code": status}
        if type(status) is not int or status != 0:
            raise VerificationError("The bounded policy fixture gate failed")
        evidence = json.loads(receipt.read_text(encoding="utf-8"))
        if (evidence.get("passed") is not True
                or [evidence.get(key) for key in ("passed_count", "data_valid_cases", "intended_data_failures")] != [64, 27, 37]
                or evidence.get("source_unchanged") is not True
                or evidence.get("binding_pdf_unchanged") is not True
                or evidence.get("rendered_policy_qualified") is not False
                or evidence.get("submission_approved") is not False):
            raise VerificationError("Incomplete or overstated policy fixture evidence")
        corpus.update(result="pass", passed_count=64, data_valid_cases=27, intended_data_failures=37,
                      rendered_policy_qualified=False, submission_approved=False)
    finally:
        if receipt.is_file():
            corpus.update(report=str(receipt.relative_to(ROOT)), report_sha256=digest(receipt))


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
        "navigation_corpus": {
            "requirement": "COR-02",
            "scope": "Bounded synthetic contents, bookmarks, links, appendix content and page labels",
            "result": "unexecuted",
            "specimens": [],
        },
        "configuration_corpus": {
            "requirement": "COR-03",
            "scope": "Bounded legacy options, bibliography resources, declaration content and logo rejection",
            "result": "unexecuted",
            "specimens": [],
        },
        "terms_corpus": {
            "requirements": ["COR-02", "COR-05"],
            "scope": "Bounded abbreviation/glossary/index values, actual references and unsupported-extraction diagnostics",
            "result": "unexecuted",
            "specimens": [],
        },
        "optional_corpus": {
            "requirement": "COR-05",
            "scope": "Bounded public optional sections, typed/private-log rejections and authored residual controls",
            "result": "unexecuted",
            "specimens": [],
            "reviewer_ready_certified": False,
            "policy_or_approval_certified": False,
        },
        "blind_corpus": {
            "requirement": "COR-04",
            "scope": "Bounded managed-identity projection and explicit authored residual failures",
            "result": "unexecuted",
            "specimens": [],
            "reviewer_ready_certified": False,
        },
        "contract_adapter_corpus": {
            "scope": "Bounded native Typst metadata, precedence, order and invalid-input slice",
            "result": "unexecuted",
            "contract_acceptance": "blocked",
        },
    }
    report["image_corpus"] = {
        "scope": "Bounded PNG/JPEG/SVG, native path and byte inputs across four profiles",
        "result": "unexecuted", "specimens": [],
    }
    report["layout_order_corpus"] = {
        "scope": "Bounded section order, logical pagination, native destinations and A4/30mm geometry",
        "result": "unexecuted", "specimens": [],
    }
    report["native_evidence_corpus"] = {
        "requirements": ["TYP-04", "TST-03"], "result": "unexecuted", "specimens": [],
        "replay_qualified": False,
    }
    report["packaging_corpus"] = {
        "requirements": ["PKG-01", "PKG-02", "PKG-03"],
        "result": "unexecuted", "specimens": [],
        "registry_submission_qualified": False, "offline_replay_qualified": False,
    }
    report["submission_policy_corpus"] = {
        "requirements": ["POL-03", "POL-04", "POL-05", "POL-06", "POL-07"],
        "result": "unexecuted", "rendered_policy_qualified": False, "submission_approved": False,
    }
    # An interrupted invocation must not leave a previous successful receipt.
    write_report(report)
    try:
        clear_previous_outputs()
        oracle = runpy.run_path(str(ROOT / ORACLES))
        navigation_oracle = runpy.run_path(str(ROOT / NAVIGATION_ORACLES))
        configuration_oracle = runpy.run_path(str(ROOT / CONFIGURATION_ORACLES))
        blind_oracle = runpy.run_path(str(ROOT / BLIND_ORACLES))
        terms_oracle = runpy.run_path(str(ROOT / TERMS_ORACLES))
        image_oracle = runpy.run_path(str(ROOT / IMAGE_ORACLES))
        layout_order_oracle = runpy.run_path(str(ROOT / LAYOUT_ORDER_ORACLES))
        optional_oracle = runpy.run_path(str(ROOT / OPTIONAL_ORACLES))
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
        verify_cor02(report, navigation_oracle)
        verify_cor03(report, configuration_oracle)
        verify_terms(report, terms_oracle, navigation_oracle)
        verify_cor04(report, blind_oracle)
        verify_images(report, image_oracle)
        verify_layout_order(report, layout_order_oracle, navigation_oracle)
        verify_cor05(report, optional_oracle)
        verify_native_evidence(report)
        verify_contract_adapter(report)
        verify_packaging(report)
        verify_submission_policy(report)
        report["passed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"Verification failed: {exc}", file=sys.stderr)
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_report(report)
    if report["passed"]:
        print("Verified thesis/sample PDFs, 14 COR-01, 3 COR-02, 34 COR-03, 25 terms, 10 COR-04, 20 image, 9 layout/order, 47 COR-05, 16 native-evidence, 21 bounded contract-adapter and 10 local package cases (including explicit residual scans and native/semantic rejections; shared contract acceptance remains blocked), plus 64 supplied-data policy fixtures (submission approval remains unqualified); evidence: build/verification/report.json")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
