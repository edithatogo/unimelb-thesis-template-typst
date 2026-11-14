"""Regressions for offline schemas and typed adapter configuration bindings.

These synthetic specimens validate the interface only; no adapter is executed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.thesis_contract import ContractError, load_bundle
from test_thesis_contract import (
    CONTRACT_ROOT,
    configuration_sha256,
    unexecuted_result,
)


class OfflineSchemaReferenceTests(unittest.TestCase):
    def assert_reference_rejected_without_retrieval(self, keyword, reference):
        with tempfile.TemporaryDirectory(prefix="umthesis offline schema ") as temporary:
            root = Path(temporary) / "bundle"
            shutil.copytree(CONTRACT_ROOT, root)
            schema_path = root / "schemas" / "metadata.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            # This property is present in defaults, so a missed guard would
            # reach the resolver during normal bundle construction.
            schema["properties"]["double_sided"][keyword] = reference
            schema_path.write_text(
                json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            manifest_path = root / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["files"]["schemas/metadata.schema.json"] = hashlib.sha256(
                schema_path.read_bytes(),
            ).hexdigest()
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            expected_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            with patch(
                "urllib.request.urlopen",
                side_effect=AssertionError("Contract validation attempted external retrieval"),
            ) as retrieve:
                with self.assertRaises(ContractError) as caught:
                    load_bundle(root=root, expected_digest=expected_digest)
                self.assertEqual(caught.exception.code, "bundle-invalid")
                retrieve.assert_not_called()

    def test_external_ref_is_rejected_before_network_or_file_retrieval(self):
        for reference in (
            "https://example.invalid/untrusted-schema.json",
            "file:///synthetic/untrusted-schema.json",
        ):
            with self.subTest(reference=reference):
                self.assert_reference_rejected_without_retrieval("$ref", reference)

    def test_external_dynamic_ref_is_rejected_before_network_or_file_retrieval(self):
        for reference in (
            "https://example.invalid/untrusted-schema.json",
            "file:///synthetic/untrusted-schema.json",
        ):
            with self.subTest(reference=reference):
                self.assert_reference_rejected_without_retrieval("$dynamicRef", reference)


class ReportedConfigurationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(root=CONTRACT_ROOT)

    def test_false_to_zero_cannot_reuse_the_valid_configuration_digest(self):
        result = unexecuted_result(self.bundle)
        self.bundle.validate_result(result, expected_revision="1" * 40)
        original_digest = result["configuration_sha256"]
        self.assertIs(result["normalized_configuration"]["double_sided"], False)
        result["normalized_configuration"]["double_sided"] = 0
        self.assertNotEqual(
            configuration_sha256(result["normalized_configuration"]), original_digest,
        )
        with self.assertRaises(ContractError) as caught:
            self.bundle.validate_result(result, expected_revision="1" * 40)
        self.assertEqual(caught.exception.code, "invalid-type")

    def test_equal_integer_and_float_cannot_reuse_different_serialized_bytes(self):
        result = unexecuted_result(self.bundle)
        entry = self.bundle.fixtures["doctoral-monograph"]
        fixture = json.loads((CONTRACT_ROOT / entry["path"]).read_text(encoding="utf-8"))
        configuration = self.bundle.normalize(
            fixture["metadata"], self.bundle.parse_cli(fixture["cli"]), fixture["explicit"],
        )["configuration"]
        result["fixture"] = {"id": "doctoral-monograph", "sha256": entry["sha256"]}
        result["normalized_configuration"] = configuration
        result["configuration_sha256"] = configuration_sha256(configuration)
        self.bundle.validate_result(result, expected_revision="1" * 40)

        declarations = configuration["metadata"]["declarations"]
        original_count = declarations["word_count"]
        self.assertIs(type(original_count), int)
        declarations["word_count"] = float(original_count)
        # JSON Schema accepts an integral float as an integer, and Python
        # equality also accepts it. The documented byte digest still differs.
        self.assertEqual(declarations["word_count"], original_count)
        self.assertNotEqual(configuration_sha256(configuration), result["configuration_sha256"])
        with self.assertRaises(ContractError) as caught:
            self.bundle.validate_result(result, expected_revision="1" * 40)
        self.assertEqual(caught.exception.code, "invalid-value")



class PdfStandardCombinationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(root=CONTRACT_ROOT)

    def test_incompatible_pdf_base_versions_and_profiles_are_rejected(self):
        # PDF Association, Tagged PDF FAQ and PDF standards table, read 2026-11-14.
        # These are invalid target selections, regardless of renderer support.
        invalid_pairs = (
            ("pdf/ua-2", "pdf-1.7"),
            ("pdf/ua-2", "pdf/a-2a"),
            ("pdf/ua-2", "pdf/a-3a"),
            ("pdf-2.0", "pdf/a-2a"),
            ("pdf-2.0", "pdf/a-3a"),
            ("pdf-1.7", "pdf/a-4"),
            ("pdf-1.7", "pdf/a-4f"),
        )
        for pair in invalid_pairs:
            for standards in (list(pair), list(reversed(pair))):
                with self.subTest(standards=standards):
                    with self.assertRaises(ContractError) as caught:
                        self.bundle.normalize(metadata={"pdf_standards": standards})
                    self.assertEqual(caught.exception.code, "invalid-combination")

    def test_compatible_families_remain_inputs_without_certifying_output(self):
        for standards in (
            ["pdf-1.7", "pdf/ua-1", "pdf/a-2a"],
            ["pdf/ua-1", "pdf/a-3a"],
            ["pdf-2.0", "pdf/ua-2", "pdf/a-4"],
            ["pdf/ua-2", "pdf/a-4f"],
        ):
            with self.subTest(standards=standards):
                normalized = self.bundle.normalize(metadata={"pdf_standards": standards})
                self.assertEqual(normalized["configuration"]["pdf_standards"], standards)
                self.assertEqual(normalized["configuration"]["purpose"], "draft")


if __name__ == "__main__":
    unittest.main()
