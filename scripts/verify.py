#!/usr/bin/env python3
"""Verify shipped PDFs and bounded content, navigation, configuration and privacy corpora."""

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
NAVIGATION_ORACLES = "tests/rendered/cor02/oracles.py"
CONFIGURATION_ORACLES = "tests/rendered/cor03/oracles.py"
BLIND_ORACLES = "tests/rendered/cor04/oracles.py"
TERMS_ORACLES = "tests/rendered/terms/oracles.py"
IMAGE_ORACLES = "tests/rendered/images/oracles.py"
LAYOUT_ORDER_ORACLES = "tests/rendered/layout-order/oracles.py"


class VerificationError(Exception):
    """A required verification command or PDF contract failed."""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(value) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def run(command: list[str], log_name: str, commands=None, *, combined=False, expected_exit=0) -> str:
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
        "expected_exit_code": expected_exit,
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
    if record["exit_code"] != expected_exit:
        raise VerificationError(
            f"{log_name}: exit {record['exit_code']} != expected {expected_exit}; see {log_path}"
        )
    return stdout + stderr if combined else stdout


def clear_previous_outputs():
    """Delete generated verifier outputs without touching retained baselines."""
    for directory in (OUTPUT, OUTPUT / "cor01", OUTPUT / "cor02", OUTPUT / "cor03", OUTPUT / "cor04", OUTPUT / "terms", OUTPUT / "images", OUTPUT / "layout-order"):
        directory.mkdir(parents=True, exist_ok=True)
        suffixes = {".pdf", ".txt", ".log"}
        if directory in (OUTPUT / "cor02", OUTPUT / "cor03", OUTPUT / "cor04", OUTPUT / "terms", OUTPUT / "images", OUTPUT / "layout-order"):
            suffixes.update({".json", ".html", ".xml"})
        for path in directory.iterdir():
            if path.suffix in suffixes and (path.is_file() or path.is_symlink()):
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
                    [*options, "--deps", str(dependencies)],
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
                if not dependencies.is_file() or not json.loads(dependencies.read_text(encoding="utf-8")):
                    raise VerificationError("COR-04 compile produced no dependency inventory")
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
        "blind_corpus": {
            "requirement": "COR-04",
            "scope": "Bounded managed-identity projection and explicit authored residual failures",
            "result": "unexecuted",
            "specimens": [],
            "reviewer_ready_certified": False,
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
        report["passed"] = True
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(f"Verification failed: {exc}", file=sys.stderr)
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_report(report)
    if report["passed"]:
        print("Verified thesis/sample PDFs, 14 COR-01, 3 COR-02, 34 COR-03, 25 terms, 10 COR-04, 20 image and 9 layout/order cases (including three failed residual-identity scans); evidence: build/verification/report.json")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
