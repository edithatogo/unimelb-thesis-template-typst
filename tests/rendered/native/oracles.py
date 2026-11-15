"""Fixed native probes and independent literal expectations for the bounded corpus."""
from __future__ import annotations

import json
from pathlib import Path
import runpy

API = runpy.run_path(
    str(Path(__file__).resolve().parents[3] / "scripts/native_evidence.py"),
    run_name="scripts.native_evidence",
)
EvidenceError = API["EvidenceError"]
strict_json = API["strict_json"]
validate_dependencies = API["validate_dependencies"]
validate_schema_result = API["validate_eval"]


def validate_eval(text, schema_name):
    schema = strict_json(Path(__file__).with_name("eval-results.schema.json").read_text(encoding="utf-8"))
    if schema_name not in schema["$defs"]:
        raise EvidenceError("unknown-schema", "No required-result schema is registered")
    selected = {"$ref": "#/$defs/" + schema_name, "$defs": schema["$defs"]}
    return validate_schema_result(text, selected)


EXPRESSIONS = {
    "assertion": "query(<native-metadata>).len() == 1",
    "metadata": "query(<native-metadata>).map(it => it.value)",
    "headings": "query(heading).map(it => (level: it.level, body: it.body.text))",
    "references": "query(ref).map(it => (target: repr(it.target)))",
    "optional": "query(<native-metadata>).first().value",
    "false": "false",
    "null": "none",
    "empty_string": '""',
    "empty_array": "()",
    "empty_object": "(:)",
    "failed_assertion": 'assert(false, message: "NATIVE REQUIRED ASSERTION FAILED")',
}

# Literal expectations are independent of the compiled fixture/data file.
EXPECTED_RECORD = {
    "title": "NATIVE METADATA TITLE", "optional_false": False,
    "optional_null": None, "optional_empty": "", "optional_array": [],
    "literal": "#panic(123)", "optional_object": {}, "optional_zero": 0,
}


def specimens():
    rows = (
        ("assertion", "assertion", "assertion", "valid", True, False),
        ("metadata", "metadata", "metadata", "valid", [EXPECTED_RECORD], False),
        ("headings", "headings", "headings", "valid",
         [{"level": 1, "body": "NATIVE SEMANTIC CHAPTER"}], False),
        ("references", "references", "references", "valid", [{"target": "<native-heading>"}], False),
        ("optional", "optional", "optional_record", "valid", EXPECTED_RECORD, False),
        ("required-false", "false", "assertion", "valid", False, True),
        ("required-null", "null", "assertion", "valid", None, True),
        ("required-empty-string", "empty_string", "text", "valid", "", True),
        ("required-empty-array", "empty_array", "metadata", "valid", [], True),
        ("required-empty-object", "empty_object", "optional_record", "valid", {}, True),
        ("missing-metadata", "metadata", "metadata", "missing", [], True),
        ("duplicate-metadata", "metadata", "metadata", "duplicate", [EXPECTED_RECORD, EXPECTED_RECORD], True),
        ("malformed-metadata", "metadata", "metadata", "malformed", [{"title": False}], True),
    )
    return [dict(zip(("id", "expression", "schema", "mode", "expected", "expect_rejection"), row)) for row in rows]


def check_eval(case, raw):
    """An expected rejected result is a passing regression, never valid evidence."""
    observed = strict_json(raw)
    same = json.dumps(observed, sort_keys=True) == json.dumps(case["expected"], sort_keys=True)
    code = None
    try:
        validate_eval(raw, case["schema"])
    except EvidenceError as exc:
        code = exc.code
    wanted = "schema-invalid" if case["expect_rejection"] else None
    checks = [
        {"name": "Exact typed native result", "passed": same},
        {"name": "Declared required-result schema", "passed": code == wanted},
    ]
    return {
        "passed": all(item["passed"] for item in checks), "checks": checks,
        "semantic_status": "rejected" if code else "accepted", "rejection_code": code,
        "native_value": observed,
    }

