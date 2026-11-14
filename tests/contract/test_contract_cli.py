"""Exercise the public contract CLI in bounded, real Python subprocesses.

Inputs and retained files are synthetic. Successful result validation is not
renderer execution or institutional approval. Child processes are not claimed
as coverage unless the caller independently enables subprocess measurement.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "thesis_contract.py"
BUNDLE = ROOT / "contracts" / "thesis" / "v1"
SENTINEL = "SYNTHETIC_AUTHOR_VALUE_92731"


def configuration_hash(configuration):
    encoded = json.dumps(
        configuration, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ContractCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract_digest = hashlib.sha256((BUNDLE / "manifest.json").read_bytes()).hexdigest()
        fixtures = json.loads((BUNDLE / "fixtures.json").read_text(encoding="utf-8"))
        cls.fixture_digest = next(
            item["sha256"] for item in fixtures["fixtures"] if item["id"] == "draft-minimal"
        )

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="umthesis cli ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write_json(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, arguments)],
            cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
            timeout=30, check=False,
        )

    def assert_controlled_failure(self, completed, code=None):
        self.assertEqual(completed.returncode, 1, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertTrue(completed.stderr)
        if code is not None:
            self.assertTrue(completed.stderr.startswith(code + ":"), completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotIn(SENTINEL, completed.stdout + completed.stderr)

    def result_specimen(self):
        configuration = {
            "contract_version": "1.0.0",
            "purpose": "draft",
            "layout": "default",
            "double_sided": False,
            "identity": "identified",
            "output": "pdf",
            "pdf_standards": [],
            "language": "en",
            "label_locale": "en",
            "bibliography": {"mode": "unified", "style": "apa"},
            "metadata": {},
            "approval_refs": {},
        }
        return {
            "schema_version": 1,
            "contract_version": "1.0.0",
            "contract_sha256": self.contract_digest,
            "source": {"revision": "1" * 40, "tree": "2" * 40, "dirty": False},
            "fixture": {"id": "draft-minimal", "sha256": self.fixture_digest},
            "engine": {
                "name": "typst", "compiler_version": "0.15.1",
                "adapter_version": "1.0.0", "tool_versions": {},
            },
            "normalized_configuration": configuration,
            "configuration_sha256": configuration_hash(configuration),
            "run": {"id": "synthetic-cli", "generated_at": "2026-11-15T00:00:00Z"},
            "requirements": [{
                "requirement_id": requirement_id,
                "source_refs": ["umthesis-contract"],
                "applicability": "applicable",
                "reason": "Synthetic unexecuted specimen: " + SENTINEL,
                "implementation_state": "planned",
                "expected": "pass",
                "result": "unexecuted",
                "command": [],
                "exit_code": None,
                "seed": None,
                "duration_seconds": 0,
                "evidence_refs": [],
                "human_decision_refs": [],
            } for requirement_id in ("CON-02", "CON-03")],
            "artifacts": [],
            "manifest_refs": {
                "dependencies": None, "fonts": None, "toolchain": None, "validators": [],
            },
            "exceptions": [],
            "evidence_classification": "public-synthetic",
        }

    def result_with_artifact(self):
        artifact_root = self.root / "retained artifacts"
        artifact_root.mkdir()
        data = json.dumps({"synthetic": SENTINEL}).encode("utf-8")
        (artifact_root / "native.json").write_bytes(data)
        report = self.result_specimen()
        report["artifacts"] = [{
            "path": "native.json", "sha256": hashlib.sha256(data).hexdigest(),
            "role": "native-report",
        }]
        return report, artifact_root

    def test_file_layers_write_bound_json_without_echoing_author_values(self):
        metadata = self.write_json("metadata.json", {
            "layout": "print", "metadata": {"title": SENTINEL},
        })
        explicit = self.write_json("explicit.json", {"double_sided": False})
        output = self.root / "nested output" / "normalized.json"
        completed = self.run_cli(
            "normalize", "--metadata", metadata, "--explicit", explicit,
            "--set", "double_sided=true", "--output", output,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")
        result = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result["configuration"]["layout"], "print")
        self.assertIs(result["configuration"]["double_sided"], False)
        self.assertEqual(result["configuration"]["metadata"]["title"], SENTINEL)
        self.assertEqual(result["contract_version"], "1.0.0")
        self.assertEqual(result["contract_sha256"], self.contract_digest)
        self.assertEqual(result["configuration_sha256"], configuration_hash(result["configuration"]))

    def test_stdout_normalization_is_one_json_value_without_a_banner(self):
        completed = self.run_cli(
            "normalize", "--set", "metadata.title=Énergie = μ",
            "--set", "double_sided=false",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        result = json.loads(completed.stdout)
        self.assertEqual(result["configuration"]["metadata"]["title"], "Énergie = μ")
        self.assertIs(result["configuration"]["double_sided"], False)

    def test_metadata_and_explicit_files_must_be_objects(self):
        path = self.write_json("non-object.json", [SENTINEL])
        for option in ("--metadata", "--explicit"):
            with self.subTest(option=option):
                self.assert_controlled_failure(
                    self.run_cli("normalize", option, path), "invalid-type",
                )

    def test_duplicate_file_json_keys_are_rejected_without_echoing_values(self):
        path = self.root / "duplicate.json"
        path.write_text(
            '{"metadata":{"title":"' + SENTINEL + '","title":"replacement"}}',
            encoding="utf-8",
        )
        self.assert_controlled_failure(
            self.run_cli("normalize", "--metadata", path), "bundle-invalid",
        )

    def test_malformed_json_file_has_a_controlled_private_diagnostic(self):
        path = self.root / "malformed.json"
        path.write_text('{"metadata":{"title":"' + SENTINEL, encoding="utf-8")
        self.assert_controlled_failure(
            self.run_cli("normalize", "--metadata", path), "bundle-invalid",
        )

    def test_failed_output_write_does_not_print_normalized_author_data(self):
        metadata = self.write_json("metadata.json", {"metadata": {"title": SENTINEL}})
        self.assert_controlled_failure(
            self.run_cli("normalize", "--metadata", metadata, "--output", self.root),
        )

    def test_exact_contract_pin_is_enforced_before_normalization(self):
        self.assert_controlled_failure(
            self.run_cli(
                "--contract-sha256", "0" * 64,
                "normalize", "--set", "metadata.title=" + SENTINEL,
            ),
            "wrong-contract",
        )

    def test_validate_result_accepts_bound_retained_artifact_without_execution_claim(self):
        report, artifact_root = self.result_with_artifact()
        path = self.write_json("result.json", report)
        completed = self.run_cli(
            "validate-result", path, "--expected-revision", "1" * 40,
            "--artifacts-root", artifact_root,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertIn("no new execution is implied", completed.stdout)
        self.assertNotIn(SENTINEL, completed.stdout + completed.stderr)

    def test_validate_result_forwards_the_expected_revision(self):
        path = self.write_json("result.json", self.result_specimen())
        completed = self.run_cli(
            "validate-result", path, "--expected-revision", "3" * 40,
        )
        self.assert_controlled_failure(completed, "invalid-value")
        self.assertIn("source revision", completed.stderr)

    def test_validate_result_requires_root_and_checks_actual_retained_bytes(self):
        report, artifact_root = self.result_with_artifact()
        path = self.write_json("result.json", report)
        missing_root = self.run_cli(
            "validate-result", path, "--expected-revision", "1" * 40,
        )
        self.assert_controlled_failure(missing_root, "invalid-value")
        (artifact_root / "native.json").write_bytes(b'{"synthetic":"changed"}\n')
        changed_artifact = self.run_cli(
            "validate-result", path, "--expected-revision", "1" * 40,
            "--artifacts-root", artifact_root,
        )
        self.assert_controlled_failure(changed_artifact, "invalid-value")

    def test_validate_result_rejects_wrong_contract_and_non_object_payloads(self):
        wrong_contract = self.result_specimen()
        wrong_contract["contract_sha256"] = "0" * 64
        for payload, code in ((wrong_contract, "wrong-contract"), ([SENTINEL], "invalid-type")):
            with self.subTest(code=code):
                path = self.write_json("result.json", payload)
                self.assert_controlled_failure(
                    self.run_cli("validate-result", path, "--expected-revision", "1" * 40),
                    code,
                )

    def test_validate_result_requires_revision_at_the_argument_boundary(self):
        path = self.write_json("result.json", self.result_specimen())
        completed = self.run_cli("validate-result", path)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, "")
        self.assertIn("--expected-revision", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotIn(SENTINEL, completed.stderr)


if __name__ == "__main__":
    unittest.main()
