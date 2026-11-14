#!/usr/bin/env python3
"""Validate the pinned UMTHESIS bundle and normalize typed configuration.

No network retrieval or rendering occurs. Schema validity does not establish
university approval, output conformance or execution by either document engine.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "contracts" / "thesis" / "v1"
VERSION = "1.0.0"
FORMATS = FormatChecker()


class ContractError(ValueError):
    """Stable error code and a diagnostic that does not echo author values."""

    def __init__(self, code, message):
        self.code = code
        super().__init__(f"{code}: {message}")


@FORMATS.checks("date-time")
def valid_datetime(value):
    if not isinstance(value, str):
        return True
    try:
        shape = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})"
        return bool(re.fullmatch(shape, value)) and datetime.fromisoformat(value).tzinfo is not None
    except ValueError:
        return False


@FORMATS.checks("year-month")
def valid_month(value):
    if not isinstance(value, str):
        return True
    try:
        return bool(re.fullmatch(r"[0-9]{4}-[0-9]{2}", value)) and bool(date.fromisoformat(value + "-01"))
    except ValueError:
        return False


@FORMATS.checks("orcid")
def valid_orcid(value):
    if not isinstance(value, str):
        return True
    if not re.fullmatch(r"[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]", value):
        return False
    digits = value.replace("-", "")
    total = 0
    for digit in digits[:-1]:
        total = (total + int(digit)) * 2
    check = (12 - total % 11) % 11
    return digits[-1] == ("X" if check == 10 else str(check))


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def configuration_digest(configuration):
    return sha256(json.dumps(configuration, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8"))


def parse_json(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ContractError("bundle-invalid", "duplicate JSON object key")
            result[key] = value
        return result

    def reject_constant(_value):
        raise ContractError("invalid-value", "non-finite JSON number")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def read_json(path):
    try:
        return parse_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("bundle-invalid", "missing or malformed JSON input") from exc


def validate(schema, value, *, partial=False):
    def finite(item):
        if isinstance(item, float) and not math.isfinite(item):
            raise ContractError("invalid-value", "non-finite numeric input")
        if isinstance(item, dict):
            for child in item.values():
                finite(child)
        elif isinstance(item, list):
            for child in item:
                finite(child)

    def patch_schema(node):
        result = {key: deepcopy(item) for key, item in node.items() if key != "required"}
        if "properties" in result:
            result["properties"] = {key: patch_schema(item) for key, item in result["properties"].items()}
        return result

    finite(value)
    if partial:
        schema = patch_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FORMATS).iter_errors(value),
                    key=lambda error: (list(map(str, error.path)), error.validator))
    if errors:
        error = errors[0]
        code = {"type": "invalid-type", "additionalProperties": "unknown-key"}.get(error.validator, "invalid-value")
        if error.validator == "format":
            code = {"orcid": "invalid-orcid", "year-month": "invalid-date"}.get(error.validator_value, code)
        if list(error.path)[-1:] in (["month"], ["resubmission_month"]):
            code = "invalid-date"
        path = ".".join(map(str, error.path)) or "configuration"
        raise ContractError(code, f"{path} violates {error.validator}")


def merge_values(base, patch):
    result = deepcopy(base)
    for key, value in patch.items():
        result[key] = (merge_values(result[key], value)
                       if isinstance(result.get(key), dict) and isinstance(value, dict)
                       else deepcopy(value))
    return result


def value_at(value, path):
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


class Bundle:
    def __init__(self, root, expected_digest=None):
        self.root = Path(root).resolve()
        manifest_path = self.root / "manifest.json"
        if manifest_path.is_symlink():
            raise ContractError("bundle-invalid", "manifest must not be a symlink")
        self.manifest = read_json(manifest_path)
        self.digest = sha256(manifest_path.read_bytes())
        if expected_digest is not None and expected_digest != self.digest:
            raise ContractError("wrong-contract", "manifest digest does not match the pin")
        if not isinstance(self.manifest, dict):
            raise ContractError("bundle-invalid", "manifest must be an object")
        if self.manifest.get("contract_version") != VERSION:
            raise ContractError("wrong-contract", "unsupported contract version")
        files = self.manifest.get("files")
        required = {"defaults.json", "profiles.json", "fixtures.json", "requirements.json",
                    "legacy-crosswalk.json", "sources.json", "source-snapshots.json", "compatibility.json"}
        required.update("schemas/" + name + ".schema.json" for name in (
            "manifest", "metadata", "fixture", "fixtures", "requirements", "legacy-crosswalk",
            "sources", "compatibility", "result"))
        if not isinstance(files, dict) or not required <= set(files):
            raise ContractError("bundle-invalid", "required bundle file is not declared")
        actual = {p.relative_to(self.root).as_posix() for p in self.root.rglob("*")
                  if p.is_file() and p != manifest_path}
        if actual != set(files):
            raise ContractError("bundle-invalid", "declared and actual file inventories differ")
        self.schemas = {}
        for name, digest in files.items():
            path = self.root / name
            if (not re.fullmatch(r"[A-Za-z0-9._/-]+", name) or ".." in Path(name).parts
                    or Path(name).is_absolute() or path.is_symlink()
                    or not path.resolve().is_relative_to(self.root)):
                raise ContractError("bundle-invalid", "bundle path escapes its root")
            if not path.is_file() or sha256(path.read_bytes()) != digest:
                raise ContractError("bundle-invalid", f"file missing or digest mismatch: {name}")
            if name.startswith("schemas/") and name.endswith(".schema.json"):
                schema = read_json(path)
                try:
                    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                        raise ValueError("unsupported schema dialect")
                    Draft202012Validator.check_schema(schema)
                    self._check_schema_references(schema)
                except Exception as exc:
                    raise ContractError("bundle-invalid", f"invalid schema: {name}") from exc
                self.schemas[Path(name).stem.removesuffix(".schema")] = schema
        self.defaults = read_json(self.root / "defaults.json")
        self.profiles = read_json(self.root / "profiles.json")
        if not isinstance(self.profiles, dict) or set(self.profiles) != {"default", "draft", "screen", "print"}:
            raise ContractError("bundle-invalid", "all four profiles must be explicitly defined")
        validate(self.schemas["metadata"], self.defaults)
        for profile in self.profiles.values():
            validate(self.schemas["metadata"], profile, partial=True)
        self._check_catalogue()

    @staticmethod
    def _check_schema_references(node):
        if isinstance(node, dict):
            for keyword in ("$ref", "$dynamicRef"):
                if keyword in node and not node[keyword].startswith("#"):
                    raise ContractError("bundle-invalid", "external schema references are forbidden")
            if "format" in node and node["format"] not in FORMATS.checkers:
                raise ContractError("bundle-invalid", "schema format has no installed validator")
            for child in node.values():
                Bundle._check_schema_references(child)
        elif isinstance(node, list):
            for child in node:
                Bundle._check_schema_references(child)

    @staticmethod
    def _unique(rows, field):
        result = {}
        for row in rows:
            if row[field] in result:
                raise ContractError("bundle-invalid", f"duplicate {field}")
            result[row[field]] = row
        return result

    def _check_catalogue(self):
        data = {}
        for name in ("manifest", "requirements", "legacy-crosswalk", "sources", "fixtures", "compatibility"):
            data[name] = read_json(self.root / (name + ".json"))
            try:
                validate(self.schemas[name], data[name])
            except ContractError as exc:
                raise ContractError("bundle-invalid", f"invalid {name} data") from exc
        self.requirements = self._unique(data["requirements"]["requirements"], "id")
        self.sources = self._unique(data["sources"]["sources"], "id")
        self.fixtures = self._unique(data["fixtures"]["fixtures"], "id")
        self.compatibility = data["compatibility"]
        adapters = self._unique(self.compatibility["adapters"], "engine")
        if set(adapters) != {"typst", "latex"}:
            raise ContractError("bundle-invalid", "both adapter boundaries must be declared")
        snapshots = read_json(self.root / "source-snapshots.json")
        if (not isinstance(snapshots, dict)
                or set(snapshots) != {"schema_version", "contract_version", "snapshots"}
                or type(snapshots["schema_version"]) is not int or snapshots["schema_version"] != 1
                or snapshots["contract_version"] != VERSION or not isinstance(snapshots["snapshots"], dict)
                or set(snapshots["snapshots"]) != set(self.sources)):
            raise ContractError("bundle-invalid", "source snapshots must cover the complete ledger")
        source_text = {}
        for identifier, path in snapshots["snapshots"].items():
            if not isinstance(path, str) or path not in self.manifest["files"]:
                raise ContractError("bundle-invalid", "undeclared source snapshot")
            raw = (self.root / path).read_bytes()
            if sha256(raw) != self.sources[identifier]["content_sha256"]:
                raise ContractError("bundle-invalid", "source snapshot digest differs from ledger")
            source_text[identifier] = raw.decode("utf-8")
        catalogue = dict(re.findall(r"^\| ([A-Z]{3}-[0-9]{2}) \| (.*?) \| .*? \|$",
                                    source_text["umthesis-contract"], re.MULTILINE))
        if set(self.requirements) != set(catalogue) or len(catalogue) != 51:
            raise ContractError("bundle-invalid", "requirement IDs differ from the pinned parent contract")
        cases = set()
        for identifier, requirement in self.requirements.items():
            if requirement["outcome"] != catalogue[identifier]:
                raise ContractError("bundle-invalid", "requirement meaning differs from the parent contract")
            if any(ref["source_id"] not in self.sources for ref in requirement["source_refs"]):
                raise ContractError("bundle-invalid", "dangling requirement source reference")
            for case in requirement["acceptance_cases"]:
                if case["id"] in cases or not set(case["fixture_ids"]) <= set(self.fixtures):
                    raise ContractError("bundle-invalid", "duplicate case or dangling fixture reference")
                cases.add(case["id"])
        legacy = self._unique(data["legacy-crosswalk"]["entries"], "legacy_id")
        headings = []
        for source_id in ("legacy-ears-requirements", "legacy-root-tasks"):
            headings.extend(re.findall(r"^### (.*)$", source_text[source_id], re.MULTILINE))
        legacy_ids = set(re.findall(r"R-[A-Z]+(?:-[A-Z]+)*-[0-9]{3}", "\n".join(headings)))
        if set(legacy) != legacy_ids:
            raise ContractError("bundle-invalid", "legacy crosswalk is incomplete or contains unknown IDs")
        for entry in legacy.values():
            if (not set(entry["requirement_ids"]) <= set(self.requirements)
                    or any(ref["source_id"] not in self.sources for ref in entry["legacy_sources"])):
                raise ContractError("bundle-invalid", "dangling legacy crosswalk reference")
        fixture_paths = set()
        for identifier, row in self.fixtures.items():
            path = row["path"]
            if (path not in self.manifest["files"] or path in fixture_paths
                    or row["sha256"] != self.manifest["files"][path]
                    or not set(row["requirements"]) <= set(self.requirements)):
                raise ContractError("bundle-invalid", "invalid fixture path, digest or requirement mapping")
            fixture_paths.add(path)
            fixture = read_json(self.root / path)
            validate(self.schemas["fixture"], fixture)
            if fixture["id"] != identifier or fixture["expected"]["result"] != row["expected_result"]:
                raise ContractError("bundle-invalid", "fixture manifest and contents disagree")
        if fixture_paths != {p for p in self.manifest["files"]
                             if p.startswith("fixtures/") and p.endswith(".json")}:
            raise ContractError("bundle-invalid", "fixture inventory does not cover all specimens")

    def normalize(self, metadata=None, cli=None, explicit=None):
        layers = [layer if layer is not None else {} for layer in (metadata, cli, explicit)]
        for layer in layers:
            validate(self.schemas["metadata"], layer, partial=True)
        selected = self.defaults["layout"]
        for layer in layers:
            selected = layer.get("layout", selected)
        configuration = merge_values(self.defaults, self.profiles[selected])
        for layer in layers:
            configuration = merge_values(configuration, layer)
        validate(self.schemas["metadata"], configuration)
        return {"configuration": configuration, "diagnostics": self._check_configuration(configuration)}

    def _check_configuration(self, config):
        final = config["purpose"] != "draft"
        standards = set(config["pdf_standards"])
        # Each selected profile constrains the effective PDF version. See the
        # dated PDF Association references in docs/thesis-contract.md.
        requires_17 = bool(standards.intersection({"pdf-1.7", "pdf/ua-1", "pdf/a-2a", "pdf/a-3a"}))
        requires_20 = bool(standards.intersection({"pdf-2.0", "pdf/ua-2", "pdf/a-4", "pdf/a-4f"}))
        if ((final and (config["identity"] == "blind-review" or config["output"] != "pdf"))
                or (config["output"] != "pdf" and standards)
                or (requires_17 and requires_20)
                or len([s for s in standards if s.startswith("pdf/a-")]) > 1):
            raise ContractError("invalid-combination", "purpose, identity or output standards conflict")
        required = ["title", "author.student_record_name", "degree.kind", "degree.course",
                    "academic_units", "submission.month", "abstract",
                    "declarations.original_work", "declarations.word_count"]
        diagnostics = []
        for name in required:
            path = "metadata." + name
            value = value_at(config, path)
            missing = value is None or (isinstance(value, str) and not value.strip()) or value == []
            if missing:
                if final:
                    raise ContractError("missing-metadata", path)
                diagnostics.append({"code": "missing-metadata", "path": path})
            elif final and isinstance(value, str) and (
                    value.strip().casefold() in {"your name", "your title", "thesis title",
                        "your thesis title", "your abstract", "author name", "placeholder", "todo", "tbd"}
                    or re.search(r"\b(?:TODO|TBD)\b", value, re.IGNORECASE)):
                raise ContractError("placeholder-metadata", path)
        approvals = []
        if config["language"].split("-")[0] != "en":
            approvals.append("non_english")
            if not config["metadata"].get("english_summary", "").strip():
                if final:
                    raise ContractError("missing-metadata", "metadata.english_summary")
                diagnostics.append({"code": "missing-metadata", "path": "metadata.english_summary"})
        if "joint_award" in config["metadata"]:
            approvals.append("joint_award")
        for key in approvals:
            path = "approval_refs." + key
            if key not in config["approval_refs"]:
                if final:
                    raise ContractError("missing-approval", path)
                diagnostics.append({"code": "missing-approval", "path": path})
            else:
                diagnostics.append({"code": "human-review-required", "path": path})
        resource_ids = set()
        for group in ("resources", "publications", "creative_outputs"):
            ids = [entry["id"] for entry in config["metadata"].get(group, [])]
            if len(ids) != len(set(ids)):
                raise ContractError("invalid-value", f"duplicate metadata.{group} ID")
            if group == "resources":
                resource_ids.update(ids)
        references = [entry["resource_id"] for entry in config["metadata"].get("rights", [])]
        for group in ("publications", "creative_outputs"):
            references.extend(ref for entry in config["metadata"].get(group, [])
                              for ref in entry.get("resource_ids", []))
        if not set(references) <= resource_ids:
            raise ContractError("invalid-value", "unresolved metadata resource reference")
        return diagnostics

    def parse_cli(self, arguments):
        patch, seen = {}, set()
        for argument in arguments:
            key, separator, raw = argument.partition("=")
            if not separator or not key or any(
                    key == old or key.startswith(old + ".") or old.startswith(key + ".") for old in seen):
                raise ContractError("invalid-value", "duplicate or overlapping CLI assignment")
            seen.add(key)
            schema = self.schemas["metadata"]
            parts = key.split(".")
            for part in parts:
                if part not in schema.get("properties", {}):
                    raise ContractError("unknown-key", "unknown CLI configuration path")
                schema = schema["properties"][part]
            kind = schema.get("type")
            if kind == "string" or "const" in schema:
                value = raw
            elif isinstance(kind, list) and "string" in kind and raw != "null":
                value = raw
            else:
                try:
                    value = parse_json(raw)
                except json.JSONDecodeError as exc:
                    raise ContractError("invalid-type", "CLI value must use its declared JSON type") from exc
            validate(schema, value, partial=True)
            target = patch
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
        validate(self.schemas["metadata"], patch, partial=True)
        return patch

    def verify_fixtures(self):
        observations = []
        for identifier, entry in self.fixtures.items():
            fixture = read_json(self.root / entry["path"])
            expected = fixture["expected"]
            try:
                result = self.normalize(fixture["metadata"], self.parse_cli(fixture["cli"]), fixture["explicit"])
            except ContractError as exc:
                if expected["result"] != "invalid" or expected.get("error_code") != exc.code:
                    raise ContractError("bundle-invalid", f"unexpected negative fixture outcome: {identifier}") from exc
                observed = "invalid"
            else:
                if expected["result"] != "valid":
                    raise ContractError("bundle-invalid", f"negative fixture was accepted: {identifier}")
                for path, value in expected["values"].items():
                    current = result["configuration"]
                    for part in path.split("."):
                        if not isinstance(current, dict) or part not in current:
                            raise ContractError("bundle-invalid", f"missing fixture oracle path: {identifier}")
                        current = current[part]
                    if current != value:
                        raise ContractError("bundle-invalid", f"fixture semantic oracle mismatch: {identifier}")
                if {item["code"] for item in result["diagnostics"]} != set(expected["diagnostic_codes"]):
                    raise ContractError("bundle-invalid", f"fixture diagnostics mismatch: {identifier}")
                observed = "valid"
            observations.append({"fixture_id": identifier, "sha256": entry["sha256"],
                                 "expected": expected["result"], "observed": observed,
                                 "regression_result": "executed-pass"})
        return observations

    def validate_result(self, result, expected_revision=None, artifact_root=None):
        if not isinstance(result, dict):
            raise ContractError("invalid-type", "result must be an object")
        if result.get("contract_version") != VERSION or result.get("contract_sha256") != self.digest:
            raise ContractError("wrong-contract", "result belongs to a different contract")
        validate(self.schemas["result"], result)
        fixture = self.fixtures.get(result["fixture"]["id"])
        if fixture is None or fixture["sha256"] != result["fixture"]["sha256"]:
            raise ContractError("stale-fixture", "result fixture identity or digest is stale")
        if expected_revision is not None and result["source"]["revision"] != expected_revision:
            raise ContractError("invalid-value", "result belongs to a different source revision")
        body = read_json(self.root / fixture["path"])
        try:
            config = self.normalize(body["metadata"], self.parse_cli(body["cli"]), body["explicit"])["configuration"]
        except ContractError:
            config = None
        expected_hash = configuration_digest(config) if config is not None else None
        reported = result["normalized_configuration"]
        if reported is not None:
            validate(self.schemas["metadata"], reported)
        reported_hash = configuration_digest(reported) if reported is not None else None
        if (reported != config or reported_hash != expected_hash
                or result["configuration_sha256"] != reported_hash):
            raise ContractError("invalid-value", "result configuration does not match its fixture")
        adapter = next(a for a in self.compatibility["adapters"] if a["engine"] == result["engine"]["name"])
        if result["engine"]["adapter_version"] != self.compatibility["adapter_api_version"]:
            raise ContractError("invalid-value", "adapter interface is stale")
        paths = set()
        for artifact in result["artifacts"]:
            path = Path(artifact["path"])
            if (artifact_root is None or path.is_absolute() or ".." in path.parts
                    or "\\" in artifact["path"] or path.as_posix() in paths):
                raise ContractError("invalid-value", "artifact requires a unique relative path and root")
            root = Path(artifact_root).resolve()
            target = root / path
            if (target.is_symlink() or not target.resolve().is_relative_to(root)
                    or not target.is_file() or sha256(target.read_bytes()) != artifact["sha256"]):
                raise ContractError("invalid-value", "artifact is missing, unsafe or has a stale digest")
            paths.add(path.as_posix())
        seen = set()
        for item in result["requirements"]:
            identifier = item["requirement_id"]
            if identifier in seen or identifier not in fixture["requirements"]:
                raise ContractError("invalid-value", "unknown, duplicate or unrelated result requirement")
            seen.add(identifier)
            allowed_sources = {r["source_id"] for r in self.requirements[identifier]["source_refs"]}
            if not set(item["source_refs"]) <= allowed_sources:
                raise ContractError("invalid-value", "unrelated result source rule")
            executed = item["result"] in {"executed-pass", "executed-fail"}
            if executed and (adapter["implementation_state"] != "implemented"
                             or item["implementation_state"] != "implemented"
                             or expected_revision is None or result["source"]["dirty"]
                             or not item["command"] or item["exit_code"] is None
                             or not item["evidence_refs"]):
                raise ContractError("invalid-value", "executed result lacks adapter, source or execution evidence")
            if ((not executed and item["exit_code"] is not None)
                    or (item["result"] == "executed-pass" and item["exit_code"] != 0)
                    or (item["result"] == "executed-fail" and item["exit_code"] == 0)):
                raise ContractError("invalid-value", "result state and exit code conflict")
            if (item["applicability"] == "not-applicable") != (item["result"] == "not-applicable"):
                raise ContractError("invalid-value", "applicability and result state conflict")
            if (item["result"] == "not-applicable"
                    and self.requirements[identifier]["applicability"]["predicate"] == "always"):
                raise ContractError("invalid-value", "mandatory contract obligation cannot be waived")
            if not set(item["evidence_refs"]) <= paths:
                raise ContractError("invalid-value", "result evidence is not bound to a retained artifact")
        if seen != set(fixture["requirements"]):
            raise ContractError("invalid-value", "result omits a declared fixture requirement")
        for name in ("dependencies", "fonts", "toolchain"):
            ref = result["manifest_refs"][name]
            if ref is not None and ref not in paths:
                raise ContractError("invalid-value", "manifest reference has no bound artifact")
        if not set(result["manifest_refs"]["validators"]) <= paths:
            raise ContractError("invalid-value", "validator reference has no bound artifact")
        for exception in result["exceptions"]:
            if exception["requirement_id"] not in seen:
                raise ContractError("invalid-value", "exception refers to an unrelated requirement")


def load_bundle(root=DEFAULT_BUNDLE, expected_digest=None):
    return Bundle(Path(root), expected_digest=expected_digest)


def write_json(path, value):
    serialized = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument("--contract-sha256", help="Require this exact manifest SHA-256")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="Validate the bundle and configuration fixtures")
    check.add_argument("--report", type=Path)
    normalize = commands.add_parser("normalize", help="Resolve typed configuration; does not render")
    normalize.add_argument("--metadata", type=Path)
    normalize.add_argument("--explicit", type=Path)
    normalize.add_argument("--set", action="append", default=[], dest="overrides")
    normalize.add_argument("--output", type=Path)
    result = commands.add_parser("validate-result", help="Validate adapter result identity and artifacts")
    result.add_argument("result", type=Path)
    result.add_argument("--expected-revision", required=True)
    result.add_argument("--artifacts-root", type=Path)
    args = parser.parse_args(argv)
    try:
        bundle = load_bundle(args.contract, args.contract_sha256)
        if args.command == "check":
            observations = bundle.verify_fixtures()
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                      text=True, capture_output=True, check=True).stdout.strip()
            dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                        text=True, capture_output=True, check=True).stdout)
            report = {"schema_version": 1, "scope": "contract-schema-api",
                      "contract_version": VERSION, "contract_sha256": bundle.digest,
                      "source_revision": revision, "source_dirty": dirty,
                      "python_version": sys.version.split()[0],
                      "requirement_count": len(bundle.requirements), "fixtures": observations,
                      "document_adapter_execution": {"typst": "unexecuted", "latex": "unexecuted"},
                      "institutional_approval": "unverified", "result": "pass"}
            write_json(args.report, report)
        elif args.command == "normalize":
            layers = []
            for path in (args.metadata, args.explicit):
                layer = read_json(path) if path else {}
                if not isinstance(layer, dict):
                    raise ContractError("invalid-type", "configuration file must be an object")
                layers.append(layer)
            value = bundle.normalize(layers[0], bundle.parse_cli(args.overrides), layers[1])
            value.update(contract_version=VERSION, contract_sha256=bundle.digest,
                         configuration_sha256=configuration_digest(value["configuration"]))
            write_json(args.output, value)
        else:
            bundle.validate_result(read_json(args.result), args.expected_revision, args.artifacts_root)
            print("Result identity, state and artifact bindings are valid; no new execution is implied.")
        return 0
    except (ContractError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
