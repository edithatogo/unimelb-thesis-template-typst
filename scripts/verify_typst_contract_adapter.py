#!/usr/bin/env python3
"""Run the bounded native Typst adapter corpus through the existing command runner."""
from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import runpy
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from scripts import verify
from scripts import typst_contract_adapter as adapter
from scripts.thesis_contract import load_bundle, read_json
from scripts.typst_contract_adapter import GENERATED_NAMES

EXPECTATIONS = "tests/contract-adapter/expectations.json"
ORACLES = "tests/contract-adapter/oracles.py"
PDF_HELPERS = "tests/rendered/cor02/oracles.py"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def invoke_adapter(arguments, output, entry, expected_status):
    """Call the CLI parser in-process; only actual tools need process deadlines."""
    saved = verify.ROOT, verify.OUTPUT
    stdout, stderr = io.StringIO(), io.StringIO()
    status = None
    started = time.monotonic()
    invocation = {
        "interface": "scripts.typst_contract_adapter.main(argv)",
        "arguments": arguments, "external_process": False,
        "expected_return_code": expected_status,
    }
    entry["invocations"].append(invocation)
    try:
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = adapter.main(arguments)
    finally:
        verify.ROOT, verify.OUTPUT = saved
        log = output / "adapter-invocation.log"
        log.write_text("In-process adapter invocation\nStdout:\n" + stdout.getvalue()
                       + "\nStderr:\n" + stderr.getvalue(), encoding="utf-8")
        invocation.update(return_code=status, duration_seconds=time.monotonic() - started,
                          log=log.relative_to(ROOT).as_posix(), log_sha256=digest(log))
    if type(status) is not int or status != expected_status:
        raise verify.VerificationError(f"Adapter returned {status!r}; expected {expected_status}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("build/contract-adapter-verification"))
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    if output.is_symlink() or not output.resolve().is_relative_to(ROOT / "build"):
        parser.error("Verification output must be under build")
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "report.json"
    report = {"schema_version": 1, "source_revision": None, "source_kind": "content-hash-bound-native-slice", "source_revision_status": "uncollected",
              "scope": "18 canonical configuration fixtures plus three local rendering/precedence controls",
              "contract_acceptance": "blocked", "shared_matter_order_oracle": "absent-from-current-canonical-bundle",
              "latex_execution": "unexecuted", "institutional_approval": "unverified",
              "passed": False, "command_timeout_seconds": verify.TIMEOUT_SECONDS,
              "started_at_utc": datetime.now(timezone.utc).isoformat(), "cases": []}
    write_json(report_path, report)
    try:
        expectations = read_json(ROOT / EXPECTATIONS)
        oracle = runpy.run_path(str(ROOT / ORACLES))
        pdf_helper = runpy.run_path(str(ROOT / PDF_HELPERS))
        cases = expectations["cases"]
        if ([c["id"] for c in cases] != list(oracle["EXPECTED_IDS"])
                or expectations["contract_sha256"] != oracle["CONTRACT_PIN"]
                or expectations["fixture_manifest_sha256"] != oracle["FIXTURE_MANIFEST_PIN"]):
            raise verify.VerificationError("Adapter expectations omit, duplicate or change a pinned case identity")
        bundle = load_bundle(ROOT / "contracts/thesis/v1", expectations["contract_sha256"])
        if digest(bundle.root / "fixtures.json") != expectations["fixture_manifest_sha256"]:
            raise verify.VerificationError("Shared fixture manifest differs from the adapter pin")
        if [c["id"] for c in cases if c["origin"] == "canonical-fixture"] != list(bundle.fixtures):
            raise verify.VerificationError("Adapter corpus does not account for every canonical fixture")
        report.update(contract_sha256=bundle.digest, fixture_manifest_sha256=expectations["fixture_manifest_sha256"],
                      expectations_sha256=digest(ROOT / EXPECTATIONS), oracle_sha256=digest(ROOT / ORACLES),
                      pdf_parser_sha256=digest(ROOT / PDF_HELPERS))
        for case in cases:
            case_output = output / case["id"]
            case_output.mkdir(exist_ok=True)
            # These exact old generated outputs must be removed by the producer
            # for invalid and unsupported inputs as well as successful renders.
            for name in GENERATED_NAMES:
                (case_output / name).write_text("STALE ADAPTER OUTPUT MUST NOT PASS\n", encoding="utf-8")
            entry = {"id": case["id"], "origin": case["origin"], "expected_outcome": case["outcome"],
                     "passed": False, "invocations": [], "errors": []}
            report["cases"].append(entry)
            try:
                command = ["--contract-sha256", expectations["contract_sha256"],
                           "--fixture-manifest-sha256", expectations["fixture_manifest_sha256"],
                           "--output", str(case_output.relative_to(ROOT))]
                fixture = None
                if case["origin"] == "canonical-fixture":
                    row = bundle.fixtures[case["id"]]
                    if row["sha256"] != case["fixture_sha256"]:
                        raise verify.VerificationError("Adapter case has a stale fixture pin")
                    fixture = read_json(bundle.root / row["path"])
                    if (case["outcome"] == "invalid") != (fixture["expected"]["result"] == "invalid"):
                        raise verify.VerificationError("Adapter expectation contradicts the shared fixture")
                    command.extend(["fixture", case["id"], "--fixture-sha256", case["fixture_sha256"]])
                else:
                    command.append("render")
                    for layer in ("metadata", "explicit"):
                        data = case["inputs"][layer]
                        path = ROOT / data["path"]
                        if (path.is_symlink() or not path.resolve().is_relative_to(ROOT / "tests/contract-adapter/inputs")
                                or digest(path) != data["sha256"]):
                            raise verify.VerificationError("Adapter local input is missing, unsafe or stale")
                        command.extend(["--" + layer, str(path)])
                    for option in case["cli"]:
                        command.extend(["--set", option])
                expected_exit = {"rendered": 0, "invalid": 1, "unsupported": 2}[case["outcome"]]
                invoke_adapter(command, case_output, entry, expected_exit)
                native_report = read_json(case_output / "native-report.json")
                for name, expected_digest in native_report["artifacts"].items():
                    path = case_output / name
                    if name not in GENERATED_NAMES or path.is_symlink() or not path.is_file() or digest(path) != expected_digest:
                        raise verify.VerificationError("Adapter artifact is missing, unsafe or stale")
                for command_record in native_report["commands"]:
                    log = ROOT / command_record["log"]
                    if (not log.resolve().is_relative_to(case_output) or digest(log) != command_record["log_sha256"]
                            or command_record["timeout_seconds"] != 60 or command_record["timed_out"]
                            or command_record["exit_code"] != 0):
                        raise verify.VerificationError("Adapter command lacks successful bounded execution evidence")
                for path, expected_digest in native_report["source_sha256_before"].items():
                    if not (ROOT / path).is_file() or digest(ROOT / path) != expected_digest:
                        raise verify.VerificationError("Adapter source changed relative to its native report")
                output_files = {p.name for p in case_output.iterdir() if p.is_file()}
                if any((case_output / name).read_bytes().startswith(b"STALE ADAPTER OUTPUT")
                       for name in output_files.intersection(GENERATED_NAMES)):
                    raise verify.VerificationError("Adapter retained stale generated output")
                text = native = bbox = None
                if case["outcome"] == "rendered":
                    text = (case_output / "document.txt").read_text(encoding="utf-8")
                    native = read_json(case_output / "document.qpdf.json")
                    bbox = (case_output / "document.bbox.html").read_text(encoding="utf-8")
                    envelope = read_json(case_output / "input.json")
                    if envelope["configuration"] != native_report["normalized_configuration"]:
                        raise verify.VerificationError("Prepared renderer input differs from the resolved configuration")
                assertions = oracle["analyze"](case, fixture, native_report, output_files, pdf_helper, text, native, bbox)
                write_json(case_output / "oracle-report.json", assertions)
                entry.update(passed=assertions["passed"], assertion_count=len(assertions["checks"]),
                             errors=assertions["errors"], native_result=native_report["result"],
                             native_report_sha256=digest(case_output / "native-report.json"),
                             oracle_report_sha256=digest(case_output / "oracle-report.json"),
                             source_unchanged=native_report["sources_unchanged"], stale_outputs_removed=True)
            except Exception as exc:
                entry["errors"].append(f"{type(exc).__name__}: {exc}")
        report["passed_count"] = sum(c["passed"] for c in report["cases"])
        report["verified_rendered_outputs"] = sum(c["passed"] and c["expected_outcome"] == "rendered" for c in report["cases"])
        report["intended_rejections"] = sum(c["passed"] and c["expected_outcome"] == "invalid" for c in report["cases"])
        report["explicit_unsupported_cases"] = sum(c["passed"] and c["expected_outcome"] == "unsupported" for c in report["cases"])
        report["passed"] = (report["passed_count"], report["verified_rendered_outputs"],
                            report["intended_rejections"], report["explicit_unsupported_cases"]) == (21, 7, 9, 5)
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(report_path, report)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
