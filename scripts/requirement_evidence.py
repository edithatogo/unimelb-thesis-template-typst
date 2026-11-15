#!/usr/bin/env python3
"""Produce and independently inspect internal, content-bound requirement receipts.

The existing central v1 wrapper is reused unchanged. Native report success is
bounded evidence, not completion of all UMTHESIS requirements or human approval.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from scripts import verify as runner
from scripts.native_evidence import EvidenceError as NativeError, strict_json
from scripts.thesis_contract import ContractError, load_bundle, validate

PROFILE = ROOT / "evidence/v1"
PROFILE_SHA256 = "379626f774c9bbbcecc4804b8aa2950f7afb1578b474da181d27af6448e7182c"
CONTRACT_SHA256 = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
CENTRAL_SHA256 = "ec2b6902a68328527b1d65e008a98874ca4103015a7535fda989a173b60d6c2e"
CENTRAL_BLOB = "730561b4ffd2ab8790905f76b648eefcfc8c328f"
REPOSITORY = "edithatogo/unimelb-thesis-template-typst"
OUTPUT_ROOT = ROOT / "build/requirement-evidence"
MAX_JSON_BYTES = 32 * 1024 * 1024
SHA = re.compile(r"^[0-9a-f]{64}$")
GIT = re.compile(r"^[0-9a-f]{40}$")


class ReceiptError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise ReceiptError(code, message)


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def parse_json_bytes(data):
    require(len(data) <= MAX_JSON_BYTES, "report-too-large", "A JSON report exceeds the bounded size.")
    try:
        return strict_json(data.decode("utf-8"))
    except (UnicodeError, NativeError) as exc:
        raise ReceiptError("invalid-json", "A required JSON file is missing or malformed.") from exc


def read_json(path, expected=None, *, code="artifact-tampered"):
    try:
        with Path(path).open("rb") as handle:
            data = handle.read(MAX_JSON_BYTES + 1)
    except OSError as exc:
        raise ReceiptError("invalid-json", "A required JSON file is missing or malformed.") from exc
    if expected is not None:
        require(hashlib.sha256(data).hexdigest() == expected, code, "The parsed JSON buffer differs from its trusted digest.")
    return parse_json_bytes(data)


def schema_check(schema, value):
    try:
        validate(schema, value)
    except ContractError as exc:
        raise ReceiptError("invalid-schema", "The value does not satisfy its pinned schema.") from exc


def safe_relative(value):
    require(isinstance(value, str) and value and not any(c in value for c in "\\\r\n\0:"),
            "unsafe-path", "Artifact paths must be safe relative POSIX paths.")
    path = PurePosixPath(value)
    require(not path.is_absolute() and all(part not in (".", "..", "") for part in value.split("/"))
            and path.as_posix() == value, "unsafe-path", "Artifact paths must be normalized and relative.")
    return value


def confined_file(root, relative):
    root = Path(root).resolve()
    candidate = root / safe_relative(relative)
    require(not any(p.is_symlink() for p in (candidate, *candidate.parents) if p != root and p.is_relative_to(root)),
            "unsafe-path", "Artifact links are not accepted.")
    require(candidate.resolve().is_relative_to(root) and candidate.is_file(),
            "missing-artifact", "A required regular artifact is missing.")
    return candidate


def datetime_value(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(parsed.tzinfo is not None, "invalid-time", "Times must carry an explicit timezone.")
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError, AttributeError) as exc:
        raise ReceiptError("invalid-time", "A receipt timestamp is invalid.") from exc


def current_time(now=None):
    value = now or datetime.now(timezone.utc)
    require(type(value) is datetime and value.tzinfo is not None, "invalid-time", "An aware assessment time is required.")
    return value.astimezone(timezone.utc)


def load_profile(path=PROFILE):
    path = Path(path)
    try:
        manifest = read_json(path / "manifest.json", PROFILE_SHA256, code="profile-drift")
        require(set(manifest["files"]) == {"request.schema.json", "sidecar.schema.json", "adapters.json", "sources.json"},
                "profile-drift", "The evidence profile inventory is incomplete.")
        values = {}
        for name, expected in manifest["files"].items():
            values[name.removesuffix(".json")] = read_json(path / name, expected, code="profile-drift")
        load_bundle(ROOT / "contracts/thesis/v1", CONTRACT_SHA256)
        contract = read_json(ROOT / "contracts/thesis/v1/manifest.json", CONTRACT_SHA256, code="contract-drift")
        values["contract_manifest"] = contract
        central_path = ROOT / values["sources"]["central_schema"]["local_source"]
        data = central_path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == CENTRAL_SHA256
                and hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest() == CENTRAL_BLOB,
                "central-schema-drift", "The existing central wrapper schema changed.")
        values["central"] = parse_json_bytes(data)
        values["catalogue"] = read_json(ROOT / "contracts/thesis/v1/requirements.json", contract["files"]["requirements.json"], code="contract-drift")
        values["source_ledger"] = read_json(ROOT / "contracts/thesis/v1/sources.json", contract["files"]["sources.json"], code="contract-drift")
        require(len(values["catalogue"]["requirements"]) == 51, "catalogue-drift", "All 51 stable requirement IDs are required.")
        return values
    except (OSError, KeyError, TypeError, ContractError) as exc:
        raise ReceiptError("profile-unavailable", "A pinned evidence or contract input is unavailable.") from exc


@contextmanager
def command_logs(directory):
    saved = runner.ROOT, runner.OUTPUT
    try:
        directory = output_directory(directory)
        for name in ("root.log", "revision.log", "tree.log", "state.log", "files.log"):
            path = directory / name
            require(not path.is_symlink() and (not path.exists() or (path.is_file() and path.stat().st_nlink == 1)),
                    "unsafe-output", "Source-probe logs cannot replace links or non-files.")
        runner.ROOT, runner.OUTPUT = ROOT, directory
        runner.OUTPUT.mkdir(parents=True, exist_ok=True)
        yield
    finally:
        runner.ROOT, runner.OUTPUT = saved


def source_snapshot(source_root, expected_revision, expected_tree, logs):
    source_root = Path(source_root).resolve()
    require(GIT.fullmatch(expected_revision) and GIT.fullmatch(expected_tree),
            "source-identity", "Full immutable source revision and tree IDs are required.")
    commands = []
    with command_logs(logs):
        def git(arguments, name):
            try:
                return runner.run(["git", "--no-optional-locks", "-C", str(source_root), *arguments], name + ".log", commands)
            except runner.VerificationError as exc:
                raise ReceiptError("source-probe-failed", "The bounded Git source probe failed.") from exc
        actual_root = Path(git(["rev-parse", "--show-toplevel"], "root").strip()).resolve()
        require(actual_root == source_root, "source-root", "The source root must be the repository root.")
        revision = git(["rev-parse", "HEAD"], "revision").strip()
        tree = git(["rev-parse", "HEAD^{tree}"], "tree").strip()
        require(revision == expected_revision, "wrong-revision", "The source revision differs from the required commit.")
        require(tree == expected_tree, "wrong-tree", "The source tree differs from the required tree.")
        require(not git(["status", "--porcelain=v1", "--untracked-files=normal"], "state").strip(),
                "dirty-source", "A clean source checkout is required for a native execution receipt.")
        entries = git(["ls-files", "--stage", "-z"], "files").split("\0")
    files = []
    for entry in entries:
        if not entry:
            continue
        metadata, relative = entry.split("\t", 1)
        mode, git_blob, stage = metadata.split(" ")
        require(stage == "0" and mode in ("100644", "100755"),
                "unsupported-source-entry", "Unmerged entries, links and submodules are not supported.")
        path = confined_file(source_root, relative)
        content = path.read_bytes()
        observed_blob = hashlib.sha1(b"blob " + str(len(content)).encode() + b"\0" + content).hexdigest()
        require(observed_blob == git_blob, "source-content-drift", "A tracked file differs from its Git object.")
        files.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest(), "git_blob": git_blob, "mode": mode})
    files.sort(key=lambda x: x["path"])
    require(files, "empty-source", "An empty source inventory is not execution evidence.")
    return {"repository": REPOSITORY, "revision": revision, "tree": tree, "dirty": False,
            "files": files, "inventory_sha256": json_digest(files)}


class Inputs:
    def __init__(self, source_root, artifact_root, source, *, bundled=False):
        self.source_root, self.artifact_root = Path(source_root), Path(artifact_root)
        self.bundled = bundled
        self.files = {item["path"]: item["sha256"] for item in source["files"]}
        self.artifacts, self.paths, self.contents = {}, {}, {}

    def source_file(self, name, expected):
        safe_relative(name)
        require(isinstance(expected, str) and SHA.fullmatch(expected) and self.files.get(name) == expected,
                "source-evidence-mismatch", "A native source identity does not match the actual commit.")

    def artifact(self, name, expected, role="native-artifact"):
        safe_relative(name)
        require(isinstance(expected, str) and SHA.fullmatch(expected), "invalid-digest", "An artifact digest is malformed.")
        relative = "artifacts/" + name
        path = confined_file(self.artifact_root, relative if self.bundled else name)
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected, "artifact-tampered", "A required artifact does not match its digest.")
        previous = self.artifacts.get(relative)
        require(previous is None or previous["sha256"] == expected, "conflicting-artifact", "One artifact path has conflicting digests.")
        item = {"path": relative, "original_path": name, "sha256": expected, "bytes": len(data),
                "role": role if previous is None else previous["role"]}
        self.artifacts[relative] = item
        self.paths[relative] = path
        self.contents[relative] = data
        return relative, path

    def unchanged(self):
        require(all(digest(path) == self.artifacts[relative]["sha256"] for relative, path in self.paths.items()),
                "artifact-changed-during-read", "An evidence input changed during verification.")


def native_records(value, pointer=""):
    """Visit native records, separating author data and observed tool identities."""
    if isinstance(value, list):
        for index, child in enumerate(value):
            yield from native_records(child, pointer + "/" + str(index))
    elif isinstance(value, dict):
        yield pointer, value
        for key, child in value.items():
            if key in ("inputs", "metadata", "normalized_configuration") or (not pointer and key == "executables"):
                continue
            yield from native_records(child, pointer + "/" + key.replace("~", "~0").replace("/", "~1"))


def native_input_paths(native, source_root):
    """Protect all declared native paths before any output or probe is written."""
    names = {"path", "pdf", "text", "log", "dependencies", "oracle_report", "pdf_structure", "review_diagnostics",
             "xmp", "report", "native_json", "bbox", "native_result", "native_failure_report", "bounding_boxes", "sidecar"}
    return [Path(source_root) / child for _pointer, item in native_records(native)
            for key, child in item.items() if isinstance(child, str) and (key in names or key.endswith("_path"))]


def native_report(request, source, inputs, profile, now):
    descriptor = request["native"]
    relative, path = inputs.artifact(descriptor["path"], descriptor["sha256"], "native-report")
    value = parse_json_bytes(inputs.contents[relative])
    require(isinstance(value, dict) and type(value.get("schema_version")) is int and value["schema_version"] == 1
            and type(value.get("passed")) is bool, "native-interface", "The native report interface is missing or malformed.")
    require(value.get("source_revision") == source["revision"] and value.get("source_dirty") is False,
            "native-wrong-revision", "Native results must identify this exact clean commit, even when another tree is equal.")
    inputs.source_file("scripts/verify.py", value.get("verifier_sha256"))
    inputs.source_file("typst.toml", value.get("typst_manifest_sha256"))
    start, finish = datetime_value(value.get("started_at_utc")), datetime_value(value.get("finished_at_utc"))
    require(datetime_value(request["run"]["not_before"]) <= start <= finish <= now,
            "stale-native-report", "The native report lies outside the required execution window.")
    require(now <= datetime_value(request["run"]["review_by"]), "review-expired", "The receipt review window has expired.")
    with confined_file(inputs.source_root, "typst.toml").open("rb") as handle:
        compiler = tomllib.load(handle)["tool"]["typst"]["version"]
    require(isinstance(value.get("compiler"), str) and value["compiler"].split()[:2] == ["typst", compiler],
            "compiler-mismatch", "The native compiler does not match the source manifest.")
    require(type(value.get("command_timeout_seconds")) is int and value["command_timeout_seconds"] == 60,
            "runtime-budget", "The native report must retain the existing command budget.")
    require(isinstance(value.get("python_version"), str) and value["python_version"].strip(),
            "tool-identities", "The native Python version observation is missing.")
    tools = value.get("tool_versions")
    binaries = value.get("executables")
    require(isinstance(tools, dict) and isinstance(binaries, dict) and all(
        isinstance(tools.get(name), str) and tools[name] and isinstance(binaries.get(name), dict)
        and isinstance(binaries[name].get("sha256"), str) and SHA.fullmatch(binaries[name]["sha256"])
        for name in ("typst", "qpdf", "pdfinfo", "pdftotext")),
        "tool-identities", "Required native tool versions and binary digests are missing.")
    require(all(isinstance(name, str) and isinstance(item, dict)
                and isinstance(item.get("sha256"), str) and SHA.fullmatch(item["sha256"])
                for name, item in binaries.items()), "tool-identities", "A native executable identity is malformed.")
    require(isinstance(value.get("commands"), list) and value["commands"]
            and all(isinstance(item, dict) and "command" in item for item in value["commands"]),
            "missing-commands", "The native report must retain its executed command inventory.")
    documents = value.get("documents")
    require(isinstance(documents, list), "native-documents", "The native document inventory is missing.")
    if value["passed"]:
        require({item.get("source") for item in documents if isinstance(item, dict)} == {"thesis.typ", "sample-chapter.typ"}
                and len(documents) == 2 and all(item.get("result") == "pass" and type(item.get("pages")) is int
                and item["pages"] > 0 and type(item.get("bytes")) is int and item["bytes"] > 0
                and all(isinstance(item.get(key), str) and SHA.fullmatch(item[key])
                        for key in ("pdf_sha256", "text_sha256", "source_sha256"))
                and item.get("pdf") and item.get("text") for item in documents),
                "false-native-pass", "A passing native report requires both actual shipped documents.")
    commands = []
    adapter = profile["adapters"]

    for pointer, item in native_records(value):
        # Current native v1 uses both named pairs and {path, sha256}
        # descriptors. Tool observations and author data are excluded by the
        # shared traversal; scan-hit path arrays are not file descriptors.
        if "sha256" in item or isinstance(item.get("path"), str):
            require(isinstance(item.get("path"), str), "missing-artifact-path", "A native descriptor has no string path.")
            require("sha256" in item, "missing-artifact-digest", "A native descriptor has no digest.")
            require(isinstance(item["sha256"], str) and SHA.fullmatch(item["sha256"]),
                    "invalid-digest", "A native descriptor digest is malformed.")
            name = safe_relative(item["path"])
            if name.startswith("build/"):
                inputs.artifact(name, item["sha256"])
            else:
                inputs.source_file(name, item["sha256"])
        if "command" in item:
            require(isinstance(item["command"], list) and item["command"] and all(isinstance(x, str) for x in item["command"])
                    and type(item.get("exit_code")) is int and type(item.get("expected_exit_code")) is int
                    and type(item.get("timed_out")) is bool and type(item.get("duration_seconds")) in (int, float)
                    and item["duration_seconds"] >= 0 and item.get("timeout_seconds") == 60,
                    "command-interface", "A native command record is malformed.")
            if value["passed"]:
                require(not item["timed_out"] and item["exit_code"] == item["expected_exit_code"],
                        "false-native-pass", "A passing native report contains a failed or timed-out command.")
            log, _ = inputs.artifact(item.get("log"), item.get("log_sha256"))
            environment = item.get("environment_overrides", {})
            require(isinstance(environment, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in environment.items()),
                    "command-interface", "Native environment observations must be typed strings.")
            commands.append({"pointer": pointer, "command": item["command"], "exit_code": item["exit_code"],
                "expected_exit_code": item["expected_exit_code"], "timed_out": item["timed_out"],
                "duration_seconds": item["duration_seconds"], "log": log, "log_sha256": item["log_sha256"],
                "environment_overrides": environment})
        for name in adapter["file_pairs"]:
            if name + "_sha256" in item:
                require(isinstance(item.get(name), str), "missing-artifact-path", "A declared artifact digest has no path.")
                inputs.artifact(item[name], item[name + "_sha256"])
            elif isinstance(item.get(name), str) and item[name].startswith("build/"):
                raise ReceiptError("missing-artifact-digest", "A native artifact path has no declared digest.")
        for name in adapter["source_pairs"]:
            if name + "_sha256" in item and isinstance(item.get(name), str):
                inputs.source_file(item[name], item[name + "_sha256"])
        for name in adapter["source_maps"]:
            if isinstance(item.get(name), dict):
                for filename, expected in item[name].items():
                    inputs.source_file(filename, expected)
    require(commands, "missing-commands", "The native report contains no executed command records.")
    for name, identifiers in adapter["native_requirement_map"].items():
        corpus = value.get(name)
        if value["passed"]:
            require(corpus is not None, "missing-native-corpus", "A required corpus is absent from the current native profile.")
        if corpus is not None:
            require(isinstance(corpus, dict) and corpus.get("result") in ("pass", "fail", "unexecuted"),
                    "corpus-interface", "A recognized native corpus has an invalid result.")
            if value["passed"]:
                require(corpus["result"] == "pass", "false-native-pass", "A native success contains an incomplete corpus.")
    return value, relative, commands


def property_report(request, inputs):
    descriptor = request["properties"]
    relative, path = inputs.artifact(descriptor["path"], descriptor["sha256"], "property-report")
    value = parse_json_bytes(inputs.contents[relative])
    require(isinstance(value, dict) and type(value.get("schema_version")) is int and value["schema_version"] == 1
            and type(value.get("passed")) is bool and type(value.get("seed")) is int and 0 <= value["seed"] <= 2**32 - 1
            and type(value.get("cases_per_property")) is int and value["cases_per_property"] >= 64
            and type(value.get("tests_run")) is int and value["tests_run"] == 10
            and type(value.get("elapsed_seconds")) in (int, float) and value["elapsed_seconds"] >= 0,
            "property-interface", "The bounded property-report interface is invalid or incomplete.")
    cases = value.get("generated_cases")
    require(isinstance(cases, dict) and len(cases) == 10 and all(
        isinstance(name, str) and name.startswith("test_") and type(count) is int and count == value["cases_per_property"]
        for name, count in cases.items()), "property-under-run", "Every recorded property must execute the declared case count.")
    sources = value.get("source_sha256")
    require(isinstance(sources, dict) and set(sources) == {"scripts/manage_terms.py", "scripts/validate_template.py", "tests/test_properties.py"},
            "property-sources", "The property report must identify every measured source.")
    for name, expected in sources.items():
        inputs.source_file(name, expected)
    if value["passed"]:
        require(value.get("failures") == [] and value.get("errors") == [] and value.get("skipped") == []
                and type(value.get("failure_threshold")) is int and value["failure_threshold"] == 0 and not value.get("harness_error"),
                "false-property-pass", "A passing property report contains failures, skips or a harness error.")
    return value, relative


def requirement_rows(profile, native, native_path, property_path):
    ledger = {item["id"]: item for item in profile["source_ledger"]["sources"]}
    result = []
    for requirement in profile["catalogue"]["requirements"]:
        observations = []
        for key, identifiers in profile["adapters"]["native_requirement_map"].items():
            corpus = native.get(key)
            if requirement["id"] in identifiers and corpus is not None:
                observations.append({"provider": key, "scope": corpus.get("scope", "Bounded native fixture corpus"),
                    "result": {"pass": "executed-pass", "fail": "executed-fail", "unexecuted": "unexecuted"}[corpus["result"]],
                    "evidence_ref": native_path, "full_requirement_qualified": False})
        if requirement["id"] == "TST-02":
            observations.append({"provider": "seeded-properties-v1", "scope": "Source-byte and seed inventory; exact revision/time were not recorded by the legacy producer",
                                 "result": "unexecuted", "evidence_ref": property_path, "full_requirement_qualified": False})
        failed = any(item["result"] == "executed-fail" for item in observations)
        passed = any(item["result"] == "executed-pass" for item in observations)
        references = [{"source_id": ref["source_id"], "url": ledger[ref["source_id"]]["url"], "clause": ref["clause"],
                       "retrieved_at": ledger[ref["source_id"]]["retrieved_at"], "sha256": ledger[ref["source_id"]]["content_sha256"]}
                      for ref in requirement["source_refs"]]
        states = {case["implementation_state"] for case in requirement["acceptance_cases"]}
        state = "implemented" if states == {"implemented"} else "planned"
        predicate = requirement["applicability"]["predicate"]
        applicable = predicate in ("always", "engine-typst", "output-pdf")
        applicability_reason = ("The programme-wide or Typst/PDF report predicate applies. " if applicable else
                                "No single canonical purpose/identity/output projection was recorded; thesis-specific applicability is unassessed. ")
        result.append({"id": requirement["id"], "source_refs": references, "programme_required": True,
            "applicability_predicate": predicate, "applicability": "applicable" if applicable else "unassessed",
            "applicability_reason": applicability_reason + requirement["applicability"]["scope"],
            "implementation_state": state, "implementation_basis": "Pinned canonical acceptance-case registration; bounded code execution is recorded separately below.",
            "expected": "executed-pass", "result": "executed-fail" if failed else ("blocked" if passed else "unexecuted"),
            "reason": "A bounded observation failed." if failed else ("Bounded observations passed; full normative acceptance remains unregistered or incomplete." if passed else "No exact-revision full acceptance has been established by these adapters."),
            "observations": observations, "full_requirement_qualified": False})
    return result


def assemble(request, source, inputs, profile, generated_at):
    schema_check(profile["request.schema"], request)
    manifest = profile["contract_manifest"]
    inputs.source_file("contracts/thesis/v1/manifest.json", CONTRACT_SHA256)
    for name, expected_hash in manifest["files"].items():
        inputs.source_file("contracts/thesis/v1/" + name, expected_hash)
    now = datetime_value(generated_at)
    native, native_path, commands = native_report(request, source, inputs, profile, now)
    properties, property_path = property_report(request, inputs)
    extras, ids = [], set()
    for item in request["sidecars"]:
        require(item["id"] not in ids, "duplicate-sidecar", "Sidecar identifiers must be unique.")
        ids.add(item["id"])
        artifact, _ = inputs.artifact(item["path"], item["sha256"], "sidecar")
        extras.append({"id": item["id"], "role": item["role"], "schema_version": item["schema_version"], "required": item["required"],
                       "artifact": artifact, "status": "unsupported", "reason": "Only file identity is validated; the supplied version has no registered semantic adapter."})
    overall = "partial" if native["passed"] and properties["passed"] else "fail"
    value = {"schema_version": 1, "artifact_kind": "umthesis-requirement-evidence", "profile_sha256": PROFILE_SHA256,
        "privacy": "internal-not-reviewer-safe", "source": source,
        "producer": {"sha256": digest(Path(__file__)), "revision": None, "revision_status": "uncollected-content-bound"},
        "central_schema": {"sha256": CENTRAL_SHA256, "git_blob": CENTRAL_BLOB, "source_id": "central-receipt-schema-current"},
        "contract": {"version": "1.0.0", "manifest_sha256": CONTRACT_SHA256,
                     "requirements_sha256": manifest["files"]["requirements.json"],
                     "sources_sha256": manifest["files"]["sources.json"],
                     "fixtures_sha256": manifest["files"]["fixtures.json"]},
        "request": request, "generated_at": generated_at, "review_by": request["run"]["review_by"],
        "native": {"artifact": native_path, "passed": native["passed"], "started_at": native["started_at_utc"],
                   "finished_at": native["finished_at_utc"], "schema_version": 1},
        "properties": {"artifact": property_path, "passed": properties["passed"], "seed": properties["seed"],
                       "cases_per_property": properties["cases_per_property"], "generated_cases": properties["generated_cases"],
                       "duration_seconds": properties["elapsed_seconds"], "exact_revision_execution": "uncollected-legacy-report",
                       "reason": "The legacy report identifies tested bytes and seed, but contains no intrinsic revision or run timestamp; neither is fabricated."},
        "provenance": {"compiler": native["compiler"], "python_version": native["python_version"], "tool_versions": native["tool_versions"],
                       "recorded_executable_sha256": {name: item["sha256"] for name, item in native["executables"].items()},
                       "fonts": "source-identities-uncollected", "complete_environment": "uncollected",
                       "normalized_configuration": None, "configuration_sha256": None, "configuration_binding": "uncollected-legacy-entrypoints"},
        "commands": commands, "artifacts": sorted(inputs.artifacts.values(), key=lambda x: x["path"]), "sidecars": extras,
        "requirements": requirement_rows(profile, native, native_path, property_path),
        "human_decisions": {"status": "not-collected", "records": []}, "exceptions": {"status": "unsupported", "records": []},
        "overall_result": overall, "full_programme_qualified": False, "institutional_approval": False, "blind_safe": False,
        "limitations": profile["adapters"]["limitations"]}
    schema_check(profile["sidecar.schema"], value)
    return value


def render_markdown(sidecar):
    lines = ["# Requirement evidence", "", "**Overall: " + sidecar["overall_result"] + ". Full programme acceptance is not established.**", "",
             "Internal provenance; this is not a reviewer-safe manifest or institutional approval.", "",
             "Source: `" + sidecar["source"]["revision"] + "`; tree `" + sidecar["source"]["tree"] + "`.",
             "Review by: `" + sidecar["review_by"] + "`.", "", "| Requirement | Applicability | Registered implementation | Observed requirement result | Bounded observations |", "| --- | --- | --- | --- | --- |"]
    for item in sidecar["requirements"]:
        observations = "; ".join(x["provider"] + ": " + x["result"] for x in item["observations"]) or "None"
        lines.append("| " + " | ".join((item["id"], item["applicability"], item["implementation_state"], item["result"], observations)) + " |")
    lines.extend(["", "## Limits", ""])
    lines.extend("- " + item for item in sidecar["limitations"])
    lines.extend(["", "The machine sidecar carries clause/date/hash links, exact artifact identities, command observations and unresolved human work.", ""])
    return "\n".join(lines)


def wrapper_for(sidecar, status_hash, markdown_hash):
    checks = [{"name": "source-and-artifact-integrity", "result": "pass", "reason": "Exact source and declared artifact bytes were checked."},
              {"name": "native-verification", "result": "pass" if sidecar["native"]["passed"] else "fail",
               "evidence": sidecar["native"]["artifact"], "reason": "Preserved native semantics; bounded fixtures are not full programme acceptance."},
              {"name": "property-revision-binding", "result": "skip", "evidence": sidecar["properties"]["artifact"],
               "reason": "Tested bytes and seed are recorded; the legacy report has no intrinsic revision/time."}]
    for item in sidecar["requirements"]:
        checks.append({"name": item["id"], "result": "fail" if item["result"] == "executed-fail" else "skip", "reason": item["reason"], "evidence": "requirement-status.json"})
    return {"schema_version": 1, "repository": REPOSITORY, "revision": sidecar["source"]["revision"],
            "generated_at": sidecar["generated_at"], "result": sidecar["overall_result"], "seed": sidecar["properties"]["seed"],
            "checks": checks, "artifacts": [{"path": "requirement-status.json", "sha256": status_hash},
                                             {"path": "requirements.md", "sha256": markdown_hash}]
            + [{"path": x["path"], "sha256": x["sha256"]} for x in sidecar["artifacts"]]}


def atomic_bytes(path, data):
    path = Path(path).absolute()
    require(path.resolve().is_relative_to(OUTPUT_ROOT.resolve())
            and not any(p.is_symlink() for p in path.parents if p.is_relative_to(ROOT)),
            "unsafe-output", "Output parents must stay inside the dedicated tree without links.")
    path.parent.mkdir(parents=True, exist_ok=True)
    require(not path.is_symlink() and (not path.exists() or (path.is_file() and path.stat().st_nlink == 1)),
            "unsafe-output", "Outputs cannot replace links or non-files.")
    descriptor, temporary = tempfile.mkstemp(prefix=".receipt-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def output_directory(value, protected=()):
    path = Path(value).absolute()
    require(path.resolve().is_relative_to(OUTPUT_ROOT.resolve()) and path.resolve() != OUTPUT_ROOT.resolve()
            and not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(ROOT)),
            "unsafe-output", "Output must be a dedicated directory under build/requirement-evidence without links.")
    require(not any(Path(p).resolve().is_relative_to(path.resolve()) for p in protected),
            "unsafe-output", "The output directory cannot contain a source evidence input.")
    require(not path.exists() or path.is_dir(), "unsafe-output", "The output must be a directory.")
    return path


def protected_inputs(request, source_root, additional=()):
    """Find declared input paths before replacing any previous receipt output."""
    protected = list(additional)
    if not isinstance(request, dict):
        return protected
    descriptors = [request.get(key) for key in ("native", "properties")]
    if isinstance(request.get("sidecars"), list):
        descriptors.extend(request["sidecars"])
    protected.extend(Path(source_root) / item["path"] for item in descriptors
                     if isinstance(item, dict) and isinstance(item.get("path"), str))
    native = request.get("native")
    if isinstance(native, dict) and isinstance(native.get("path"), str):
        try:
            document = read_json(confined_file(source_root, native["path"]))
        except ReceiptError:
            return protected  # Normal validation rejects this input after invalidation.

        protected.extend(native_input_paths(document, source_root))
    return protected


def produce(request, *, source_root, output, now=None, protected_paths=()):
    moment = current_time(now)
    protected = protected_inputs(request, source_root, protected_paths)
    output = output_directory(output, protected)
    output.mkdir(parents=True, exist_ok=True)
    revision = request.get("revision") if isinstance(request, dict) else None
    invalidate_output(output, revision if isinstance(revision, str) and GIT.fullmatch(revision) else "unresolved", moment)
    profile = load_profile()
    schema_check(profile["request.schema"], request)
    source = source_snapshot(source_root, request["revision"], request["tree"], output / "source-before")
    inputs = Inputs(source_root, source_root, source)
    sidecar = assemble(request, source, inputs, profile, moment.isoformat())
    for relative, path in inputs.paths.items():
        require(not path.resolve().is_relative_to(output.resolve()), "unsafe-output", "An output would replace its input evidence.")
        atomic_bytes(output / relative, inputs.contents[relative])
    after = source_snapshot(source_root, request["revision"], request["tree"], output / "source-after")
    require(source == after, "source-changed-during-read", "Source changed while the receipt was being produced.")
    inputs.unchanged()
    status = json.dumps(sidecar, indent=2, ensure_ascii=False, allow_nan=False).encode() + b"\n"
    markdown = render_markdown(sidecar).encode()
    wrapper = wrapper_for(sidecar, hashlib.sha256(status).hexdigest(), hashlib.sha256(markdown).hexdigest())
    schema_check(profile["central"], wrapper)
    atomic_bytes(output / "requirement-status.json", status)
    atomic_bytes(output / "requirements.md", markdown)
    atomic_bytes(output / "verification-receipt.json", json.dumps(wrapper, indent=2, ensure_ascii=False).encode() + b"\n")
    return wrapper, sidecar


def verify_receipt(receipt, *, source_root, expected_revision, trusted_sha256, now=None, logs=None):
    profile = load_profile()
    require(isinstance(trusted_sha256, str) and SHA.fullmatch(trusted_sha256), "missing-trust-anchor", "An independently trusted wrapper digest is required.")
    receipt = Path(receipt)
    require(not receipt.is_symlink() and receipt.is_file(), "unsafe-path", "A regular wrapper file is required.")
    wrapper = read_json(receipt, trusted_sha256, code="wrapper-tampered")
    schema_check(profile["central"], wrapper)
    require(wrapper["repository"] == REPOSITORY and wrapper["revision"] == expected_revision,
            "wrong-revision", "This receipt is not for the required repository/commit.")
    root = receipt.parent
    require(isinstance(wrapper.get("artifacts"), list), "missing-artifacts", "The wrapper must bind the sidecar and actual artifacts.")
    seen, buffers, protected = {}, {}, [receipt]
    for item in wrapper["artifacts"]:
        path = confined_file(root, item["path"])
        require(item["path"] not in seen, "duplicate-artifact", "Wrapper artifact paths must be unique.")
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == item["sha256"], "artifact-tampered", "A wrapper artifact changed.")
        seen[item["path"]] = item["sha256"]
        buffers[item["path"]] = data
        protected.append(path)
    require("requirement-status.json" in seen and "requirements.md" in seen, "missing-sidecar", "The versioned requirement sidecar and readable report are required.")
    sidecar = parse_json_bytes(buffers["requirement-status.json"])
    schema_check(profile["sidecar.schema"], sidecar)
    moment = current_time(now)
    require(datetime_value(sidecar["generated_at"]) <= moment <= datetime_value(sidecar["review_by"]),
            "review-expired", "The receipt is future-dated or past its explicit review window.")
    request = sidecar["request"]
    require(request["revision"] == expected_revision, "wrong-revision", "The sidecar names an unrelated commit.")
    before_logs = Path(logs or OUTPUT_ROOT / "consumer-probes")
    after_logs = before_logs.with_name("consumer-after")
    output_directory(before_logs, protected)
    output_directory(after_logs, protected)
    source = source_snapshot(source_root, expected_revision, request["tree"], before_logs)
    inputs = Inputs(source_root, root, source, bundled=True)
    expected = assemble(request, source, inputs, profile, sidecar["generated_at"])
    require(sidecar == expected, "sidecar-semantic-drift", "The sidecar's statuses, scope or provenance differ from independently reconstructed evidence.")
    markdown = render_markdown(expected).encode()
    require(buffers["requirements.md"] == markdown, "readable-report-drift", "The readable report misrepresents the machine sidecar.")
    expected_wrapper = wrapper_for(expected, seen["requirement-status.json"], hashlib.sha256(markdown).hexdigest())
    require(wrapper == expected_wrapper, "wrapper-semantic-drift", "The central wrapper does not truthfully represent the sidecar.")
    inputs.unchanged()
    after = source_snapshot(source_root, expected_revision, request["tree"], after_logs)
    require(after == source, "source-changed-during-read", "Source changed while the receipt was being checked.")
    require(digest(receipt) == trusted_sha256 and all(digest(confined_file(root, path)) == expected_hash
            for path, expected_hash in seen.items()), "artifact-changed-during-read", "The receipt bundle changed during verification.")
    return {"integrity_verified": True, "result": wrapper["result"], "revision": expected_revision,
            "full_programme_qualified": False, "institutional_approval": False, "blind_safe": False,
            "requirements": len(sidecar["requirements"]), "artifacts": len(sidecar["artifacts"])}


def invalidate_output(output, revision, now):
    """Replace previous success before a new attempt; never manufacture acceptance."""
    failed = {"schema_version": 1, "repository": REPOSITORY, "revision": revision,
              "generated_at": now.isoformat(), "result": "fail", "checks": [{"name": "receipt-production",
              "result": "fail", "reason": "This attempt has not completed; no requirement acceptance is established."}], "artifacts": []}
    atomic_bytes(output / "verification-receipt.json", json.dumps(failed, indent=2).encode() + b"\n")
    for name in ("requirement-status.json", "requirements.md"):
        path = output / name
        require(not path.is_symlink() and (not path.exists() or (path.is_file() and path.stat().st_nlink == 1)),
                "unsafe-output", "Previous receipt outputs must not alias source files.")
        path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    build = sub.add_parser("produce")
    build.add_argument("--request", type=Path, required=True)
    build.add_argument("--source-root", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("--receipt", type=Path, required=True)
    check.add_argument("--source-root", type=Path, required=True)
    check.add_argument("--expected-revision", required=True)
    check.add_argument("--trusted-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "produce":
            try:
                request = read_json(args.request)
            except ReceiptError:
                output = output_directory(args.output, [args.request])
                invalidate_output(output, "unresolved", current_time())
                raise
            wrapper, sidecar = produce(request, source_root=args.source_root, output=args.output, protected_paths=[args.request])
            print("Receipt produced: " + wrapper["result"] + "; 51 requirement IDs; programme acceptance remains incomplete.")
            return 1 if wrapper["result"] == "fail" else 0
        result = verify_receipt(args.receipt, source_root=args.source_root, expected_revision=args.expected_revision, trusted_sha256=args.trusted_sha256)
        print("Receipt integrity verified; recorded result: " + result["result"] + "; no programme, institutional or blind-delivery approval.")
        return 1 if result["result"] == "fail" else 0
    except (ReceiptError, OSError, ValueError) as exc:
        print("Requirement evidence rejected: " + getattr(exc, "code", "io-or-value-error"), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
