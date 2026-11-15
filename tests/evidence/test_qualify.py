"""Post-build orchestration boundaries; these are synthetic attachment records."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("evidence_qualification", Path(__file__).with_name("qualify.py"))
DRIVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DRIVER)
API = DRIVER.api


class PostBuildEvidenceTests(unittest.TestCase):
    def setUp(self):
        API.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="driver-unit-", dir=API.OUTPUT_ROOT)
        self.root = Path(self.temp.name) / "source"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "output"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n")
        return path

    def reject(self, code, call):
        with self.assertRaises(API.ReceiptError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def declared(self, replay=False):
        path = self.write("build/sidecar.json", {"schema_version": 1,
                          "artifact_kind": "bounded-replay-native-controls" if replay else "synthetic-policy-record",
                          "submission_approved": True})
        if replay:
            return {"replay_corpus": {"sidecar": str(path), "sidecar_sha256": API.digest(path)}}
        return {"submission_policy_corpus": {"report": "build/sidecar.json", "report_sha256": API.digest(path)}}

    def test_policy_and_absolute_replay_paths_attach_only_identity(self):
        self.assertEqual(DRIVER.optional_sidecars({}, self.root), [])
        for replay in (False, True):
            with self.subTest(replay=replay):
                descriptors = DRIVER.optional_sidecars(self.declared(replay), self.root)
                self.assertEqual(descriptors[0]["path"], "build/sidecar.json")
                self.assertIs(descriptors[0]["required"], False)
                self.assertEqual(descriptors[0]["schema_version"], "1")
                self.assertNotIn("submission_approved", descriptors[0])

    def test_explicit_unexecuted_optional_corpus_is_not_an_artifact_declaration(self):
        corpus = {"result": "unexecuted", "reason": "Opt in with --replay-package-cache", "byte_replay_qualified": False}
        self.assertEqual(DRIVER.optional_sidecars({"replay_corpus": corpus}, self.root), [])
        for key, value in (("sidecar", "build/missing.json"), ("sidecar_sha256", "0" * 64)):
            changed = corpus.copy(); changed[key] = value
            self.reject("sidecar-declaration", lambda: DRIVER.optional_sidecars({"replay_corpus": changed}, self.root))

    def test_existing_negative_output_is_preserved_before_probe_or_copy(self):
        marker = self.output / "negative/unrelated-note.txt"
        marker.parent.mkdir(parents=True); marker.write_text("Preserve existing material")
        self.write(DRIVER.NATIVE, {})
        now = API.current_time()
        result = DRIVER.qualify(self.root, self.output, now.isoformat(), (now + DRIVER.timedelta(days=7)).isoformat())
        self.assertFalse(result["passed"])
        self.assertEqual(result["error_code"], "unsafe-output")
        self.assertEqual(marker.read_text(), "Preserve existing material")
        self.assertFalse((self.output / "identity-probes").exists())

    def test_missing_or_changed_declared_sidecars_cannot_be_skipped(self):
        native = self.declared()
        path = self.root / "build/sidecar.json"
        path.write_text("{}")
        self.reject("artifact-tampered", lambda: DRIVER.optional_sidecars(native, self.root))
        path.unlink()
        self.reject("missing-artifact", lambda: DRIVER.optional_sidecars(native, self.root))
        for value in (None, {}, {"report": "build/sidecar.json"}):
            with self.subTest(value=value):
                self.reject("sidecar-declaration", lambda: DRIVER.optional_sidecars({"submission_policy_corpus": value}, self.root))

    def test_absolute_outside_traversal_and_symlink_sidecars_are_rejected(self):
        native = self.declared(True)
        actual = self.root / "build/sidecar.json"
        (self.root / "build/link.json").symlink_to(actual)
        for path in (str(self.root.parent / "outside.json"), "../outside.json", str(self.root / "build/link.json")):
            with self.subTest(path=path):
                native["replay_corpus"]["sidecar"] = path
                self.reject("unsafe-path", lambda: DRIVER.optional_sidecars(native, self.root))

    def test_unknown_version_or_replay_kind_is_not_silently_accepted(self):
        for version in (True, 2, "1", None):
            with self.subTest(version=version):
                path = self.write("build/sidecar.json", {"schema_version": version})
                native = {"submission_policy_corpus": {"report": "build/sidecar.json", "report_sha256": API.digest(path)}}
                self.reject("sidecar-version", lambda: DRIVER.optional_sidecars(native, self.root))
        path = self.write("build/sidecar.json", {"schema_version": 1, "artifact_kind": "unrelated"})
        self.reject("sidecar-kind", lambda: DRIVER.optional_sidecars(
            {"replay_corpus": {"sidecar": str(path), "sidecar_sha256": API.digest(path)}}, self.root))

    def test_missing_native_or_invalid_declared_sidecar_replaces_stale_success(self):
        self.output.mkdir()
        target = self.output / "qualification.json"
        for native in (None, {"submission_policy_corpus": {}}):
            with self.subTest(native=native):
                if native is not None:
                    self.write(DRIVER.NATIVE, native)
                target.write_text('{"passed":true}\n')
                now = API.current_time()
                result = DRIVER.qualify(self.root, self.output, now.isoformat(), (now + DRIVER.timedelta(days=7)).isoformat())
                self.assertIs(result["passed"], False)
                self.assertIs(json.loads(target.read_text())["passed"], False)
                self.assertEqual(result["cases"], [])

    def test_failure_stub_cannot_overwrite_a_declared_optional_input(self):
        self.output.mkdir()
        input_path = self.output / "qualification.json"
        input_path.write_text('{"schema_version":1}\n')
        original = input_path.read_bytes()
        self.write(DRIVER.NATIVE, {"replay_corpus": {"sidecar": str(input_path), "sidecar_sha256": API.digest(input_path)}})
        now = API.current_time()
        self.reject("unsafe-output", lambda: DRIVER.qualify(self.root, self.output, now.isoformat(),
                    (now + DRIVER.timedelta(days=7)).isoformat()))
        self.assertEqual(input_path.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
