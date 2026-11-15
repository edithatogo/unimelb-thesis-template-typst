#!/usr/bin/env python3
"""Render the supported UMTHESIS metadata slice with a pinned Typst adapter.

The canonical bundle remains unchanged. Native execution reports are separate
from contract requirement acceptance, which also needs an implemented adapter
registration, a qualified source revision and the remaining engine work.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tomllib
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from scripts.thesis_contract import ContractError, configuration_digest, load_bundle, read_json
from scripts import verify

ENTRY_POINT = "adapters/typst/v1/entry.typ"
DEFAULT_BODY = "tests/contract-adapter/body.typ"
ADAPTER_VERSION = "1.0.0"
CREATION_TIMESTAMP = "1794700800"
GENERATED_NAMES = {
    "input.json", "document.pdf", "document.txt", "document.qpdf.json",
    "document.bbox.html", "document-compile.log", "document-qpdf.log",
    "document-pdfinfo.log", "document-pdftotext.log", "native.log", "bbox.log",
    "native-report.json", "typst-version.log", "qpdf-version.log",
    "pdfinfo-version.log", "pdftotext-version.log",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def resolve_inputs(bundle, metadata=None, cli=(), explicit=None):
    """Resolve all five layers once, using the canonical schema and semantics."""
    return bundle.normalize(metadata, bundle.parse_cli(cli), explicit)


def unsupported_paths(configuration):
    """Fail closed on fields whose rendering/projection is not implemented here."""
    paths = []
    for key, supported in (
        ("purpose", {"draft", "examination"}),
        ("identity", {"identified"}),
        ("output", {"pdf"}),
        ("language", {"en"}),
        ("label_locale", {"en"}),
    ):
        if configuration[key] not in supported:
            paths.append(key)
    if configuration["pdf_standards"]:
        paths.append("pdf_standards")
    if configuration["bibliography"] != {"mode": "unified", "style": "apa"}:
        paths.append("bibliography")
    if configuration["approval_refs"]:
        paths.append("approval_refs")
    fields = {
        "title": None, "author": {"student_record_name", "orcid"},
        "degree": {"kind", "course"}, "academic_units": None,
        "submission": {"month"}, "abstract": None,
        "declarations": {"original_work", "word_count"},
    }
    for key, value in configuration["metadata"].items():
        if key not in fields:
            paths.append("metadata." + key)
        elif fields[key] is not None:
            paths.extend("metadata." + key + "." + name for name in value if name not in fields[key])
    if configuration["metadata"].get("declarations", {}).get("original_work") is False:
        paths.append("metadata.declarations.original_work")
    return sorted(paths)


def source_hashes(body):
    paths = {ROOT / "scripts" / name for name in ("typst_contract_adapter.py", "thesis_contract.py", "verify.py")}
    paths.add(ROOT / "typst.toml")
    for folder in ("adapters/typst/v1", "utils", "config", "layouts", "pages", "assets/colors"):
        paths.update((ROOT / folder).rglob("*.typ"))
    paths.add(body)
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}


def render(configuration, output, body, commands):
    envelope = {
        "schema_version": 1,
        "configuration": configuration,
        "configuration_sha256": configuration_digest(configuration),
    }
    input_path = output / "input.json"
    write_json(input_path, envelope)
    details, _ = verify.verify_pdf(
        ENTRY_POINT, output / "document.pdf", "document", commands,
        ["--ignore-system-fonts", "--creation-timestamp", CREATION_TIMESTAMP,
         "--input", "contract-input=/" + input_path.relative_to(ROOT).as_posix(),
         "--input", "contract-body=/" + body.relative_to(ROOT).as_posix()],
    )
    native = verify.run(["qpdf", "--json", str(output / "document.pdf")], "native.log", commands)
    (output / "document.qpdf.json").write_text(native, encoding="utf-8")
    parsed = json.loads(native)
    if not isinstance(parsed, dict) or len(parsed.get("pages", [])) != details["pages"]:
        raise verify.VerificationError("Native PDF report does not match the compiled page count")
    bbox = verify.run(["pdftotext", "-bbox-layout", str(output / "document.pdf"), "-"], "bbox.log", commands)
    (output / "document.bbox.html").write_text(bbox, encoding="utf-8")
    if len(ET.fromstring(bbox).findall(".//{*}page")) != details["pages"]:
        raise verify.VerificationError("Bounding-box report does not match the compiled page count")
    return details


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=ROOT / "contracts/thesis/v1")
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--fixture-manifest-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--body", type=Path, default=Path(DEFAULT_BODY))
    commands = parser.add_subparsers(dest="command", required=True)
    fixture = commands.add_parser("fixture")
    fixture.add_argument("id")
    fixture.add_argument("--fixture-sha256", required=True)
    external = commands.add_parser("render")
    external.add_argument("--metadata", type=Path)
    external.add_argument("--explicit", type=Path)
    external.add_argument("--set", action="append", default=[], dest="overrides")
    args = parser.parse_args(argv)
    output = args.output if args.output.is_absolute() else ROOT / args.output
    body = args.body if args.body.is_absolute() else ROOT / args.body
    if (output.is_symlink() or output.resolve() == ROOT / "build"
            or not output.resolve().is_relative_to(ROOT / "build")):
        parser.error("Output must be a subdirectory under build")
    output.mkdir(parents=True, exist_ok=True)
    for name in GENERATED_NAMES:
        artifact = output / name
        if artifact.is_file() or artifact.is_symlink():
            artifact.unlink()
    # Use the canonical bounded command runner and PDF checks. Only this
    # adapter invocation's output directory changes; all commands retain 60s.
    verify.ROOT, verify.OUTPUT = ROOT, output
    started = datetime.now(timezone.utc).isoformat()
    report = {
        "schema_version": 1, "scope": "typst-contract-adapter-native-slice",
        "adapter_api_version": ADAPTER_VERSION,
        "source_revision": None, "source_kind": "content-hash-bound-native-slice", "source_revision_status": "uncollected",
        "started_at_utc": started, "result": "failed", "exit_code": None,
        "normalization": "unexecuted", "rendering": "unexecuted",
        "normalized_configuration": None, "configuration_sha256": None,
        "diagnostics": [], "unsupported_paths": [], "commands": [], "artifacts": {},
        "contract_acceptance": "blocked-pending-adapter-registration-and-qualified-source",
        "institutional_approval": "unverified", "latex_execution": "unexecuted",
    }
    report_path = output / "native-report.json"
    write_json(report_path, report)
    status = 1
    try:
        if body.is_symlink() or not body.resolve().is_relative_to(ROOT) or not body.is_file():
            raise ContractError("invalid-resource", "body must be a regular project source file")
        report["source_sha256_before"] = source_hashes(body)
        bundle = load_bundle(args.contract, args.contract_sha256)
        if bundle.compatibility["adapter_api_version"] != ADAPTER_VERSION:
            raise ContractError("stale-adapter", "adapter API differs from the pinned contract")
        fixture_digest = digest(bundle.root / "fixtures.json")
        if fixture_digest != args.fixture_manifest_sha256:
            raise ContractError("stale-fixture", "fixture manifest differs from the required pin")
        report.update(contract_version=bundle.manifest["contract_version"], contract_sha256=bundle.digest,
                      fixture_manifest_sha256=fixture_digest)
        if args.command == "fixture":
            entry = bundle.fixtures.get(args.id)
            if entry is None or entry["sha256"] != args.fixture_sha256:
                raise ContractError("stale-fixture", "fixture ID or digest differs from the required pin")
            fixture_input = read_json(bundle.root / entry["path"])
            report["fixture"] = {"id": args.id, "sha256": entry["sha256"]}
            metadata, cli, explicit = fixture_input["metadata"], fixture_input["cli"], fixture_input["explicit"]
        else:
            metadata = read_json(args.metadata) if args.metadata else {}
            explicit = read_json(args.explicit) if args.explicit else {}
            cli = args.overrides
        layers = {"metadata": metadata, "cli": cli, "explicit": explicit}
        report["input_layers_sha256"] = configuration_digest(layers)
        normalized = resolve_inputs(bundle, metadata, cli, explicit)
        configuration = normalized["configuration"]
        report.update(normalization="valid", normalized_configuration=configuration,
                      configuration_sha256=configuration_digest(configuration), diagnostics=normalized["diagnostics"])
        report["unsupported_paths"] = unsupported_paths(configuration)
        if report["unsupported_paths"]:
            report.update(result="unsupported", rendering="unsupported")
            status = 2
        else:
            with (ROOT / "typst.toml").open("rb") as manifest:
                expected_version = tomllib.load(manifest)["tool"]["typst"]["version"]
            report["typst_manifest_sha256"] = digest(ROOT / "typst.toml")
            report["expected_typst_version"] = expected_version
            report["tool_versions"] = {}
            for executable, option in (("typst", "--version"), ("qpdf", "--version"),
                                       ("pdfinfo", "-v"), ("pdftotext", "-v")):
                version = verify.run([executable, option], executable + "-version.log", report["commands"], combined=True)
                if not version.strip():
                    raise verify.VerificationError("Required tool did not report its version")
                report["tool_versions"][executable] = version.splitlines()[0]
                if executable == "typst" and version.split()[:2] != ["typst", expected_version]:
                    raise verify.VerificationError(
                        f"Expected Typst {expected_version} from typst.toml, got {version.strip()!r}"
                    )
            report["rendering"] = "running"
            report["document"] = render(configuration, output, body, report["commands"])
            report.update(result="rendered", rendering="executed")
            status = 0
    except ContractError as exc:
        report.update(result="rejected", normalization="invalid" if report["normalization"] == "unexecuted" else report["normalization"],
                      error_code=exc.code, error=str(exc))
        print(str(exc), file=sys.stderr)
    except Exception as exc:
        report.update(error_code="execution-failed", error=f"{type(exc).__name__}: {exc}")
        if report["rendering"] == "running":
            report["rendering"] = "failed"
        print(report["error"], file=sys.stderr)
    finally:
        if "source_sha256_before" in report:
            try:
                after = source_hashes(body)
                report.update(source_sha256_after=after, sources_unchanged=report["source_sha256_before"] == after)
                if not report["sources_unchanged"]:
                    report.update(result="failed", error_code="stale-source", error="Rendering sources changed during execution")
                    status = 1
            except OSError as exc:
                report.update(result="failed", sources_unchanged=False, error_code="stale-source", error=f"{type(exc).__name__}: rendering source unavailable")
                status = 1
        for name in sorted(GENERATED_NAMES - {"native-report.json"}):
            artifact = output / name
            if artifact.is_file():
                report["artifacts"][artifact.name] = digest(artifact)
        report.update(exit_code=status, finished_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(report_path, report)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
