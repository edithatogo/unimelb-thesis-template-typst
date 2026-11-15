#!/usr/bin/env python3
"""Exercise supplied-data policy fixtures against one actual, synthetic PDF.

The PDF demonstrates artifact binding only. No fixture metadata is represented
as rendered by it, and no successful case establishes submission approval.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
import tomllib

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import submission_policy as policy
from scripts import verify

FIXTURES = ROOT / "tests/policy"
OUTPUT = ROOT / "build/verification/submission-policy"
EXPECTED_CASES = 64


def source_inventory():
    paths = [ROOT / "scripts/submission_policy.py", ROOT / "scripts/thesis_contract.py",
             ROOT / "scripts/native_evidence.py", ROOT / "scripts/verify.py", ROOT / "typst.toml",
             ROOT / "tests/maintenance/test_submission_policy.py"]
    for directory in (FIXTURES, policy.POLICY_ROOT, ROOT / "contracts/thesis/v1"):
        paths.extend(p for p in directory.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    return {p.relative_to(ROOT).as_posix(): policy.digest(p) for p in sorted(set(paths))}


def materialize(case, pdf_sha256, acknowledgement):
    text = json.dumps(case)
    text = text.replace("${PDF_SHA256}", pdf_sha256)
    text = text.replace("${RTP_ACKNOWLEDGEMENT}", acknowledgement)
    return policy.strict_json(text)


def assertions(case, report, pdf_sha256):
    expected = case["expected"]
    checks = {item["id"]: item for item in report["checks"]}
    result = [
        {"name": "Expected supplied-data outcome", "passed": report["data_result"] == expected["data_result"]},
        {"name": "Expected overall partial or failure", "passed": report["overall_result"] == expected["overall_result"]},
        {"name": "Never submission approval", "passed": report["submission_approved"] is False},
        {"name": "Exact actual PDF identity", "passed": report["artifact"]["sha256"] == pdf_sha256},
        {"name": "No rendered policy certification", "passed": report["artifact"]["pdf_structure"] == "unexecuted"
         and all(checks[key]["result"] == "unexecuted" for key in ("POL01.RENDERED", "POL02.RENDERED", "POL05.ETHICS"))},
        {"name": "Exact intended failure set", "passed": {key for key, item in checks.items() if item["result"] == "fail"}
         == set(expected["failed_checks"])},
        {"name": "Distinct emitted checks", "passed": len(checks) == len(report["checks"])},
        {"name": "Outstanding review bound to actual PDF", "passed": bool(report["human_checklist"])
         and all(item["status"] == "human-review-required" and item["pdf_sha256"] == pdf_sha256
                 for item in report["human_checklist"])},
    ]
    result.extend({"name": key + " expected result", "passed": checks.get(key, {}).get("result") == value}
                  for key, value in expected["checks"].items())
    if "canonical_publication_bridge" in expected:
        result.append({"name": "Explicit unsupported canonical bridge", "passed": report["canonical_publication_bridge"]
                       == expected["canonical_publication_bridge"]})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    output = args.output
    if (output.resolve() != OUTPUT.resolve() or output.is_symlink()
            or any(p.is_symlink() for p in OUTPUT.parents if p.is_relative_to(ROOT))):
        parser.error("The fixture gate writes only to build/verification/submission-policy without links.")
    output.mkdir(parents=True, exist_ok=True)
    receipt = output / "report.json"
    if any(p.is_symlink() or (p.is_file() and p.stat().st_nlink > 1) for p in output.iterdir()):
        parser.error("Fixture output files must not be symbolic or hard links.")
    report = {
        "schema_version": 1, "passed": False, "scope": "Supplied-data policy fixtures and actual PDF byte binding",
        "started_at_utc": datetime.now(timezone.utc).isoformat(), "command_timeout_seconds": verify.TIMEOUT_SECONDS,
        "source_revision": None, "source_kind": "content-hash-bound-candidate",
        "rendered_policy_qualified": False, "submission_approved": False,
        "commands": [], "cases": [], "errors": [],
    }
    saved = verify.ROOT, verify.OUTPUT
    try:
        # Clear previous report first; a later interrupted or failed run cannot retain success.
        receipt.write_text(json.dumps(report, indent=2) + "\n")
        for previous in output.iterdir():
            if previous != receipt and previous.is_file() and previous.suffix in {".pdf", ".txt", ".log", ".json"}:
                previous.unlink()
        report["source_sha256_before"] = source_inventory()
        manifest = policy.read_json(FIXTURES / "manifest.json")
        entries = manifest["cases"]
        identifiers = [x["id"] for x in entries]
        expected_paths = {"fixtures/" + identity + ".json" for identity in identifiers}
        actual_paths = {p.relative_to(FIXTURES).as_posix() for p in (FIXTURES / "fixtures").glob("*.json")}
        if (len(entries) != EXPECTED_CASES or len(set(identifiers)) != EXPECTED_CASES
                or {x["path"] for x in entries} != expected_paths or expected_paths != actual_paths
                or any(not identity or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in identity)
                       for identity in identifiers)):
            raise verify.VerificationError("The complete fixed policy fixture inventory is required")
        verify.ROOT, verify.OUTPUT = ROOT, output
        with (ROOT / "typst.toml").open("rb") as handle:
            compiler_version = tomllib.load(handle)["tool"]["typst"]["version"]
        actual_version = verify.run(["typst", "--version"], "typst-version.log", report["commands"]).strip()
        if actual_version.split()[:2] != ["typst", compiler_version]:
            raise verify.VerificationError("Policy fixture gate requires the manifest-pinned Typst version")
        report["compiler"] = actual_version
        pdf = output / "binding.pdf"
        details, text = verify.verify_pdf("tests/policy/specimen.typ", pdf, "binding", report["commands"])
        if details["pages"] != 1 or "Synthetic policy binding specimen" not in " ".join(text.split()):
            raise verify.VerificationError("The actual neutral PDF must contain the independent binding control")
        report["binding_pdf"] = details
        report["binding_pdf"]["policy_content_representation"] = "none; neutral artifact identity specimen only"
        pdf_sha256 = policy.digest(pdf)
        acknowledgement = policy.load_policy()["profile"]["rtp_acknowledgement"]
        for entry in entries:
            fixture = FIXTURES / entry["path"]
            if policy.digest(fixture) != entry["sha256"]:
                raise verify.VerificationError("Policy fixture bytes do not match the inventory")
            case = materialize(policy.read_json(fixture), pdf_sha256, acknowledgement)
            if case["id"] != entry["id"] or case["classification"] != "synthetic":
                raise verify.VerificationError("Unexpected policy fixture identity or classification")
            result = policy.evaluate(case["request"], pdf_path=pdf, evidence_root=FIXTURES,
                                     as_of=date.fromisoformat(case["as_of"]))
            path = output / (entry["id"] + ".json")
            path.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
            checks = assertions(case, result, pdf_sha256)
            report["cases"].append({"id": entry["id"], "fixture_sha256": entry["sha256"],
                "expected_data_result": case["expected"]["data_result"], "data_result": result["data_result"],
                "result": "pass" if all(item["passed"] for item in checks) else "fail",
                "report": str(path.relative_to(ROOT)), "report_sha256": policy.digest(path), "checks": checks})
        report["passed_count"] = sum(x["result"] == "pass" for x in report["cases"])
        report["data_valid_cases"] = sum(x["data_result"] == "pass" for x in report["cases"])
        report["intended_data_failures"] = sum(x["data_result"] == "fail" for x in report["cases"])
        report["assertion_count"] = sum(len(x["checks"]) for x in report["cases"])
        report["source_sha256_after"] = source_inventory()
        report["source_unchanged"] = report["source_sha256_before"] == report["source_sha256_after"]
        report["binding_pdf_unchanged"] = policy.digest(pdf) == pdf_sha256
        if (report["passed_count"], report["data_valid_cases"], report["intended_data_failures"],
                report["source_unchanged"], report["binding_pdf_unchanged"]) != (EXPECTED_CASES, 27, 37, True, True):
            raise verify.VerificationError("Policy fixture expectations failed or source/artifact changed")
        report["passed"] = True
    except Exception as exc:
        report["errors"].append({"type": type(exc).__name__, "message": str(exc)})
        print("Policy fixture gate failed: " + type(exc).__name__, file=sys.stderr)
    finally:
        verify.ROOT, verify.OUTPUT = saved
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    if report["passed"]:
        print(f"Policy fixture expectations passed: {EXPECTED_CASES}; rendered policy and submission approval remain unqualified.")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
