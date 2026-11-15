"""Evidence-contract unit controls; synthetic files are not real compiler proof."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
API = runpy.run_path(str(ROOT / "tests/rendered/native/oracles.py"))
Error = API["EvidenceError"]
SPEC = importlib.util.spec_from_file_location("native_evidence_verifier", ROOT / "scripts/verify.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="native-unit-", dir=ROOT / "build")
        self.parent = Path(self.temp.name)
        self.root = self.parent / "project"
        self.root.mkdir()
        for name, value in {"source.typ": "Synthetic source", "data.json": "{}",
                            "output.pdf": "Synthetic unit bytes, not PDF evidence",
                            "compile.log": "Synthetic successful command record"}.items():
            (self.root / name).write_text(value)
        self.deps = self.root / "dependencies.json"
        self.native = {"inputs": ["source.typ", "data.json"], "outputs": ["output.pdf"]}
        self.details = {"source": "source.typ", "pdf": "output.pdf",
                        "source_sha256": self.hash("source.typ"), "pdf_sha256": self.hash("output.pdf")}
        self.commands = [{"command": ["typst", "compile", "--deps", str(self.deps),
                                      "--deps-format", "json", "source.typ", "output.pdf"],
                          "cwd": str(self.root), "exit_code": 0, "timed_out": False,
                          "log": "compile.log", "log_sha256": self.hash("compile.log")}]

    def tearDown(self):
        self.temp.cleanup()

    def hash(self, name):
        return hashlib.sha256((self.root / name).read_bytes()).hexdigest()

    def validate(self, native=None, **options):
        raw = json.dumps(self.native if native is None else native)
        self.deps.write_text(raw)
        return API["validate_dependencies"](raw, root=self.root, details=self.details,
                                            commands=self.commands, **options)

    def rejected(self, code, callback):
        with self.assertRaises(Error) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    def test_required_false_null_empty_values_are_rejected_by_their_schema(self):
        for raw, schema in (("false", "assertion"), ("null", "assertion"), ('""', "text"),
                            ('"   "', "text"), ("[]", "metadata"), ("{}", "optional_record")):
            with self.subTest(raw=raw):
                self.rejected("schema-invalid", lambda: API["validate_eval"](raw, schema))

    def test_optional_values_and_literal_code_are_preserved_exactly(self):
        data = json.loads((ROOT / "tests/rendered/native/data.json").read_text())
        observed = API["validate_eval"](json.dumps(data), "optional_record")
        self.assertEqual(json.dumps(observed, sort_keys=True), json.dumps(data, sort_keys=True))
        self.assertIs(observed["optional_false"], False)
        self.assertIsNone(observed["optional_null"])
        self.assertEqual(observed["optional_zero"], 0)
        self.assertEqual(observed["literal"], "#panic(123)")

    def test_oracle_does_not_treat_false_and_zero_as_the_same_value(self):
        case = next(case for case in API["specimens"]() if case["id"] == "optional")
        changed = dict(API["EXPECTED_RECORD"], optional_false=0)
        result = API["check_eval"](case, json.dumps(changed))
        self.assertFalse(result["passed"])

    def test_expected_semantic_rejection_remains_rejected_evidence(self):
        case = next(case for case in API["specimens"]() if case["id"] == "required-false")
        result = API["check_eval"](case, "false")
        self.assertTrue(result["passed"])
        self.assertEqual(result["semantic_status"], "rejected")
        self.assertFalse(API["check_eval"](case, "true")["passed"])

    def test_missing_duplicate_and_malformed_required_metadata_are_rejected(self):
        valid = json.loads((ROOT / "tests/rendered/native/data.json").read_text())
        for value in ([], [valid, valid], [{"title": False}], [dict(valid, title=None)]):
            with self.subTest(value=value):
                self.rejected("schema-invalid", lambda: API["validate_eval"](json.dumps(value), "metadata"))

    def test_malformed_duplicate_key_and_nonfinite_json_are_rejected(self):
        for raw in ("{", '{"x":1,"x":2}', "NaN", "Infinity", "true false"):
            with self.subTest(raw=raw):
                self.rejected("invalid-json", lambda: API["strict_json"](raw))

    def test_exponent_overflow_cannot_become_nonfinite_evidence(self):
        for raw in ("1e999", "-1e999", "[1e999]", '{"value":-1e999}'):
            with self.subTest(raw=raw):
                self.rejected("invalid-json", lambda: API["strict_json"](raw))
                self.rejected("invalid-json", lambda: API["validate_schema_result"](raw, True))
        self.assertEqual(API["strict_json"]("1e2"), 100.0)
        self.assertEqual(API["validate_schema_result"]("-1e2", {"type": "number"}), -100.0)

    def test_unregistered_schema_cannot_relax_a_required_result(self):
        self.rejected("unknown-schema", lambda: API["validate_eval"]("false", "optional_anything"))

    def test_malformed_schemas_are_rejected(self):
        for schema in (None, {"type": "unknown-json-type"}):
            with self.subTest(schema=schema):
                self.rejected("invalid-schema", lambda: API["validate_schema_result"]("true", schema))

    def test_external_static_and_dynamic_schema_references_never_fetch(self):
        for keyword in ("$ref", "$dynamicRef"):
            with self.subTest(keyword=keyword), patch("urllib.request.urlopen", side_effect=AssertionError("Network resolution must not run")):
                self.rejected("invalid-schema", lambda: API["validate_schema_result"](
                    "true", {"allOf": [{keyword: "https://example.invalid/native-schema"}]}))

    def test_dependencies_bind_source_output_and_observed_input_hashes(self):
        value = self.validate(required_inputs=["source.typ", "data.json"])
        self.assertEqual(value["outputs"], [{"path": "project:output.pdf", "sha256": self.hash("output.pdf")}])
        self.assertEqual(value["source"]["sha256"], self.hash("source.typ"))
        self.assertTrue(value["native_entries_are_paths"])
        self.assertFalse(value["replay_qualified"])
        self.assertFalse(value["font_inventory_included"])

    def test_outputs_null_or_empty_cannot_establish_success(self):
        for outputs in (None, []):
            with self.subTest(outputs=outputs):
                self.rejected("missing-outputs", lambda: self.validate(dict(self.native, outputs=outputs)))

    def test_native_entries_must_be_paths_not_claimed_hash_objects(self):
        for value in ({"sha256": "0" * 64}, False, None, 7, ""):
            with self.subTest(value=value):
                self.rejected("invalid-dependencies", lambda: self.validate(dict(self.native, inputs=[value])))

    def test_native_shape_cannot_omit_or_add_fields(self):
        for value in ({"inputs": ["source.typ"]}, dict(self.native, passed=True), [self.native]):
            with self.subTest(value=value):
                self.rejected("invalid-dependencies", lambda: self.validate(value))

    def test_wrong_output_is_rejected_before_trusting_any_file(self):
        self.rejected("wrong-output", lambda: self.validate(dict(self.native, outputs=["another.pdf"])))

    def test_wrong_or_omitted_source_and_required_input_are_rejected(self):
        self.rejected("missing-input", lambda: self.validate(dict(self.native, inputs=["data.json"])))
        self.rejected("missing-input", lambda: self.validate(required_inputs=["missing-required.typ"]))
        self.commands[0]["command"][-2] = "another.typ"
        self.rejected("wrong-source", self.validate)

    def test_duplicate_normalized_paths_are_rejected(self):
        self.rejected("duplicate-dependency", lambda: self.validate(dict(self.native, inputs=["source.typ", "./source.typ"])))

    def test_failed_timed_out_or_duplicate_compile_records_are_rejected(self):
        original = deepcopy(self.commands)
        for patch in ({"exit_code": 1}, {"exit_code": False}, {"timed_out": True}, {"cleanup_error": "failed"}):
            self.commands = [dict(original[0], **patch)]
            with self.subTest(patch=patch):
                self.rejected("compile-not-successful", self.validate)
        self.commands = original + original
        self.rejected("compile-not-successful", self.validate)

    def test_missing_or_malformed_compile_identity_is_rejected(self):
        for name in ("source", "pdf", "source_sha256", "pdf_sha256"):
            old = self.details.pop(name)
            with self.subTest(name=name):
                self.rejected("invalid-compile-evidence", self.validate)
            self.details[name] = old
        self.commands = [None]
        self.rejected("compile-not-successful", self.validate)

    def test_source_and_output_hash_mismatch_are_rejected(self):
        for key, code in (("source_sha256", "source-hash-mismatch"), ("pdf_sha256", "output-hash-mismatch")):
            old = self.details[key]
            self.details[key] = "0" * 64
            with self.subTest(key=key):
                self.rejected(code, self.validate)
            self.details[key] = old

    def test_missing_input_or_output_artifact_is_rejected(self):
        self.rejected("missing-artifact", lambda: self.validate(dict(self.native, inputs=["source.typ", "missing.json"])))
        (self.root / "output.pdf").unlink()
        self.rejected("missing-artifact", self.validate)

    def test_unapproved_external_dependency_is_rejected(self):
        external = self.parent / "external.typ"
        external.write_text("Synthetic external dependency")
        self.rejected("unapproved-path", lambda: self.validate(dict(self.native, inputs=["source.typ", str(external)])))

    def test_approved_external_paths_are_sanitized_and_hashed(self):
        external = self.parent / "cache"
        external.mkdir()
        source = external / "module.typ"
        source.write_text("Synthetic package file")
        value = self.validate(dict(self.native, inputs=["source.typ", str(source)]),
                              approved_external_roots={"package-cache": external})
        self.assertEqual(value["inputs"][1]["path"], "package-cache:module.typ")
        self.assertNotIn(str(self.parent), json.dumps(value))

    def test_compile_log_and_native_capture_must_match_their_records(self):
        (self.root / "compile.log").write_text("Changed command log")
        self.rejected("compile-not-successful", self.validate)
        self.commands[0]["log_sha256"] = self.hash("compile.log")
        raw = json.dumps(self.native)
        self.deps.write_text(raw + "\n")
        self.rejected("dependency-hash-mismatch", lambda: API["validate_dependencies"](
            raw, root=self.root, details=self.details, commands=self.commands))

    def test_native_capture_binding_preserves_exact_newline_bytes(self):
        raw = json.dumps(self.native, indent=2)
        self.deps.write_bytes(raw.replace("\n", "\r\n").encode("utf-8"))
        self.rejected("dependency-hash-mismatch", lambda: API["validate_dependencies"](
            raw, root=self.root, details=self.details, commands=self.commands))

    def test_explicit_json_dependency_flags_are_required(self):
        self.commands[0]["command"].remove("--deps-format")
        self.rejected("invalid-dependencies", self.validate)

    def test_output_cannot_also_be_an_old_input(self):
        self.rejected("invalid-dependencies", lambda: self.validate(dict(self.native, inputs=["source.typ", "output.pdf"])))

    def capture(self):
        with patch.object(VERIFY, "ROOT", self.root), patch.object(VERIFY, "NATIVE_EVIDENCE", str(ROOT / "scripts/native_evidence.py")):
            return VERIFY.capture_dependencies(self.deps, self.details, self.commands)

    def test_capture_requires_an_actual_dependency_file(self):
        with self.assertRaisesRegex(VERIFY.VerificationError, "no native dependency file"):
            self.capture()

    def test_public_capture_is_transformed_and_bound_to_original_bytes(self):
        raw = json.dumps(self.native).encode("utf-8")
        self.deps.write_bytes(raw)
        receipt = self.capture()
        observed = json.loads(self.deps.read_text())
        self.assertEqual(observed["artifact_kind"], "validated-dependency-inventory")
        self.assertEqual(receipt["native_report_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(receipt["sha256"], self.hash("dependencies.json"))
        self.assertFalse(receipt["native_report_retained_verbatim"])
        self.assertNotIn(str(self.parent), json.dumps(observed))

    def test_rejected_public_capture_removes_unapproved_host_paths(self):
        raw = json.dumps(dict(self.native, inputs=["source.typ", str(self.parent / "private-file")]))
        self.deps.write_text(raw)
        with self.assertRaises(ValueError):
            self.capture()
        observed = json.loads(self.deps.read_text())
        self.assertEqual(observed["artifact_kind"], "rejected-native-dependency-inventory")
        self.assertFalse(observed["successful_compile_inventory"])
        self.assertNotIn(str(self.parent), json.dumps(observed))
        self.assertEqual(observed["native_report_sha256"], hashlib.sha256(raw.encode()).hexdigest())

    def test_malformed_capture_cannot_reuse_a_successful_receipt(self):
        for raw in (b"{", b"\xff", b'{"inputs":[],"outputs":null}'):
            with self.subTest(raw=raw):
                self.deps.write_bytes(raw)
                with self.assertRaises((ValueError, UnicodeError)):
                    self.capture()
                observed = json.loads(self.deps.read_text())
                self.assertEqual(observed["artifact_kind"], "rejected-native-dependency-inventory")
                self.assertFalse(observed["successful_compile_inventory"])

    def test_missing_tool_leaves_failed_report_and_removes_seeded_outputs(self):
        output = ROOT / "build" / (self.parent.name + "-capture")
        output.mkdir()
        self.addCleanup(lambda: shutil.rmtree(output))
        (output / "native").mkdir()
        for name in ("document.pdf", "failed.pdf", "document.dependencies.json", "optional.eval.json", "supplement.json"):
            (output / "native" / name).write_text("OLD_SUCCESS")
        (output / "report.json").write_text('{"passed":true}')
        report = {"passed": False}
        with patch.object(VERIFY, "ROOT", ROOT), patch.object(VERIFY, "OUTPUT", output), patch.object(VERIFY.shutil, "which", return_value=None):
            with self.assertRaisesRegex(VERIFY.VerificationError, "Required native-evidence executable not found"):
                VERIFY.verify_native_evidence(report)
        observed = json.loads((output / "report.json").read_text())
        self.assertFalse(observed["passed"])
        self.assertEqual(observed["native_evidence_corpus"]["result"], "fail")
        self.assertEqual(list((output / "native").iterdir()), [])

    def test_relative_explicit_package_roots_use_the_compiler_working_directory(self):
        with patch.object(VERIFY, "ROOT", self.root), patch.dict(VERIFY.os.environ, {
            "TYPST_PACKAGE_CACHE_PATH": "cache", "TYPST_PACKAGE_PATH": "local-packages",
        }):
            observed = VERIFY.native_package_roots()
        self.assertEqual(observed["package-cache"], self.root / "cache")
        self.assertEqual(observed["package-local"], self.root / "local-packages")


if __name__ == "__main__":
    unittest.main()
