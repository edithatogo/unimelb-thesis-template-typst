"""Synthetic policy decisions; these tests never establish institutional approval."""
from copy import deepcopy
from datetime import date, datetime
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import submission_policy as policy

FIXTURES = ROOT / "tests/policy"
AS_OF = date(2026, 11, 15)
HARNESS_SPEC = importlib.util.spec_from_file_location("policy_fixture_gate", FIXTURES / "verify.py")
harness = importlib.util.module_from_spec(HARNESS_SPEC)
HARNESS_SPEC.loader.exec_module(harness)


def synthetic_pdf():
    """Small independent PDF byte specimen; policy inspection remains unexecuted."""
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>",
               b"<< /Length 0 >>\nstream\n\nendstream"]
    data = b"%PDF-1.7\n"
    offsets = [0]
    for index, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += str(index).encode() + b" 0 obj\n" + body + b"\nendobj\n"
    start = len(data)
    data += b"xref\n0 5\n0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return data + f"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode()


class SubmissionPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.pdf = self.folder / "synthetic-thesis.pdf"
        self.pdf.write_bytes(synthetic_pdf())
        self.pdf_hash = policy.digest(self.pdf)

    def fixture(self, name):
        text = (FIXTURES / "fixtures" / (name + ".json")).read_text()
        text = text.replace("${PDF_SHA256}", self.pdf_hash)
        acknowledgement = policy.load_policy()["profile"]["rtp_acknowledgement"]
        text = text.replace("${RTP_ACKNOWLEDGEMENT}", acknowledgement)
        return json.loads(text)

    def request(self, name="draft-baseline"):
        return self.fixture(name)["request"]

    def evaluate(self, value, **options):
        return policy.evaluate(value, pdf_path=options.pop("pdf_path", self.pdf),
                               evidence_root=options.pop("evidence_root", FIXTURES),
                               as_of=options.pop("as_of", AS_OF), **options)

    def checks(self, result):
        return {item["id"]: item for item in result["checks"]}

    def test_frozen_engine_neutral_cases_have_exact_expected_failures(self):
        manifest = json.loads((FIXTURES / "manifest.json").read_text())
        self.assertEqual(len(manifest["cases"]), 64)
        self.assertEqual(len({x["id"] for x in manifest["cases"]}), 64)
        self.assertEqual({x["path"] for x in manifest["cases"]},
                         {p.relative_to(FIXTURES).as_posix() for p in (FIXTURES / "fixtures").glob("*.json")})
        for entry in manifest["cases"]:
            with self.subTest(case=entry["id"]):
                self.assertEqual(policy.digest(FIXTURES / entry["path"]), entry["sha256"])
                case = self.fixture(entry["id"])
                result = self.evaluate(case["request"])
                self.assertEqual(result["data_result"], case["expected"]["data_result"])
                self.assertEqual(result["overall_result"], case["expected"]["overall_result"])
                checks = self.checks(result)
                for key, expected in case["expected"]["checks"].items():
                    self.assertEqual(checks[key]["result"], expected, key)
                self.assertEqual({key for key, check in checks.items() if check["result"] == "fail"},
                                 set(case["expected"]["failed_checks"]))
                if "canonical_publication_bridge" in case["expected"]:
                    self.assertEqual(result["canonical_publication_bridge"], case["expected"]["canonical_publication_bridge"])
                self.assertIs(result["submission_approved"], False)

    def test_successful_data_never_approves_submission_or_rendered_policy(self):
        result = self.evaluate(self.request("final-deposit-records"))
        self.assertEqual(result["data_result"], "pass")
        self.assertEqual(result["overall_result"], "partial")
        self.assertIs(result["submission_approved"], False)
        self.assertEqual(result["artifact"]["pdf_structure"], "unexecuted")
        self.assertEqual(self.checks(result)["POL01.RENDERED"]["result"], "unexecuted")
        self.assertEqual(self.checks(result)["POL02.RENDERED"]["result"], "unexecuted")
        self.assertTrue(result["human_checklist"])
        self.assertTrue(all(x["status"] == "human-review-required" and x["pdf_sha256"] == self.pdf_hash
                            for x in result["human_checklist"]))

    def test_conditional_matrix_has_satisfying_missing_and_inapplicable_cases(self):
        matrix = json.loads((FIXTURES / "applicability-matrix.json").read_text())
        rows = matrix["conditional_checks"]
        self.assertEqual(len(rows), 25)
        self.assertEqual(len({x["check"] for x in rows}), 25)
        for row in rows:
            for category, expected in (("satisfying", "pass"), ("missing_or_invalid", "fail"),
                                       ("not_applicable", "not-applicable")):
                with self.subTest(check=row["check"], category=category):
                    # The corpus test independently executes each referenced expectation.
                    case = self.fixture(row[category])
                    self.assertEqual(case["expected"]["checks"][row["check"]], expected)

    def test_observed_order_claims_are_not_an_input_interface(self):
        request = self.request()
        request["policy"]["observed_order"] = ["title", "abstract", "declaration"]
        with self.assertRaises(policy.PolicyError) as caught:
            self.evaluate(request)
        self.assertEqual(caught.exception.code, "input-invalid")

    def test_later_overrides_cannot_hide_invalid_lower_layers(self):
        for layer in ("metadata", "cli"):
            with self.subTest(layer=layer):
                request = self.request()
                if layer == "metadata":
                    request["layers"]["metadata"]["double_sided"] = "false"
                else:
                    request["layers"]["cli"] = ['double_sided="false"']
                request["layers"]["explicit"] = {"double_sided": False}
                with self.assertRaises(policy.PolicyError) as caught:
                    self.evaluate(request)
                self.assertEqual(caught.exception.code, "configuration-invalid")

    def test_all_five_layers_use_the_canonical_normalizer(self):
        request = self.request()
        request["layers"]["metadata"].update(layout="print", double_sided=False)
        request["layers"]["cli"] = ["double_sided=true"]
        request["layers"]["explicit"] = {"double_sided": False}
        bundle = policy.load_bundle(ROOT / "contracts/thesis/v1", policy.CONTRACT_SHA256)
        expected = bundle.normalize(request["layers"]["metadata"], bundle.parse_cli(request["layers"]["cli"]),
                                    request["layers"]["explicit"])["configuration"]
        self.assertIs(expected["double_sided"], False)
        self.assertEqual(self.evaluate(request)["configuration_sha256"], policy.configuration_digest(expected))

    def test_bool_is_not_a_count_or_percentage(self):
        for name in ("body", "footnotes"):
            with self.subTest(field=name):
                request = self.request()
                request["policy"]["word_count"][name] = False
                with self.assertRaises(policy.PolicyError):
                    self.evaluate(request)
        request = self.request("creative-agreed")
        request["policy"]["creative"]["dissertation_percent"] = True
        with self.assertRaises(policy.PolicyError):
            self.evaluate(request)

    def test_strict_json_rejects_duplicates_and_nonfinite_numbers(self):
        for value in ('{"a":1,"a":2}', '{"body":NaN}', '{"body":1e999}', '{"body":-1e999}'):
            with self.subTest(value=value):
                path = self.folder / "input.json"
                path.write_text(value)
                with self.assertRaises(policy.PolicyError):
                    policy.read_json(path)

    def test_policy_file_tampering_is_rejected(self):
        copy = self.folder / "policy"
        shutil.copytree(policy.POLICY_ROOT, copy)
        body = json.loads((copy / "profile.json").read_text())
        body["limits"]["doctoral"]["maximum"] = 1000000
        (copy / "profile.json").write_text(json.dumps(body))
        with self.assertRaises(policy.PolicyError) as caught:
            self.evaluate(self.request(), policy_root=copy)
        self.assertEqual(caught.exception.code, "policy-drift")

    def test_rehashed_policy_manifest_cannot_replace_the_source_pin(self):
        copy = self.folder / "policy"
        shutil.copytree(policy.POLICY_ROOT, copy)
        (copy / "profile.json").write_text('{}')
        manifest = json.loads((copy / "manifest.json").read_text())
        manifest["files"]["profile.json"] = policy.digest(copy / "profile.json")
        (copy / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaises(policy.PolicyError):
            policy.load_policy(copy)

    def test_recommendations_and_masters_maxima_are_separate(self):
        result = self.evaluate(self.request("above-advisory-target"))
        self.assertEqual(result["metrics"]["counted_words"], 95000)
        self.assertEqual(result["metrics"]["maximum_words"], 100000)
        self.assertEqual(result["metrics"]["recommended_words"], 80000)
        self.assertTrue(result["metrics"]["above_recommendation"])
        self.assertEqual(result["data_result"], "pass")
        result = self.evaluate(self.request("nonenglish-masters"))
        self.assertEqual(result["metrics"]["maximum_words"], 50000)
        self.assertEqual(result["metrics"]["recommended_words"], 40000)

    def test_footnotes_count_but_named_exclusions_do_not(self):
        request = self.request()
        for key in ("tables", "maps", "bibliographies", "appendices"):
            request["policy"]["word_count"][key] = 200000
        result = self.evaluate(request)
        self.assertEqual(result["metrics"]["counted_words"], 80000)
        request["policy"]["word_count"]["footnotes"] = 200
        result = self.evaluate(request)
        self.assertEqual(result["metrics"]["counted_words"], 80100)
        self.assertEqual(self.checks(result)["POL03.DECLARATION"]["result"], "fail")

    def test_exception_rejects_wrong_subject_course_purpose_authority_or_limit(self):
        edits = [("subject_sha256", "0" * 64), ("course", "OTHER"), ("purpose", "examination"), ("max_words", 109999)]
        for key, value in edits:
            with self.subTest(scope=key):
                request = self.request("approved-word-exception")
                request["policy"]["decisions"][0]["scope"][key] = value
                self.assertEqual(self.checks(self.evaluate(request))["POL03.EXCEPTION"]["result"], "fail")
        request = self.request("approved-word-exception")
        request["policy"]["decisions"][0]["authority"] = "author"
        self.assertEqual(self.checks(self.evaluate(request))["POL03.EXCEPTION"]["result"], "fail")

    def test_exception_rejects_expired_future_or_denied_records(self):
        for field, value in (("expires_on", "2026-11-14"), ("issued_on", "2026-11-16"), ("state", "denied")):
            request = self.request("approved-word-exception")
            request["policy"]["decisions"][0][field] = value
            self.assertEqual(self.checks(self.evaluate(request))["POL03.EXCEPTION"]["result"], "fail")

    def test_calendar_dates_and_assessment_types_are_validated(self):
        request = self.request("approved-word-exception")
        request["policy"]["decisions"][0]["issued_on"] = "2026-02-30"
        with self.assertRaises(policy.PolicyError):
            self.evaluate(request)
        for value in ("2026-11-15", True, datetime(2026, 11, 15)):
            with self.assertRaises(policy.PolicyError):
                self.evaluate(self.request(), as_of=value)

    def test_missing_or_altered_evidence_cannot_back_approval(self):
        request = self.request("approved-word-exception")
        request["policy"]["documents"][0]["sha256"] = "0" * 64
        result = self.evaluate(request)
        self.assertEqual(self.checks(result)["EVIDENCE.IDENTITIES"]["result"], "fail")
        self.assertEqual(self.checks(result)["POL03.EXCEPTION"]["result"], "fail")
        request["policy"]["documents"][0]["path"] = "missing.md"
        self.assertEqual(self.checks(self.evaluate(request))["POL03.EXCEPTION"]["result"], "fail")

    def test_separate_evidence_cannot_reuse_thesis_bytes(self):
        request = self.request("examination-records")
        for item in request["policy"]["documents"]:
            if item["kind"] == "originality-report":
                item.update(path=self.pdf.name, sha256=self.pdf_hash)
        result = self.evaluate(request, evidence_root=self.folder)
        self.assertEqual(self.checks(result)["POL07.ORIGINALITY"]["result"], "fail")

    def test_evidence_traversal_absolute_paths_and_symlinks_are_rejected(self):
        for value in ("../outside.md", str(self.pdf)):
            request = self.request("approved-word-exception")
            request["policy"]["documents"][0]["path"] = value
            with self.assertRaises(policy.PolicyError) as caught:
                self.evaluate(request)
            self.assertEqual(caught.exception.code, "evidence-path")
        link = self.folder / "linked.md"
        link.symlink_to(FIXTURES / "documents/approval.md")
        request = self.request("approved-word-exception")
        request["policy"]["documents"][0]["path"] = link.name
        with self.assertRaises(policy.PolicyError):
            self.evaluate(request, evidence_root=self.folder)

    def test_duplicate_document_and_decision_ids_do_not_overwrite_records(self):
        for group in ("documents", "decisions"):
            request = self.request("approved-word-exception")
            request["policy"][group].append(deepcopy(request["policy"][group][0]))
            with self.assertRaises(policy.PolicyError) as caught:
                self.evaluate(request)
            self.assertEqual(caught.exception.code, "duplicate-id")

    def test_summary_upper_bounds_are_inclusive_and_do_not_follow_ui_locale(self):
        for count, expected in ((10000, "pass"), (10001, "fail")):
            request = self.request("nonenglish-doctoral")
            request["layers"]["metadata"]["label_locale"] = "en"
            request["layers"]["metadata"]["metadata"]["english_summary"] = " ".join(["word"] * count)
            self.assertEqual(self.checks(self.evaluate(request))["POL04.SUMMARY"]["result"], expected)

    def test_rtp_stipend_and_fee_offset_both_trigger_the_exact_dated_literal(self):
        request = self.request("rtp-fee-offset")
        request["policy"]["funding"].update(rtp_fee_offset=False, rtp_stipend=True)
        self.assertEqual(self.checks(self.evaluate(request))["POL05.RTP"]["result"], "pass")
        ack = request["layers"]["metadata"]["metadata"]["funding"][0]["acknowledgement"]
        request["layers"]["metadata"]["metadata"]["funding"][0]["acknowledgement"] = ack.replace("10.82133/C42F-K220", "wrong-doi")
        self.assertEqual(self.checks(self.evaluate(request))["POL05.RTP"]["result"], "fail")

    def test_private_logs_are_not_emitted_and_embedded_log_claim_is_rejected(self):
        request = self.request("ai-assistance")
        request["policy"]["assistance"][0]["extent"] = "PRIVATE-SYNTHETIC-INPUT-SENTINEL"
        result = self.evaluate(request)
        self.assertNotIn("PRIVATE-SYNTHETIC-INPUT-SENTINEL", json.dumps(result))
        request["policy"]["assistance"][0]["full_private_log_embedded"] = True
        self.assertEqual(self.checks(self.evaluate(request))["POL05.ASSISTANCE"]["result"], "fail")

    def test_roles_may_overlap_without_invented_authorship_percentage_threshold(self):
        request = self.request("publication-coauthored")
        contributions = request["layers"]["metadata"]["metadata"]["publications"][0]["contributions"]
        self.assertEqual(sum(x["percentage"] for x in contributions), 140)
        self.assertEqual(self.checks(self.evaluate(request))["POL06.REGISTRY"]["result"], "pass")

    def test_nonai_assistance_cannot_claim_ai_authorship(self):
        for case in ("human-assistance", "digital-assistance"):
            with self.subTest(kind=case):
                request = self.request(case)
                request["policy"]["assistance"][0]["ai_authorship_claimed"] = True
                result = self.evaluate(request)
                self.assertEqual(self.checks(result)["POL05.AI"]["result"], "fail")
                self.assertEqual(result["data_result"], "fail")

    def test_exclusive_partition_cannot_substitute_unrelated_contributor_names(self):
        request = self.request("exclusive-partition")
        request["policy"]["publications"]["records"][0]["exclusive_partition"][0]["name"] = "Another person"
        self.assertEqual(self.checks(self.evaluate(request))["POL06.REGISTRY"]["result"], "fail")

    def test_all_five_official_statuses_have_explicit_canonical_bridge_semantics(self):
        for canonical, official in (("draft", "unpublished"), ("submitted", "submitted"), ("accepted", "accepted"), ("published", "published")):
            request = self.request("publication-coauthored")
            request["layers"]["metadata"]["metadata"]["publications"][0]["status"] = canonical
            request["policy"]["publications"]["records"][0]["official_status"] = official
            result = self.evaluate(request)
            self.assertEqual(self.checks(result)["POL06.REGISTRY"]["result"], "pass")
            self.assertEqual(result["canonical_publication_bridge"], "supported")
        result = self.evaluate(self.request("publication-in-revision"))
        self.assertEqual(result["canonical_publication_bridge"], "unsupported-in-revision")

    def test_signed_form_byte_identity_never_verifies_actual_signatures(self):
        result = self.evaluate(self.request("publication-coauthored"))
        self.assertEqual(self.checks(result)["POL06.FORMS"]["result"], "pass")
        review = [x for x in result["human_checklist"] if x["id"] == "PUBLICATIONS.SIGNEDFORMS"]
        self.assertEqual(review[0]["status"], "human-review-required")

    def test_publication_rights_unknown_license_and_publisher_copy_boundaries(self):
        request = self.request("publication-coauthored")
        publication = request["policy"]["publications"]["records"][0]
        publication["rights_basis"] = "unknown"
        with self.assertRaises(policy.PolicyError):
            self.evaluate(request)
        publication["rights_basis"] = "pending"
        self.assertEqual(self.checks(self.evaluate(request))["POL06.RIGHTS"]["result"], "fail")
        publication["rights_basis"] = "open-license"
        publication["license_url"] = "https://creativecommons.org/licenses/by/4.0/"
        self.assertEqual(self.checks(self.evaluate(request))["POL06.RIGHTS"]["result"], "fail")
        record = FIXTURES / "documents/rights-record.md"
        request["policy"]["documents"].append({"id": "license-record", "path": "documents/rights-record.md",
            "sha256": policy.digest(record), "kind": "rights-record", "classification": "synthetic"})
        publication["rights_ref"] = "license-record"
        result = self.evaluate(request)
        self.assertEqual(self.checks(result)["POL06.RIGHTS"]["result"], "pass")
        self.assertTrue(any(x["id"] == "PUBLICATIONS.INTEGRITY" for x in result["human_checklist"]))
        publication.update(rights_basis="owned", version="publisher")
        request["layers"]["metadata"]["metadata"]["publications"][0]["version"] = "publisher"
        self.assertEqual(self.checks(self.evaluate(request))["POL06.RIGHTS"]["result"], "pass")
        del publication["rights_ref"]
        self.assertEqual(self.checks(self.evaluate(request))["POL06.RIGHTS"]["result"], "fail")

    def test_manual_adjustment_cannot_produce_a_negative_total(self):
        request = self.request("count-adjustment")
        request["policy"]["word_count"]["adjustments"][0]["delta"] = -200000
        report = self.evaluate(request)
        self.assertEqual(self.checks(report)["POL03.ADJUSTMENTS"]["result"], "fail")
        self.assertEqual(report["data_result"], "fail")
        self.assertNotIn("counted_words", report["metrics"])

    def test_updated_pdf_invalidates_originality_and_supervisor_bindings(self):
        request = self.request("examination-records")
        self.pdf.write_bytes(self.pdf.read_bytes() + b"% changed bytes\n")
        result = self.evaluate(request)
        self.assertNotEqual(result["artifact"]["sha256"], self.pdf_hash)
        checks = self.checks(result)
        self.assertEqual(checks["POL07.ORIGINALITY"]["result"], "fail")
        self.assertEqual(checks["POL07.REVIEW"]["result"], "fail")
        self.assertTrue(all(x["pdf_sha256"] == result["artifact"]["sha256"] for x in result["human_checklist"]))

    def test_actual_tes_filename_is_checked_without_inventing_extra_prohibitions(self):
        for name, expected in (("thesis,#.pdf", "fail"), ("named thesis-final_1.pdf", "pass")):
            path = self.folder / name
            path.write_bytes(synthetic_pdf())
            self.assertEqual(self.checks(self.evaluate(self.request(), pdf_path=path))["POL07.FILE"]["result"], expected)

    def test_non_pdf_or_missing_artifacts_do_not_get_a_checklist(self):
        self.pdf.write_text("Not PDF bytes")
        with self.assertRaises(policy.PolicyError) as caught:
            self.evaluate(self.request())
        self.assertEqual(caught.exception.code, "artifact-invalid")
        self.pdf.unlink()
        with self.assertRaises(policy.PolicyError):
            self.evaluate(self.request())

    def run_cli(self, request_text):
        output_root = ROOT / "build/submission-policy"
        output_root.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(dir=output_root))
        self.addCleanup(shutil.rmtree, output)
        input_path = self.folder / "request.json"
        input_path.write_text(request_text)
        report = output / "report.json"
        report.write_text('{"submission_approved":true,"overall_result":"pass"}')
        command = [sys.executable, str(ROOT / "scripts/submission_policy.py"), "--input", str(input_path),
                   "--pdf", str(self.pdf), "--evidence-root", str(FIXTURES), "--report", str(report), "--as-of", "2026-11-15"]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
        return result, json.loads(report.read_text())

    def test_cli_success_is_explicitly_partial_and_not_submission_authorisation(self):
        process, report = self.run_cli(json.dumps(self.request()))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("overall: partial", process.stdout)
        self.assertIs(report["submission_approved"], False)

    def test_cli_invalid_json_replaces_stale_success_without_echoing_private_input(self):
        process, report = self.run_cli('{"PRIVATE-INPUT":')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(report["data_result"], "invalid")
        self.assertIs(report["submission_approved"], False)
        self.assertNotIn("PRIVATE-INPUT", process.stderr + json.dumps(report))

    def test_cli_policy_failure_has_nonzero_status_and_fresh_failure_report(self):
        process, report = self.run_cli(json.dumps(self.request("unapproved-word-exception")))
        self.assertEqual(process.returncode, 1, process.stderr)
        self.assertEqual(report["overall_result"], "fail")

    def test_output_guard_rejects_source_aliases_and_hardlinks_before_mutation(self):
        output_root = ROOT / "build/submission-policy"
        output_root.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(dir=output_root))
        self.addCleanup(shutil.rmtree, output)
        protected = output / "input.json"
        protected.write_text('sensitive input')
        with self.assertRaises(policy.PolicyError):
            policy.output_guard(protected, [protected])
        linked = output / "linked.json"
        os.link(protected, linked)
        with self.assertRaises(policy.PolicyError):
            policy.output_guard(linked, [])
        self.assertEqual(protected.read_text(), 'sensitive input')


    def test_output_guard_rejects_directories_and_parent_symlinks(self):
        output_root = ROOT / "build/submission-policy"
        output_root.mkdir(parents=True, exist_ok=True)
        output = Path(tempfile.mkdtemp(dir=output_root))
        self.addCleanup(shutil.rmtree, output)
        target = output / "directory"
        target.mkdir()
        with self.assertRaises(policy.PolicyError):
            policy.output_guard(target, [])
        link = output / "alias"
        link.symlink_to(target, target_is_directory=True)
        with self.assertRaises(policy.PolicyError):
            policy.output_guard(link / "report.json", [])
        relative = Path(os.path.relpath(link / "report.json", Path.cwd()))
        with self.assertRaises(policy.PolicyError):
            policy.output_guard(relative, [])

    def test_fixture_oracle_rejects_false_approval_and_erased_expected_failures(self):
        for case_name, mutation in (("draft-baseline", "approval"), ("unapproved-word-exception", "failure")):
            case = self.fixture(case_name)
            report = self.evaluate(case["request"])
            if mutation == "approval":
                report["submission_approved"] = True
            else:
                for check in report["checks"]:
                    if check["result"] == "fail":
                        check["result"] = "pass"
            checks = harness.assertions(case, report, self.pdf_hash)
            self.assertTrue(any(not item["passed"] for item in checks))

    def test_fixture_gate_wrong_compiler_removes_stale_outputs_and_restores_runner(self):
        output = self.folder / "fixture-gate"
        output.mkdir()
        (output / "binding.pdf").write_bytes(b"stale PDF")
        (output / "report.json").write_text('{"passed":true}')
        (output / "draft-baseline.json").write_text('{"overall_result":"pass"}')
        saved = harness.verify.ROOT, harness.verify.OUTPUT
        with patch.object(harness, "OUTPUT", output), patch.object(harness.verify, "run", return_value="typst 0.14.0") as run:
            self.assertEqual(harness.main([]), 1)
        run.assert_called_once()
        self.assertEqual((harness.verify.ROOT, harness.verify.OUTPUT), saved)
        self.assertFalse((output / "binding.pdf").exists())
        self.assertFalse((output / "draft-baseline.json").exists())
        self.assertIs(json.loads((output / "report.json").read_text())["passed"], False)

    def test_fixture_gate_tool_failure_retains_only_a_failed_receipt(self):
        output = self.folder / "fixture-gate"
        with patch.object(harness, "OUTPUT", output), patch.object(harness.verify, "run", side_effect=harness.verify.VerificationError("Synthetic command failure")):
            self.assertEqual(harness.main([]), 1)
        report = json.loads((output / "report.json").read_text())
        self.assertIs(report["passed"], False)
        self.assertEqual(report["cases"], [])
        self.assertTrue(report["errors"])
        self.assertFalse((output / "binding.pdf").exists())

    def test_cli_report_write_failure_returns_invalid_without_success(self):
        request = self.folder / "request.json"
        request.write_text(json.dumps(self.request()))
        destination = ROOT / "build/submission-policy/write-failure/report.json"
        with patch.object(Path, "write_text", side_effect=OSError("Synthetic unavailable output")):
            status = policy.main(["--input", str(request), "--pdf", str(self.pdf),
                                  "--report", str(destination), "--as-of", "2026-11-15"])
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
