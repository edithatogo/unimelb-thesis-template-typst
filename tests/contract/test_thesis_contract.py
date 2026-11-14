"""Behavioral checks for the shared UMTHESIS configuration and bundle boundary.

All examples are synthetic. These tests qualify contract behavior, not rendered
documents, institutional approval, or either engine's complete implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.thesis_contract import ContractError, load_bundle


CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "thesis" / "v1"


def normalized_defaults() -> dict:
    """The declared v1 defaults, not values read back from the implementation."""
    return {
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


def configuration_sha256(configuration: dict) -> str:
    """Independently apply the documented JSON serialization and hash recipe."""
    data = json.dumps(configuration, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def unexecuted_result(bundle) -> dict:
    """A schema specimen, explicitly not a claim that a renderer executed."""
    configuration = normalized_defaults()
    return {
        "schema_version": 1,
        "contract_version": "1.0.0",
        "contract_sha256": bundle.digest,
        "source": {"revision": "1" * 40, "tree": "2" * 40, "dirty": False},
        "fixture": {"id": "draft-minimal", "sha256": bundle.fixtures["draft-minimal"]["sha256"]},
        "engine": {"name": "typst", "compiler_version": "0.15.1",
                   "adapter_version": "1.0.0", "tool_versions": {}},
        "normalized_configuration": configuration,
        "configuration_sha256": configuration_sha256(configuration),
        "run": {"id": "synthetic", "generated_at": "2026-11-15T00:00:00Z"},
        "requirements": [{
            "requirement_id": "CON-02",
            "source_refs": ["umthesis-contract"],
            "applicability": "applicable",
            "reason": "Synthetic interface specimen; rendering unexecuted.",
            "implementation_state": "planned",
            "expected": "pass",
            "result": "unexecuted",
            "command": [],
            "exit_code": None,
            "seed": None,
            "duration_seconds": 0,
            "evidence_refs": [],
            "human_decision_refs": [],
        }],
        "artifacts": [],
        "manifest_refs": {"dependencies": None, "fonts": None,
                          "toolchain": None, "validators": []},
        "exceptions": [],
        "evidence_classification": "public-synthetic",
    }


def complete_configuration() -> dict:
    """A literal, synthetic final-purpose input independent of fixture output."""
    return {
        "purpose": "examination",
        "metadata": {
            "title": "Spectral observations in a synthetic environment",
            "author": {"student_record_name": "Alex Researcher"},
            "degree": {"kind": "doctoral", "course": "Doctor of Philosophy"},
            "academic_units": ["Synthetic Research School"],
            "submission": {"month": "2026-11"},
            "abstract": "This synthetic study describes a controlled experiment.",
            "declarations": {"original_work": True, "word_count": 1234},
        },
    }


class NormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(root=CONTRACT_ROOT)

    def assert_contract_error(self, code, function, *args, **kwargs):
        with self.assertRaises(ContractError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_empty_draft_uses_literal_defaults_without_inventing_author_data(self):
        result = self.bundle.normalize()
        self.assertEqual(result["configuration"], normalized_defaults())
        missing = {
            item["path"]
            for item in result["diagnostics"]
            if item["code"] == "missing-metadata"
        }
        self.assertEqual(
            missing,
            {
                "metadata.title",
                "metadata.author.student_record_name",
                "metadata.degree.kind",
                "metadata.degree.course",
                "metadata.academic_units",
                "metadata.submission.month",
                "metadata.abstract",
                "metadata.declarations.original_work",
                "metadata.declarations.word_count",
            },
        )

    def test_none_layers_are_absent(self):
        self.assertEqual(
            self.bundle.normalize(metadata=None, cli=None, explicit=None),
            self.bundle.normalize(),
        )

    def test_profile_defaults_preserve_independent_purpose(self):
        for profile, expected in (("default", False), ("draft", False),
                                  ("screen", False), ("print", True)):
            with self.subTest(profile=profile):
                config = self.bundle.normalize(metadata={"layout": profile})["configuration"]
                self.assertEqual(config["layout"], profile)
                self.assertIs(config["double_sided"], expected)
                self.assertEqual(config["purpose"], "draft")

    def test_every_override_layer_can_replace_the_previous_value(self):
        cases = (
            ({"layout": "print"}, {}, {}, True),
            ({"layout": "print", "double_sided": False}, {}, {}, False),
            ({"layout": "print", "double_sided": False}, {"double_sided": True}, {}, True),
            ({"layout": "print", "double_sided": False}, {"double_sided": True},
             {"double_sided": False}, False),
        )
        for metadata, cli, explicit, expected in cases:
            with self.subTest(metadata=metadata, cli=cli, explicit=explicit):
                result = self.bundle.normalize(metadata=metadata, cli=cli, explicit=explicit)
                self.assertIs(result["configuration"]["double_sided"], expected)

    def test_highest_precedence_layout_selects_its_defaults_first(self):
        cases = (
            ({"layout": "print"}, {"layout": "screen"}, {}, "screen", False),
            ({"layout": "screen"}, {"layout": "print"}, {}, "print", True),
            ({"layout": "print"}, {"layout": "print"}, {"layout": "screen"}, "screen", False),
            ({"layout": "screen"}, {"layout": "screen"}, {"layout": "print"}, "print", True),
        )
        for metadata, cli, explicit, layout, double_sided in cases:
            with self.subTest(metadata=metadata, cli=cli, explicit=explicit):
                config = self.bundle.normalize(metadata=metadata, cli=cli, explicit=explicit)["configuration"]
                self.assertEqual(config["layout"], layout)
                self.assertIs(config["double_sided"], double_sided)

    def test_selected_profile_does_not_override_explicit_metadata_values(self):
        config = self.bundle.normalize(
            metadata={"layout": "screen", "double_sided": False},
            cli={"layout": "print"},
        )["configuration"]
        self.assertEqual(config["layout"], "print")
        self.assertIs(config["double_sided"], False)

    def test_nested_patches_preserve_siblings_and_replace_arrays(self):
        config = self.bundle.normalize(
            metadata={
                "metadata": {
                    "title": "Metadata title",
                    "author": {"student_record_name": "Alex Researcher", "orcid": "0000-0000-0000-001X"},
                    "academic_units": ["First unit", "Second unit"],
                },
                "bibliography": {"style": "ieee"},
            },
            cli={"metadata": {"title": "CLI title", "academic_units": ["Replacement unit"]}},
            explicit={"metadata": {"title": "Function title"}},
        )["configuration"]
        self.assertEqual(config["metadata"]["title"], "Function title")
        self.assertEqual(config["metadata"]["academic_units"], ["Replacement unit"])
        self.assertEqual(config["metadata"]["author"], {
            "student_record_name": "Alex Researcher", "orcid": "0000-0000-0000-001X",
        })
        self.assertEqual(config["bibliography"], {"mode": "unified", "style": "ieee"})

    def test_inputs_and_cached_defaults_are_not_mutated(self):
        metadata = complete_configuration()
        cli = {"metadata": {"academic_units": ["CLI unit"]}}
        explicit = {"double_sided": False}
        before = copy.deepcopy((metadata, cli, explicit))
        first = self.bundle.normalize(metadata=metadata, cli=cli, explicit=explicit)
        self.assertEqual((metadata, cli, explicit), before)
        first["configuration"]["metadata"]["academic_units"].append("Mutated output")
        first["configuration"]["pdf_standards"].append("pdf/ua-1")
        second = self.bundle.normalize(metadata=metadata, cli=cli, explicit=explicit)
        self.assertEqual(second["configuration"]["metadata"]["academic_units"], ["CLI unit"])
        self.assertEqual(second["configuration"]["pdf_standards"], [])
        self.assertEqual((metadata, cli, explicit), before)

    def test_equivalent_input_order_and_layering_produce_identical_results(self):
        original = complete_configuration()
        reordered = dict(reversed(list(original.items())))
        reordered["metadata"] = dict(reversed(list(original["metadata"].items())))
        expected = self.bundle.normalize(metadata=original)
        self.assertEqual(self.bundle.normalize(metadata=reordered), expected)
        self.assertEqual(self.bundle.normalize(metadata={"purpose": "examination"},
                                               cli={"metadata": original["metadata"]}), expected)

    def test_unknown_keys_are_rejected_at_every_layer(self):
        for layer in ("metadata", "cli", "explicit"):
            for patch in ({"profle": "print"}, {"metadata": {"titel": "Misspelled"}},
                          {"metadata": {"author": {"name": "Undeclared alias"}}}):
                with self.subTest(layer=layer, patch=patch):
                    self.assert_contract_error("unknown-key", self.bundle.normalize, **{layer: patch})

    def test_invalid_lower_precedence_values_cannot_be_hidden(self):
        cases = (
            ({"double_sided": "false"}, {"double_sided": False}, {}, "invalid-type"),
            ({"layout": "poster"}, {"layout": "print"}, {}, "invalid-value"),
            ({}, {"double_sided": "false"}, {"double_sided": False}, "invalid-type"),
            ({"metadata": {"submission": {"month": "2026-13"}}},
             {"metadata": {"submission": {"month": "2026-11"}}}, {}, "invalid-date"),
        )
        for metadata, cli, explicit, code in cases:
            with self.subTest(metadata=metadata, cli=cli):
                self.assert_contract_error(code, self.bundle.normalize,
                                           metadata=metadata, cli=cli, explicit=explicit)

    def test_wrong_types_are_not_coerced_by_normalization(self):
        cases = (
            {"double_sided": "false"}, {"double_sided": 0}, {"double_sided": None},
            {"metadata": []}, {"metadata": {"academic_units": "One unit"}},
            {"metadata": {"declarations": {"word_count": True}}},
            {"metadata": {"declarations": {"word_count": "1234"}}},
        )
        for patch in cases:
            with self.subTest(patch=patch):
                self.assert_contract_error("invalid-type", self.bundle.normalize, metadata=patch)

    def test_falsey_non_object_layers_are_not_treated_as_absent(self):
        for layer in ("metadata", "cli", "explicit"):
            for value in ([], False, 0, ""):
                with self.subTest(layer=layer, value=value):
                    self.assert_contract_error("invalid-type", self.bundle.normalize, **{layer: value})

    def test_unknown_enum_values_and_duplicate_set_values_fail(self):
        for patch in ({"purpose": "submission"}, {"layout": "poster"},
                      {"identity": "anonymous"}, {"output": "epub"},
                      {"label_locale": "xx"}, {"pdf_standards": ["pdf/ua-1", "pdf/ua-1"]},
                      {"metadata": {"degree": {"kind": "bachelor"}}},
                      {"metadata": {"academic_units": ["One unit", "One unit"]}}):
            with self.subTest(patch=patch):
                self.assert_contract_error("invalid-value", self.bundle.normalize, metadata=patch)

    def test_nonfinite_numeric_values_are_rejected_in_nested_metadata(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                self.assert_contract_error("invalid-value", self.bundle.normalize, metadata={
                    "metadata": {"creative_outputs": [{
                        "id": "synthetic-work", "description": "Synthetic creative component",
                        "proportion": value,
                    }]},
                })

    def test_year_month_values_are_calendar_valid(self):
        for valid in ("0001-01", "2024-02", "2026-12", "9999-12"):
            with self.subTest(valid=valid):
                config = self.bundle.normalize(metadata={"metadata": {"submission": {"month": valid}}})["configuration"]
                self.assertEqual(config["metadata"]["submission"]["month"], valid)
        for invalid in ("0000-01", "2026-00", "2026-13", "2026-1", "26-11", "2026-11-01", " 2026-11"):
            for field in ("month", "resubmission_month"):
                with self.subTest(invalid=invalid, field=field):
                    self.assert_contract_error("invalid-date", self.bundle.normalize,
                                               metadata={"metadata": {"submission": {field: invalid}}})

    def test_orcid_syntax_and_check_digit_are_independent_requirements(self):
        for valid in ("0000-0000-0000-0001", "0000-0000-0000-001X", None):
            with self.subTest(valid=valid):
                config = self.bundle.normalize(metadata={"metadata": {"author": {"orcid": valid}}})["configuration"]
                self.assertEqual(config["metadata"]["author"]["orcid"], valid)
        for invalid in ("0000-0000-0000-0002", "0000-0000-0000-0010", "0000000000000001",
                        "0000-0000-0000-001x", "https://orcid.org/0000-0000-0000-0001", ""):
            with self.subTest(invalid=invalid):
                self.assert_contract_error("invalid-orcid", self.bundle.normalize,
                                           metadata={"metadata": {"author": {"orcid": invalid}}})

    def test_resource_types_and_paths_are_validated_before_rendering(self):
        resource = {"id": "figure-one", "kind": "image", "path": "assets/chart.svg"}
        config = self.bundle.normalize(metadata={"metadata": {"resources": [resource]}})["configuration"]
        self.assertEqual(config["metadata"]["resources"], [resource])
        for field, value in (("kind", "executable"), ("path", "../private.txt"),
                             ("path", "/tmp/asset.svg"), ("path", "assets/../private.txt")):
            with self.subTest(field=field, value=value):
                invalid = dict(resource, **{field: value})
                self.assert_contract_error("invalid-value", self.bundle.normalize,
                                           metadata={"metadata": {"resources": [invalid]}})

    def test_final_purposes_accept_complete_typed_metadata(self):
        for purpose in ("examination", "deposit-full", "deposit-public"):
            with self.subTest(purpose=purpose):
                source = complete_configuration()
                source["purpose"] = purpose
                result = self.bundle.normalize(metadata=source)
                self.assertEqual(result["configuration"]["metadata"], source["metadata"])
                self.assertEqual(result["diagnostics"], [])

    def test_final_purposes_reject_each_missing_required_field(self):
        paths = (("title",), ("author", "student_record_name"), ("degree", "kind"),
                 ("degree", "course"), ("academic_units",), ("submission", "month"),
                 ("abstract",), ("declarations", "original_work"), ("declarations", "word_count"))
        for path in paths:
            with self.subTest(path=path):
                source = complete_configuration()
                node = source["metadata"]
                for key in path[:-1]:
                    node = node[key]
                del node[path[-1]]
                self.assert_contract_error("missing-metadata", self.bundle.normalize, metadata=source)

    def test_final_required_text_and_collections_cannot_be_empty(self):
        for key, value in (("title", ""), ("title", " \t "),
                           ("abstract", "\n"), ("academic_units", [])):
            with self.subTest(key=key, value=value):
                source = complete_configuration()
                source["metadata"][key] = value
                self.assert_contract_error("missing-metadata", self.bundle.normalize, metadata=source)

    def test_final_required_text_rejects_known_placeholders(self):
        for value in ("Your thesis title", "  PLACEHOLDER  ", "Results TBD after review", "TODO: revise abstract"):
            with self.subTest(value=value):
                source = complete_configuration()
                source["metadata"]["title"] = value
                self.assert_contract_error("placeholder-metadata", self.bundle.normalize, metadata=source)

    def test_blind_review_is_draft_only_regardless_of_layout(self):
        config = self.bundle.normalize(metadata={"identity": "blind-review", "layout": "print"})["configuration"]
        self.assertEqual(config["identity"], "blind-review")
        for purpose in ("examination", "deposit-full", "deposit-public"):
            with self.subTest(purpose=purpose):
                source = complete_configuration()
                source.update(purpose=purpose, identity="blind-review")
                self.assert_contract_error("invalid-combination", self.bundle.normalize,
                                           metadata=source, explicit={"layout": "draft", "double_sided": False})

    def test_label_locale_does_not_change_thesis_language_or_require_permission(self):
        for language in ("en", "en-AU"):
            with self.subTest(language=language):
                source = complete_configuration()
                source.update(language=language, label_locale="zh")
                result = self.bundle.normalize(metadata=source)
                self.assertEqual(result["configuration"]["language"], language)
                self.assertEqual(result["configuration"]["label_locale"], "zh")
                self.assertEqual(result["diagnostics"], [])

    def test_non_english_final_requires_reference_and_english_summary(self):
        source = complete_configuration()
        source["language"] = "fr"
        source["metadata"]["english_summary"] = "A synthetic English summary."
        self.assert_contract_error("missing-approval", self.bundle.normalize, metadata=source)
        source["approval_refs"] = {"non_english": "synthetic-language-decision"}
        result = self.bundle.normalize(metadata=source)
        self.assertEqual(result["configuration"]["approval_refs"], source["approval_refs"])
        self.assertEqual([(item["code"], item["path"]) for item in result["diagnostics"]],
                         [("human-review-required", "approval_refs.non_english")])
        del source["metadata"]["english_summary"]
        self.assert_contract_error("missing-metadata", self.bundle.normalize, metadata=source)

    def test_draft_language_and_joint_award_gaps_remain_explicit_diagnostics(self):
        result = self.bundle.normalize(metadata={
            "language": "fr",
            "metadata": {"joint_award": {"institutions": ["Synthetic University A", "Synthetic University B"]}},
        })
        diagnostics = {(item["code"], item["path"]) for item in result["diagnostics"]}
        self.assertIn(("missing-approval", "approval_refs.non_english"), diagnostics)
        self.assertIn(("missing-approval", "approval_refs.joint_award"), diagnostics)
        self.assertIn(("missing-metadata", "metadata.english_summary"), diagnostics)
        self.assertEqual(result["configuration"]["approval_refs"], {})

    def test_final_joint_award_requires_a_separate_reference(self):
        source = complete_configuration()
        source["metadata"]["joint_award"] = {"institutions": ["Synthetic University A", "Synthetic University B"]}
        self.assert_contract_error("missing-approval", self.bundle.normalize, metadata=source)
        source["approval_refs"] = {"joint_award": "synthetic-joint-award-decision"}
        result = self.bundle.normalize(metadata=source)
        self.assertEqual([(item["code"], item["path"]) for item in result["diagnostics"]],
                         [("human-review-required", "approval_refs.joint_award")])

    def test_incompatible_pdf_standards_are_rejected(self):
        combinations = (
            ["pdf/ua-1", "pdf-2.0"], ["pdf/ua-1", "pdf/a-4"], ["pdf/ua-1", "pdf/a-4f"],
            ["pdf/ua-1", "pdf/ua-2"], ["pdf/a-2a", "pdf/a-3a"],
            ["pdf-1.7", "pdf-2.0"],
        )
        for standards in combinations:
            with self.subTest(standards=standards):
                self.assert_contract_error("invalid-combination", self.bundle.normalize,
                                           metadata={"pdf_standards": standards})
        config = self.bundle.normalize(metadata={"pdf_standards": ["pdf/ua-1", "pdf/a-2a"]})["configuration"]
        self.assertEqual(config["pdf_standards"], ["pdf/ua-1", "pdf/a-2a"])

    def test_experimental_outputs_do_not_inherit_pdf_or_final_qualification(self):
        for output in ("html", "bundle"):
            with self.subTest(output=output):
                result = self.bundle.normalize(metadata={"output": output})
                self.assertEqual(result["configuration"]["output"], output)
                self.assert_contract_error("invalid-combination", self.bundle.normalize,
                                           metadata={"output": output, "pdf_standards": ["pdf/ua-1"]})
                source = complete_configuration()
                source["output"] = output
                self.assert_contract_error("invalid-combination", self.bundle.normalize, metadata=source)


class CliParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(root=CONTRACT_ROOT)

    def test_cli_uses_schema_types_including_nested_json(self):
        self.assertEqual(self.bundle.parse_cli([
            "double_sided=false",
            "metadata.title=false",
            "metadata.declarations.word_count=1234",
            "metadata.declarations.original_work=true",
            'metadata.academic_units=["Synthetic A","Synthetic B"]',
            'metadata.author={"student_record_name":"Alex Researcher","orcid":null}',
        ]), {
            "double_sided": False,
            "metadata": {
                "title": "false",
                "declarations": {"word_count": 1234, "original_work": True},
                "academic_units": ["Synthetic A", "Synthetic B"],
                "author": {"student_record_name": "Alex Researcher", "orcid": None},
            },
        })

    def test_cli_preserves_string_equals_and_unicode(self):
        self.assertEqual(self.bundle.parse_cli(["metadata.title=Énergie = μ × fréquence"]),
                         {"metadata": {"title": "Énergie = μ × fréquence"}})

    def test_cli_rejects_non_boolean_spellings_and_wrong_numeric_types(self):
        assignments = (
            "double_sided=False", "double_sided=yes", "double_sided=0", "double_sided=null",
            'double_sided="false"', "metadata.declarations.word_count=true",
            'metadata.declarations.word_count="1234"', "metadata.declarations.word_count=1.5",
            "metadata.declarations.word_count=-1", "metadata.declarations.word_count=NaN",
            'metadata.academic_units="Synthetic unit"',
        )
        for assignment in assignments:
            with self.subTest(assignment=assignment), self.assertRaises(ContractError):
                self.bundle.parse_cli([assignment])

    def test_duplicate_and_parent_child_assignments_are_ambiguous(self):
        cases = (
            ["double_sided=true", "double_sided=false"],
            ["double_sided=false", "double_sided=false"],
            ['metadata={"title":"Parent"}', "metadata.title=Child"],
            ["metadata.title=Child", 'metadata={"title":"Parent"}'],
            ['metadata.author={"student_record_name":"Alex Researcher"}', "metadata.author.orcid=0000-0000-0000-001X"],
        )
        for assignments in cases:
            with self.subTest(assignments=assignments), self.assertRaises(ContractError):
                self.bundle.parse_cli(assignments)

    def test_cli_json_rejects_duplicate_members_and_nonfinite_numbers(self):
        assignments = (
            'metadata.author={"student_record_name":"First","student_record_name":"Second"}',
            'metadata.funding=[{"funder":"First","funder":"Second"}]',
            'metadata.creative_outputs=[{"id":"work","description":"Synthetic","proportion":NaN}]',
            'metadata.creative_outputs=[{"id":"work","description":"Synthetic","proportion":Infinity}]',
            'metadata.creative_outputs=[{"id":"work","description":"Synthetic","proportion":1e999}]',
        )
        for assignment in assignments:
            with self.subTest(assignment=assignment), self.assertRaises(ContractError):
                self.bundle.parse_cli([assignment])

    def test_unknown_or_malformed_cli_keys_fail(self):
        for assignment in ("double-sided=false", "metadata.titel=Misspelled", "layout", "=value",
                           "metadata..title=Value", "metadata.author.name=Undeclared alias"):
            with self.subTest(assignment=assignment), self.assertRaises(ContractError):
                self.bundle.parse_cli([assignment])

    def test_parsed_false_overrides_true_profile_default(self):
        parsed = self.bundle.parse_cli(["layout=print", "double_sided=false"])
        result = self.bundle.normalize(cli=parsed)
        self.assertEqual(result["configuration"]["layout"], "print")
        self.assertIs(result["configuration"]["double_sided"], False)


class BundleIntegrityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="umthesis contract ")
        self.addCleanup(temporary.cleanup)
        self.temporary = Path(temporary.name)
        self.root = self.temporary / "bundle"
        shutil.copytree(CONTRACT_ROOT, self.root)

    def read_document(self, name):
        return json.loads((self.root / name).read_text(encoding="utf-8"))

    def write_document(self, name, value):
        (self.root / name).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8",
        )

    def refresh_hash(self, name):
        """Refresh byte integrity so a test reaches semantic validation."""
        manifest = self.read_document("manifest.json")
        manifest["files"][name] = hashlib.sha256((self.root / name).read_bytes()).hexdigest()
        self.write_document("manifest.json", manifest)

    def assert_bundle_error(self, code="bundle-invalid", **kwargs):
        with self.assertRaises(ContractError) as caught:
            load_bundle(root=self.root, **kwargs)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_unchanged_copy_loads_with_exact_manifest_byte_pin(self):
        expected = hashlib.sha256((self.root / "manifest.json").read_bytes()).hexdigest()
        bundle = load_bundle(root=self.root, expected_digest=expected)
        self.assertEqual(bundle.digest, expected)

    def test_wrong_expected_manifest_digest_is_rejected(self):
        self.assert_bundle_error("wrong-contract", expected_digest="0" * 64)

    def test_manifest_whitespace_change_also_changes_its_exact_byte_identity(self):
        manifest_path = self.root / "manifest.json"
        original = manifest_path.read_bytes()
        expected = hashlib.sha256(original).hexdigest()
        manifest_path.write_bytes(original + b"\n")
        self.assert_bundle_error("wrong-contract", expected_digest=expected)

    def test_unsupported_contract_version_is_rejected(self):
        manifest = self.read_document("manifest.json")
        manifest["contract_version"] = "2.0.0"
        self.write_document("manifest.json", manifest)
        self.assert_bundle_error("wrong-contract")

    def test_missing_manifest_fails_with_contract_error(self):
        (self.root / "manifest.json").unlink()
        self.assert_bundle_error()

    def test_empty_file_inventory_cannot_bypass_integrity_checks(self):
        manifest = self.read_document("manifest.json")
        manifest["files"] = {}
        self.write_document("manifest.json", manifest)
        self.assert_bundle_error()

    def test_missing_listed_file_is_rejected(self):
        (self.root / "defaults.json").unlink()
        self.assert_bundle_error()

    def test_changed_file_bytes_are_rejected_even_when_json_is_unchanged(self):
        path = self.root / "defaults.json"
        path.write_bytes(path.read_bytes() + b"\n")
        self.assert_bundle_error()

    def test_unlisted_file_cannot_silently_extend_a_pinned_bundle(self):
        self.write_document("unlisted-policy.json", {"extra": "unreviewed"})
        self.assert_bundle_error()

    def test_removing_a_file_from_inventory_does_not_make_it_trusted(self):
        manifest = self.read_document("manifest.json")
        del manifest["files"]["schemas/metadata.schema.json"]
        self.write_document("manifest.json", manifest)
        self.assert_bundle_error()

    def test_inventory_paths_cannot_escape_bundle_root(self):
        outside = self.temporary / "outside.json"
        outside.write_text('{"synthetic":true}\n', encoding="utf-8")
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        original = self.read_document("manifest.json")
        for path in ("../outside.json", str(outside), "schemas/../../outside.json"):
            with self.subTest(path=path):
                manifest = copy.deepcopy(original)
                manifest["files"][path] = digest
                self.write_document("manifest.json", manifest)
                self.assert_bundle_error()

    def test_symlinked_file_cannot_bind_outside_content(self):
        target = self.root / "defaults.json"
        outside = self.temporary / "outside-defaults.json"
        outside.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(outside)
        self.assert_bundle_error()

    def test_symlinked_parent_directory_cannot_escape_root(self):
        target = self.root / "schemas"
        outside = self.temporary / "outside-schemas"
        target.rename(outside)
        target.symlink_to(outside, target_is_directory=True)
        self.assert_bundle_error()

    def test_duplicate_json_keys_are_rejected_at_manifest_boundary(self):
        path = self.root / "manifest.json"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("{", '{"contract_version":"1.0.0",', 1), encoding="utf-8")
        self.assert_bundle_error()

    def test_duplicate_document_keys_fail_after_digest_is_refreshed(self):
        path = self.root / "defaults.json"
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("{", '{"purpose":"draft",', 1), encoding="utf-8")
        self.refresh_hash("defaults.json")
        self.assert_bundle_error()

    def test_nonfinite_json_is_not_a_valid_bundle_document(self):
        defaults = self.read_document("defaults.json")
        defaults["metadata"] = {"declarations": {"word_count": float("nan")}}
        self.write_document("defaults.json", defaults)
        self.refresh_hash("defaults.json")
        with self.assertRaises(ContractError) as caught:
            load_bundle(root=self.root)
        self.assertIn(caught.exception.code, {"invalid-value", "bundle-invalid"})

    def test_invalid_json_schema_fails_after_digest_is_refreshed(self):
        name = "schemas/metadata.schema.json"
        schema = self.read_document(name)
        schema["type"] = "not-a-json-schema-type"
        self.write_document(name, schema)
        self.refresh_hash(name)
        self.assert_bundle_error()

    def test_requirement_owner_is_mandatory_after_byte_hashes_are_refreshed(self):
        name = "requirements.json"
        requirements = self.read_document(name)
        del requirements["requirements"][0]["owners"]
        self.write_document(name, requirements)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_requirement_source_must_resolve_to_the_ledger(self):
        name = "requirements.json"
        requirements = self.read_document(name)
        requirements["requirements"][0]["source_refs"][0]["source_id"] = "missing-source"
        self.write_document(name, requirements)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_duplicate_requirement_ids_cannot_overwrite_an_obligation(self):
        name = "requirements.json"
        requirements = self.read_document(name)
        requirements["requirements"][1]["id"] = requirements["requirements"][0]["id"]
        self.write_document(name, requirements)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_removing_a_requirement_cannot_shrink_the_parent_contract(self):
        name = "requirements.json"
        requirements = self.read_document(name)
        requirements["requirements"].pop()
        self.write_document(name, requirements)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_fixture_requirement_mapping_cannot_dangle(self):
        name = "fixtures.json"
        fixtures = self.read_document(name)
        fixtures["fixtures"][0]["requirements"].append("CON-99")
        self.write_document(name, fixtures)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_duplicate_fixture_ids_are_rejected_before_dictionary_conversion(self):
        name = "fixtures.json"
        fixtures = self.read_document(name)
        fixtures["fixtures"].append(copy.deepcopy(fixtures["fixtures"][0]))
        self.write_document(name, fixtures)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_fixture_digest_must_match_even_when_outer_inventory_is_current(self):
        name = "fixtures.json"
        fixtures = self.read_document(name)
        fixtures["fixtures"][0]["sha256"] = "0" * 64
        self.write_document(name, fixtures)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_fixture_document_id_must_match_manifest_after_all_hashes_refresh(self):
        fixtures = self.read_document("fixtures.json")
        entry = fixtures["fixtures"][0]
        fixture = self.read_document(entry["path"])
        fixture["id"] = "different-fixture-id"
        self.write_document(entry["path"], fixture)
        entry["sha256"] = hashlib.sha256((self.root / entry["path"]).read_bytes()).hexdigest()
        self.refresh_hash(entry["path"])
        self.write_document("fixtures.json", fixtures)
        self.refresh_hash("fixtures.json")
        self.assert_bundle_error(code=None)

    def test_compatibility_cannot_exclude_its_own_contract_version(self):
        name = "compatibility.json"
        compatibility = self.read_document(name)
        compatibility["supported_contract_versions"] = ["0.9.0"]
        self.write_document(name, compatibility)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_retained_source_digest_must_match_its_snapshot(self):
        name = "sources.json"
        sources = self.read_document(name)
        source = next(item for item in sources["sources"] if item["id"] == "umthesis-contract")
        source["content_sha256"] = "0" * 64
        self.write_document(name, sources)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)

    def test_legacy_crosswalk_cannot_point_to_unknown_requirements(self):
        name = "legacy-crosswalk.json"
        crosswalk = self.read_document(name)
        crosswalk["entries"][0]["requirement_ids"] = ["CON-99"]
        self.write_document(name, crosswalk)
        self.refresh_hash(name)
        self.assert_bundle_error(code=None)


class ResultValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(root=CONTRACT_ROOT)

    def assert_result_error(self, result, code=None, **kwargs):
        with self.assertRaises(ContractError) as caught:
            self.bundle.validate_result(result, **kwargs)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        return caught.exception

    def retained_artifact(self):
        """A real file retained with an unexecuted, synthetic report."""
        temporary = tempfile.TemporaryDirectory(prefix="umthesis retained artifact ")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "artifacts"
        root.mkdir()
        data = b'{"synthetic":"retained input; no renderer execution"}\n'
        (root / "native-report.json").write_bytes(data)
        result = unexecuted_result(self.bundle)
        result["artifacts"] = [{"path": "native-report.json", "sha256": hashlib.sha256(data).hexdigest(),
                                "role": "native-report"}]
        return root, result, data

    def test_valid_unexecuted_specimen_is_accepted_without_mutation(self):
        result = unexecuted_result(self.bundle)
        original = copy.deepcopy(result)
        self.assertIsNone(self.bundle.validate_result(result))
        self.assertIsNone(self.bundle.validate_result(result, expected_revision="1" * 40))
        self.assertEqual(result, original)
        self.assertEqual(result["requirements"][0]["result"], "unexecuted")

    def test_wrong_contract_digest_does_not_qualify_a_result(self):
        result = unexecuted_result(self.bundle)
        result["contract_sha256"] = "0" * 64
        self.assert_result_error(result, code="wrong-contract")

    def test_unknown_contract_version_is_rejected(self):
        result = unexecuted_result(self.bundle)
        result["contract_version"] = "2.0.0"
        self.assert_result_error(result)

    def test_stale_fixture_digest_and_unknown_fixture_id_are_rejected(self):
        for key, value in (("sha256", "0" * 64), ("id", "unknown-fixture")):
            with self.subTest(key=key):
                result = unexecuted_result(self.bundle)
                result["fixture"][key] = value
                self.assert_result_error(result, code="stale-fixture")

    def test_stale_adapter_version_is_rejected(self):
        result = unexecuted_result(self.bundle)
        result["engine"]["adapter_version"] = "0.9.0"
        self.assert_result_error(result)

    def test_configuration_digest_is_verified_against_exact_configuration(self):
        result = unexecuted_result(self.bundle)
        result["configuration_sha256"] = "0" * 64
        self.assert_result_error(result)

    def test_self_consistent_config_hash_does_not_hide_wrong_fixture_configuration(self):
        result = unexecuted_result(self.bundle)
        result["normalized_configuration"]["layout"] = "print"
        result["normalized_configuration"]["double_sided"] = True
        result["configuration_sha256"] = configuration_sha256(result["normalized_configuration"])
        self.assert_result_error(result)

    def test_normalized_configuration_must_itself_satisfy_metadata_schema(self):
        result = unexecuted_result(self.bundle)
        result["normalized_configuration"]["double_sided"] = "false"
        result["configuration_sha256"] = configuration_sha256(result["normalized_configuration"])
        self.assert_result_error(result)

    def test_expected_receiving_revision_is_checked_separately_from_contract(self):
        self.assert_result_error(unexecuted_result(self.bundle), expected_revision="3" * 40)

    def test_unknown_requirement_and_source_references_are_rejected(self):
        for key, value in (("requirement_id", "CON-99"), ("source_refs", ["missing-source"])):
            with self.subTest(key=key):
                result = unexecuted_result(self.bundle)
                result["requirements"][0][key] = value
                self.assert_result_error(result)

    def test_ambiguous_duplicate_requirement_results_are_rejected(self):
        result = unexecuted_result(self.bundle)
        result["requirements"].append(copy.deepcopy(result["requirements"][0]))
        result["requirements"][1]["result"] = "blocked"
        self.assert_result_error(result)

    def test_result_schema_rejects_extra_fields_and_wrong_evidence_classification(self):
        for patch in ({"overall_compliant": True}, {"evidence_classification": "private"}):
            with self.subTest(patch=patch):
                result = unexecuted_result(self.bundle)
                result.update(patch)
                self.assert_result_error(result)

    def test_unexecuted_result_cannot_claim_an_exit_code(self):
        result = unexecuted_result(self.bundle)
        result["requirements"][0]["exit_code"] = 0
        self.assert_result_error(result)

    def test_not_applicable_result_requires_consistent_applicability(self):
        result = unexecuted_result(self.bundle)
        result["requirements"][0]["result"] = "not-applicable"
        self.assert_result_error(result)

    def test_planned_adapter_cannot_claim_executed_pass_even_with_native_file(self):
        temporary = tempfile.TemporaryDirectory(prefix="umthesis result ")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        data = b'{"synthetic":"test double, not a renderer report"}\n'
        (root / "native-report.json").write_bytes(data)
        result = unexecuted_result(self.bundle)
        result["requirements"][0].update({
            "implementation_state": "implemented", "result": "executed-pass",
            "command": ["synthetic-adapter", "draft-minimal"], "exit_code": 0,
            "evidence_refs": ["native-report.json"],
        })
        result["artifacts"] = [{"path": "native-report.json", "sha256": hashlib.sha256(data).hexdigest(),
                                "role": "native-report"}]
        self.assert_result_error(result, expected_revision="1" * 40, artifact_root=root)


    def test_retained_artifact_is_verified_without_turning_unexecuted_into_pass(self):
        root, result, _data = self.retained_artifact()
        original = copy.deepcopy(result)
        self.assertIsNone(self.bundle.validate_result(result, artifact_root=root))
        self.assertEqual(result, original)
        self.assertEqual(result["requirements"][0]["result"], "unexecuted")

    def test_declared_artifacts_require_an_explicit_artifact_root(self):
        _root, result, _data = self.retained_artifact()
        self.assert_result_error(result)

    def test_changed_artifact_bytes_cannot_reuse_a_previous_digest(self):
        root, result, _data = self.retained_artifact()
        (root / "native-report.json").write_bytes(b'{"synthetic":"changed"}\n')
        self.assert_result_error(result, artifact_root=root)

    def test_missing_artifact_does_not_satisfy_a_declared_reference(self):
        root, result, _data = self.retained_artifact()
        (root / "native-report.json").unlink()
        self.assert_result_error(result, artifact_root=root)

    def test_artifact_paths_cannot_escape_the_declared_root(self):
        root, result, data = self.retained_artifact()
        outside = root.parent / "outside.json"
        outside.write_bytes(data)
        for path in ("../outside.json", str(outside)):
            with self.subTest(path=path):
                result["artifacts"][0]["path"] = path
                self.assert_result_error(result, artifact_root=root)

    def test_symlinked_artifact_or_parent_cannot_read_outside_content(self):
        root, result, data = self.retained_artifact()
        outside = root.parent / "outside"
        outside.mkdir()
        (outside / "native-report.json").write_bytes(data)
        (root / "escaped.json").symlink_to(outside / "native-report.json")
        (root / "linked").symlink_to(outside, target_is_directory=True)
        for path in ("escaped.json", "linked/native-report.json"):
            with self.subTest(path=path):
                result["artifacts"][0]["path"] = path
                self.assert_result_error(result, artifact_root=root)


if __name__ == "__main__":
    unittest.main()
