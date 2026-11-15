"""Validate native semantic JSON and source/output-bound dependency captures.

This module does not supervise commands or certify fonts, document policy or replay.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


class EvidenceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def strict_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise EvidenceError("invalid-json", "Duplicate JSON object key")
            result[key] = value
        return result

    def constant(value):
        raise EvidenceError("invalid-json", "Nonfinite JSON value")

    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise EvidenceError("invalid-json", "Nonfinite JSON value")
        return number

    try:
        return json.loads(
            text, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_float,
        )
    except (json.JSONDecodeError, UnicodeError, TypeError) as exc:
        raise EvidenceError("invalid-json", "Malformed JSON evidence") from exc


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_eval(text, schema):
    """Apply the caller's fixed local result schema without fetching external refs."""
    def local_refs(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("$ref", "$dynamicRef") and (not isinstance(item, str) or not item.startswith("#")):
                    raise EvidenceError("invalid-schema", "Native result schemas must use local references")
                local_refs(item)
        elif isinstance(value, list):
            for item in value:
                local_refs(item)

    local_refs(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise EvidenceError("invalid-schema", "Malformed native result schema") from exc
    value = strict_json(text)
    errors = list(Draft202012Validator(schema).iter_errors(value))
    if errors:
        raise EvidenceError("schema-invalid", "Native result does not satisfy its declared schema")
    return value


def validate_dependencies(text, *, root, details, commands, approved_external_roots=None,
                          required_inputs=()):
    """Bind paths to one successful PDF compile; this is not a complete replay lock."""
    root = Path(root).resolve()
    approved_external_roots = approved_external_roots or {}
    if (not isinstance(commands, list)
            or any(not isinstance(item, dict) or not isinstance(item.get("command"), list)
                   or not item["command"] or any(type(arg) is not str for arg in item["command"])
                   for item in commands)):
        raise EvidenceError("compile-not-successful", "Command evidence is malformed")
    records = [item for item in commands if isinstance(item.get("command"), list)
               and len(item["command"]) >= 4 and Path(item["command"][0]).name == "typst"
               and item["command"][1] == "compile"]
    if len(records) != 1:
        raise EvidenceError("compile-not-successful", "Expected exactly one successful compile record")
    compile_record = records[0]
    if (type(compile_record.get("exit_code")) is not int or compile_record["exit_code"] != 0
            or compile_record.get("timed_out") is not False or compile_record.get("error")
            or compile_record.get("cleanup_error") or compile_record.get("cwd") != str(root)):
        raise EvidenceError("compile-not-successful", "Dependency paths cannot certify an unsuccessful compile")
    if (not isinstance(details, dict)
            or any(type(details.get(key)) is not str or not details[key].strip() for key in ("source", "pdf"))
            or any(type(details.get(key)) is not str or not re.fullmatch(r"[0-9a-f]{64}", details[key])
                   for key in ("source_sha256", "pdf_sha256"))):
        raise EvidenceError("invalid-compile-evidence", "Required source/output identities are absent or malformed")
    native = strict_json(text)
    if not isinstance(native, dict) or set(native) != {"inputs", "outputs"}:
        raise EvidenceError("invalid-dependencies", "Expected native input/output path lists")
    if native["outputs"] is None or native["outputs"] == []:
        raise EvidenceError("missing-outputs", "Native dependencies do not establish a successful output")
    for key in ("inputs", "outputs"):
        values = native[key]
        if not isinstance(values, list) or not values or any(type(v) is not str or not v.strip() for v in values):
            raise EvidenceError("invalid-dependencies", "Dependency entries must be nonempty path strings")

    def resolve(value):
        path = Path(value)
        return (path if path.is_absolute() else root / path).resolve()

    def identity(path):
        if path.is_relative_to(root):
            return "project:" + path.relative_to(root).as_posix()
        for label, directory in approved_external_roots.items():
            if type(label) is not str or not re.fullmatch(r"[a-z0-9-]+", label):
                raise EvidenceError("unapproved-path", "External roots need neutral public identifiers")
            directory = Path(directory).resolve()
            if path.is_relative_to(directory):
                return label + ":" + path.relative_to(directory).as_posix()
        raise EvidenceError("unapproved-path", "Dependency is outside the project and declared package roots")

    source = resolve(details["source"])
    output = resolve(details["pdf"])
    if not source.is_relative_to(root) or not output.is_relative_to(root):
        raise EvidenceError("unapproved-path", "Source/output must belong to the project")
    command = compile_record["command"]
    if resolve(command[-2]) != source:
        raise EvidenceError("wrong-source", "Compile record describes a different source")
    if resolve(command[-1]) != output:
        raise EvidenceError("wrong-output", "Compile record describes a different output")
    inputs = [resolve(value) for value in native["inputs"]]
    outputs = [resolve(value) for value in native["outputs"]]
    if len(set(inputs)) != len(inputs) or len(set(outputs)) != len(outputs):
        raise EvidenceError("duplicate-dependency", "Duplicate normalized dependency path")
    if outputs != [output]:
        raise EvidenceError("wrong-output", "Native output differs from the verified PDF")
    if set(inputs).intersection(outputs):
        raise EvidenceError("invalid-dependencies", "A verified output cannot also be a stale input")
    if source not in inputs or not {resolve(value) for value in required_inputs}.issubset(inputs):
        raise EvidenceError("missing-input", "Native inventory omits a required source/input")
    names = {path: identity(path) for path in [*inputs, *outputs]}
    if any(not path.is_file() for path in [*inputs, *outputs]):
        raise EvidenceError("missing-artifact", "Native inventory names an absent file")
    if digest(source) != details["source_sha256"]:
        raise EvidenceError("source-hash-mismatch", "Source no longer matches the compile evidence")
    if digest(output) != details["pdf_sha256"]:
        raise EvidenceError("output-hash-mismatch", "PDF no longer matches the compile evidence")
    if (type(compile_record.get("log")) is not str
            or type(compile_record.get("log_sha256")) is not str):
        raise EvidenceError("compile-not-successful", "Compile log identity is missing")
    log = resolve(compile_record["log"])
    if not log.is_relative_to(root) or not log.is_file() or digest(log) != compile_record["log_sha256"]:
        raise EvidenceError("compile-not-successful", "Compile log is missing or differs from its record")
    if (command.count("--deps-format") != 1 or command.index("--deps-format") + 1 >= len(command)
            or command[command.index("--deps-format") + 1] != "json"):
        raise EvidenceError("invalid-dependencies", "Compile did not request native JSON dependencies")
    if command.count("--deps") != 1 or command.index("--deps") + 1 >= len(command):
        raise EvidenceError("invalid-dependencies", "Compile did not request a dependency report")
    dependency_path = resolve(command[command.index("--deps") + 1])
    if (not dependency_path.is_relative_to(root) or not dependency_path.is_file()
            or dependency_path.read_bytes() != text.encode("utf-8")):
        raise EvidenceError("dependency-hash-mismatch", "Native capture differs from the compile's dependency file")
    return {
        "schema_version": 1,
        "artifact_kind": "validated-dependency-inventory",
        "scope": "Native paths and observed post-compile content hashes; not a complete replay lock",
        "native_report_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "native_report_bytes": len(text.encode("utf-8")),
        "native_report_retained_verbatim": False,
        "external_paths_sanitized": True,
        "source": {"path": names[source], "sha256": details["source_sha256"]},
        "inputs": [{"path": names[path], "sha256_observed_after_compile": digest(path)} for path in inputs],
        "outputs": [{"path": names[path], "sha256": digest(path)} for path in outputs],
        "compile_log_sha256": compile_record["log_sha256"],
        "native_entries_are_paths": True,
        "font_inventory_included": False,
        "replay_qualified": False,
    }
