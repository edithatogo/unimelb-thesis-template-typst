"""Receipt integrity controls; synthetic records are not rendered acceptance."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from datetime import timedelta
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import requirement_evidence as evidence

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = runpy.run_path(str(ROOT / "tests/evidence/fixture_support.py"))
NOW, NATIVE, PROPERTIES = (FIXTURES[key] for key in ("NOW", "NATIVE", "PROPERTIES"))
write_json, git = FIXTURES["write_json"], FIXTURES["git"]


class RequirementEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evidence.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        cls.container = tempfile.TemporaryDirectory(prefix="unit-source-", dir=evidence.OUTPUT_ROOT)
        cls.base = Path(cls.container.name) / "source"
        cls.fixture = FIXTURES["make_fixture"](cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.container.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="unit-", dir=evidence.OUTPUT_ROOT)
        self.parent = Path(self.temp.name)
        self.source = self.parent / "source"
        shutil.copytree(self.base, self.source)
        self.request, self.native, self.properties = deepcopy(self.fixture)
        self.output = self.parent / "receipt"
        self.receipt = self.output / "verification-receipt.json"

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        write_json(self.source / NATIVE, self.native)
        write_json(self.source / PROPERTIES, self.properties)
        self.request["native"]["sha256"] = evidence.digest(self.source / NATIVE)
        self.request["properties"]["sha256"] = evidence.digest(self.source / PROPERTIES)

    def produce(self, **options):
        self.save()
        return evidence.produce(self.request, source_root=self.source, output=self.output, now=NOW, **options)

    def verify(self, **options):
        values = {"source_root": self.source, "expected_revision": self.request["revision"],
                  "trusted_sha256": evidence.digest(self.receipt), "now": NOW,
                  "logs": self.parent / "consumer-probes"}
        values.update(options)
        return evidence.verify_receipt(self.receipt, **values)

    def reject(self, code, call):
        with self.assertRaises(evidence.ReceiptError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def repin(self, name):
        wrapper = evidence.read_json(self.receipt)
        next(item for item in wrapper["artifacts"] if item["path"] == name)["sha256"] = evidence.digest(self.output / name)
        write_json(self.receipt, wrapper)

    def test_central_wrapper_and_all_requirement_ids_are_bound_without_promotion(self):
        wrapper, sidecar = self.produce()
        self.assertEqual(wrapper["result"], "partial")
        self.assertEqual(len(sidecar["requirements"]), 51)
        expected_ids = {item["id"] for item in evidence.load_profile()["catalogue"]["requirements"]}
        self.assertEqual({item["id"] for item in sidecar["requirements"]}, expected_ids)
        self.assertEqual({item["result"] for item in sidecar["requirements"]}, {"blocked", "unexecuted"})
        self.assertFalse(sidecar["full_programme_qualified"])
        self.assertFalse(sidecar["institutional_approval"])
        self.assertFalse(sidecar["blind_safe"])
        self.assertTrue(all(item["source_refs"] for item in sidecar["requirements"]))
        self.assertTrue(self.verify()["integrity_verified"])

    def test_missing_purpose_and_identity_do_not_invent_conditional_applicability(self):
        _, sidecar = self.produce()
        rows = {row["id"]: row for row in sidecar["requirements"]}
        for identifier in ("COR-04", "POL-03", "DEP-02", "WEB-01"):
            self.assertEqual(rows[identifier]["applicability"], "unassessed")
            self.assertTrue(rows[identifier]["programme_required"])
        for identifier in ("CON-01", "TYP-04", "ACC-01"):
            self.assertEqual(rows[identifier]["applicability"], "applicable")
        self.assertTrue(all(row["applicability_predicate"] for row in rows.values()))

    def test_native_bytes_and_legacy_property_scope_are_preserved(self):
        _, sidecar = self.produce()
        self.assertEqual((self.output / sidecar["native"]["artifact"]).read_bytes(), (self.source / NATIVE).read_bytes())
        self.assertEqual((self.output / sidecar["properties"]["artifact"]).read_bytes(), (self.source / PROPERTIES).read_bytes())
        self.assertEqual(sidecar["properties"]["exact_revision_execution"], "uncollected-legacy-report")
        self.assertIsNone(sidecar["provenance"]["normalized_configuration"])
        self.assertIsNone(sidecar["producer"]["revision"])
        self.assertEqual(sidecar["human_decisions"]["records"], [])

    def test_same_tree_other_commit_cannot_relabel_native_execution(self):
        git(self.source, "-c", "user.name=Synthetic Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "--allow-empty", "-q", "-m", "Different commit, same tree")
        self.assertEqual(git(self.source, "rev-parse", "HEAD^{tree}"), self.request["tree"])
        self.request["revision"] = git(self.source, "rev-parse", "HEAD")
        self.reject("native-wrong-revision", self.produce)

    def test_wrong_source_revision_or_tree_is_rejected(self):
        original = deepcopy(self.request)
        for field, code in (("revision", "wrong-revision"), ("tree", "wrong-tree")):
            with self.subTest(field=field):
                self.request = dict(original, **{field: "0" * 40})
                self.reject(code, self.produce)

    def test_dirty_tracked_or_untracked_source_cannot_be_certified(self):
        path = self.source / "thesis.typ"
        original = path.read_bytes()
        path.write_bytes(original + b"Changed\n")
        self.reject("dirty-source", self.produce)
        path.write_bytes(original)
        (self.source / "unexpected-source.typ").write_text("Untracked input")
        self.reject("dirty-source", self.produce)

    def test_nonroot_source_directory_is_rejected(self):
        self.reject("source-root", lambda: evidence.source_snapshot(self.source / "scripts", self.request["revision"],
                    self.request["tree"], self.parent / "probe"))

    def test_committed_symbolic_link_source_is_unsupported(self):
        (self.source / "linked.typ").symlink_to("thesis.typ")
        git(self.source, "add", "linked.typ")
        git(self.source, "-c", "user.name=Synthetic Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Synthetic link control")
        self.reject("unsupported-source-entry", lambda: evidence.source_snapshot(
            self.source, git(self.source, "rev-parse", "HEAD"), git(self.source, "rev-parse", "HEAD^{tree}"), self.parent / "probe"))

    def test_native_revision_and_clean_flag_are_required(self):
        for field, value in (("source_revision", "f" * 40), ("source_dirty", True), ("source_dirty", 0)):
            with self.subTest(field=field, value=value):
                self.native = dict(self.fixture[1], **{field: value})
                self.reject("native-wrong-revision", self.produce)

    def test_source_digest_cannot_point_to_another_file_version(self):
        self.native["verifier_sha256"] = "0" * 64
        self.reject("source-evidence-mismatch", self.produce)

    def test_missing_required_primary_or_native_output_fails(self):
        self.save()
        for name in (NATIVE, PROPERTIES, "build/verification/thesis.pdf", "build/verification/sample-chapter.txt",
                     "build/verification/synthetic.log"):
            path = self.source / name
            saved = path.read_bytes()
            path.unlink()
            with self.subTest(name=name):
                self.reject("missing-artifact", lambda: evidence.produce(self.request, source_root=self.source, output=self.output, now=NOW))
            path.write_bytes(saved)

    def test_trusted_native_digest_and_declared_output_digest_are_enforced(self):
        self.save()
        self.request["native"]["sha256"] = "0" * 64
        self.reject("artifact-tampered", lambda: evidence.produce(self.request, source_root=self.source, output=self.output, now=NOW))
        self.native["documents"][0]["pdf_sha256"] = "0" * 64
        self.reject("artifact-tampered", self.produce)

    def test_missing_path_or_digest_cannot_hide_a_required_output(self):
        for field, code in (("pdf", "false-native-pass"), ("pdf_sha256", "false-native-pass")):
            with self.subTest(field=field):
                self.native = deepcopy(self.fixture[1])
                del self.native["documents"][0][field]
                self.reject(code, self.produce)
        self.native = deepcopy(self.fixture[1])
        self.native["rendered_corpus"]["log_sha256"] = "0" * 64
        self.reject("missing-artifact-path", self.produce)
        self.native["rendered_corpus"] = {"result": "pass", "log": "build/verification/synthetic.log"}
        self.reject("missing-artifact-digest", self.produce)

    def test_corpus_omission_or_nonpass_cannot_hide_behind_native_success(self):
        for value in (None, {"result": "fail"}, {"result": "unexecuted"}, {"result": "invented"}):
            with self.subTest(value=value):
                self.native = deepcopy(self.fixture[1])
                self.native["navigation_corpus"] = value
                code = "missing-native-corpus" if value is None else ("corpus-interface" if value["result"] == "invented" else "false-native-pass")
                self.reject(code, self.produce)

    def test_required_document_inventory_does_not_accept_duplicate_or_empty_documents(self):
        for documents in ([], [self.fixture[1]["documents"][0]] * 2):
            with self.subTest(documents=documents):
                self.native["documents"] = documents
                self.reject("false-native-pass", self.produce)

    def test_stale_future_or_reversed_native_times_are_rejected(self):
        for changes in ({"started_at_utc": "2026-11-15T02:58:00Z"},
                        {"finished_at_utc": "2026-11-15T05:00:00Z"},
                        {"finished_at_utc": "2026-11-15T02:59:30Z"},
                        {"started_at_utc": "2026-02-30T03:00:00Z"}):
            with self.subTest(changes=changes):
                self.native = dict(self.fixture[1], **changes)
                self.reject("invalid-time" if "02-30" in str(changes) else "stale-native-report", self.produce)

    def test_receipt_expiration_and_future_issue_time_are_enforced(self):
        self.produce()
        self.reject("review-expired", lambda: self.verify(now=NOW + timedelta(days=2)))
        self.reject("review-expired", lambda: self.verify(now=NOW - timedelta(seconds=1)))
        self.request["run"]["review_by"] = "2026-11-15T03:59:00Z"
        self.reject("review-expired", self.produce)

    def test_invalid_native_types_tool_versions_and_budget_are_rejected(self):
        cases = (({"schema_version": True}, "native-interface"), ({"passed": 1}, "native-interface"),
                 ({"compiler": "typst 0.14.2"}, "compiler-mismatch"), ({"python_version": None}, "tool-identities"),
                 ({"command_timeout_seconds": 600}, "runtime-budget"), ({"tool_versions": {}}, "tool-identities"),
                 ({"executables": {}}, "tool-identities"))
        for changes, code in cases:
            with self.subTest(changes=changes):
                self.native = dict(self.fixture[1], **changes)
                self.reject(code, self.produce)

    def test_malformed_or_missing_command_cannot_be_skipped(self):
        for changes in ({"exit_code": False}, {"exit_code": None}, {"duration_seconds": -1},
                        {"expected_exit_code": None}, {"timed_out": 0}, {"timeout_seconds": 61}):
            with self.subTest(changes=changes):
                self.native = deepcopy(self.fixture[1])
                self.native["commands"][0].update(changes)
                self.reject("command-interface", self.produce)
        self.native["commands"] = [{}]
        self.reject("missing-commands", self.produce)

    def test_timeout_or_unexpected_exit_cannot_be_a_native_pass(self):
        for changes in ({"exit_code": 1}, {"timed_out": True}):
            with self.subTest(changes=changes):
                self.native = deepcopy(self.fixture[1])
                self.native["commands"][0].update(changes)
                self.reject("false-native-pass", self.produce)
        self.native = deepcopy(self.fixture[1])
        self.native["commands"][0].update(exit_code=1, expected_exit_code=1)
        _, sidecar = self.produce()
        self.assertEqual(sidecar["commands"][0]["exit_code"], 1)
        self.assertEqual(sidecar["overall_result"], "partial")

    def test_recorded_native_or_property_failure_remains_failure(self):
        self.native["passed"] = False
        self.native["rendered_corpus"]["result"] = "fail"
        wrapper, sidecar = self.produce()
        self.assertEqual(wrapper["result"], "fail")
        self.assertEqual(next(x for x in sidecar["requirements"] if x["id"] == "COR-01")["result"], "executed-fail")
        self.assertEqual(self.verify()["result"], "fail")
        self.native = deepcopy(self.fixture[1])
        self.properties["passed"] = False
        self.properties["failures"] = [{"test": "test_synthetic_1", "traceback": "Synthetic failure"}]
        self.assertEqual(self.produce()[0]["result"], "fail")

    def test_property_under_run_or_changed_measured_source_is_rejected(self):
        self.properties["generated_cases"]["test_synthetic_0"] = 63
        self.reject("property-under-run", self.produce)
        self.properties = deepcopy(self.fixture[2])
        self.properties["source_sha256"]["scripts/manage_terms.py"] = "0" * 64
        self.reject("source-evidence-mismatch", self.produce)

    def test_property_pass_cannot_contain_skips_failures_or_boolean_threshold(self):
        for changes in ({"skipped": ["synthetic skip"]}, {"errors": ["synthetic error"]},
                        {"failures": ["synthetic failure"]}, {"failure_threshold": False},
                        {"harness_error": "synthetic missing generator"}):
            with self.subTest(changes=changes):
                self.properties = dict(self.fixture[2], **changes)
                self.reject("false-property-pass", self.produce)

    def test_property_interface_and_complete_source_inventory_are_required(self):
        for changes, code in (({"tests_run": 0}, "property-interface"), ({"cases_per_property": 1}, "property-interface"),
                              ({"seed": True}, "property-interface"), ({"source_sha256": {}}, "property-sources")):
            with self.subTest(changes=changes):
                self.properties = dict(self.fixture[2], **changes)
                self.reject(code, self.produce)

    def test_unregistered_required_sidecar_stays_unsupported_and_hash_bound(self):
        path = self.source / "build/policy.json"
        write_json(path, {"schema_version": "99", "submission_approved": True})
        descriptor = {"id": "policy", "role": "policy", "path": "build/policy.json", "sha256": evidence.digest(path),
                      "schema_version": "99", "required": True}
        self.request["sidecars"] = [descriptor]
        wrapper, sidecar = self.produce()
        self.assertEqual(wrapper["result"], "partial")
        self.assertEqual(sidecar["sidecars"][0]["status"], "unsupported")
        self.assertFalse(sidecar["institutional_approval"])
        self.assertTrue(self.verify()["integrity_verified"])
        self.request["sidecars"].append(deepcopy(descriptor))
        self.reject("duplicate-sidecar", self.produce)

    def test_wrapper_digest_is_mandatory_and_commit_specific(self):
        self.produce()
        self.reject("missing-trust-anchor", lambda: self.verify(trusted_sha256=None))
        self.reject("wrapper-tampered", lambda: self.verify(trusted_sha256="0" * 64))
        self.reject("wrong-revision", lambda: self.verify(expected_revision="0" * 40))

    def test_copied_output_tamper_and_missing_file_are_detected(self):
        _, sidecar = self.produce()
        path = self.output / next(x["path"] for x in sidecar["artifacts"] if x["path"].endswith("thesis.pdf"))
        path.write_bytes(b"Counterfeit bytes")
        self.reject("artifact-tampered", self.verify)
        path.unlink()
        self.reject("missing-artifact", self.verify)

    def test_required_sidecar_or_artifact_cannot_be_removed_from_wrapper(self):
        self.produce()
        wrapper = evidence.read_json(self.receipt)
        wrapper["artifacts"] = [x for x in wrapper["artifacts"] if x["path"] != "requirement-status.json"]
        write_json(self.receipt, wrapper)
        self.reject("missing-sidecar", self.verify)
        self.produce()
        wrapper = evidence.read_json(self.receipt)
        wrapper["artifacts"].append(deepcopy(wrapper["artifacts"][0]))
        write_json(self.receipt, wrapper)
        self.reject("duplicate-artifact", self.verify)

    def test_rehashed_status_or_clause_forgery_is_independently_rejected(self):
        for field, value in (("result", "executed-pass"), ("implementation_state", "implemented"),
                             ("applicability_reason", "Not required because a caller says so")):
            with self.subTest(field=field):
                self.produce()
                path = self.output / "requirement-status.json"
                sidecar = evidence.read_json(path)
                sidecar["requirements"][0][field] = value
                write_json(path, sidecar)
                self.repin(path.name)
                self.reject("sidecar-semantic-drift", self.verify)
        self.produce()
        path = self.output / "requirement-status.json"
        sidecar = evidence.read_json(path)
        sidecar["requirements"][0]["source_refs"][0]["clause"] = "Invented clause"
        write_json(path, sidecar)
        self.repin(path.name)
        self.reject("sidecar-semantic-drift", self.verify)

    def test_duplicate_or_missing_requirement_ids_cannot_replace_complete_status(self):
        for count in (50, 51):
            with self.subTest(count=count):
                self.produce()
                path = self.output / "requirement-status.json"
                sidecar = evidence.read_json(path)
                sidecar["requirements"] = sidecar["requirements"][:count]
                sidecar["requirements"][-1] = deepcopy(sidecar["requirements"][0])
                write_json(path, sidecar)
                self.repin(path.name)
                self.reject("invalid-schema" if count == 50 else "sidecar-semantic-drift", self.verify)

    def test_rehashed_readable_report_and_wrapper_result_tamper_are_detected(self):
        self.produce()
        path = self.output / "requirements.md"
        path.write_text("# Submission approved\n")
        self.repin(path.name)
        self.reject("readable-report-drift", self.verify)
        self.produce()
        wrapper = evidence.read_json(self.receipt)
        wrapper["result"] = "pass"
        write_json(self.receipt, wrapper)
        self.reject("wrapper-semantic-drift", self.verify)

    def test_institutional_approval_or_blind_safe_promotion_is_forbidden(self):
        self.produce()
        path = self.output / "requirement-status.json"
        sidecar = evidence.read_json(path)
        sidecar["institutional_approval"] = True
        sidecar["blind_safe"] = True
        write_json(path, sidecar)
        self.repin(path.name)
        self.reject("invalid-schema", self.verify)

    def test_unsafe_input_paths_and_artifact_parent_symlinks_are_rejected(self):
        for name in ("/tmp/file", "../file", "build/../file", "build//file", "build\\file", "C:file", "build/./file"):
            with self.subTest(name=name):
                self.reject("unsafe-path", lambda: evidence.safe_relative(name))
        (self.source / "build/link").symlink_to(self.source / "build/verification", target_is_directory=True)
        self.request["native"]["path"] = "build/link/report.json"
        self.reject("unsafe-path", self.produce)

    def test_relative_internal_parent_symlink_cannot_bypass_output_guard(self):
        real = self.parent / "real-output"
        real.mkdir()
        linked = self.parent / "link-output"
        linked.symlink_to(real, target_is_directory=True)
        old = Path.cwd()
        try:
            os.chdir(ROOT)
            self.reject("unsafe-output", lambda: evidence.output_directory((linked / "report").relative_to(ROOT)))
        finally:
            os.chdir(old)

    def test_hardlinked_or_symbolic_output_cannot_overwrite_input(self):
        self.output.mkdir()
        source = self.source / "thesis.typ"
        original = source.read_bytes()
        os.link(source, self.receipt)
        self.reject("unsafe-output", self.produce)
        self.assertEqual(source.read_bytes(), original)
        self.receipt.unlink()
        self.receipt.symlink_to(source)
        self.reject("unsafe-output", self.produce)
        self.assertEqual(source.read_bytes(), original)

    def test_primary_and_nested_native_inputs_cannot_be_inside_output(self):
        self.output.mkdir()
        request_path = self.output / "request.json"
        write_json(request_path, self.request)
        original = request_path.read_bytes()
        self.reject("unsafe-output", lambda: self.produce(protected_paths=[request_path]))
        self.assertEqual(request_path.read_bytes(), original)
        self.output = self.source / "build/requirement-evidence/collision"
        self.output.mkdir(parents=True)
        nested = self.output / "requirements.md"
        nested.write_text("Required original native artifact\n")
        self.native["documents"][0].update(text=nested.relative_to(self.source).as_posix(), text_sha256=evidence.digest(nested))
        # The source lives under the helper's dedicated test output root, so this
        # path is allowed lexically; only declared-input protection rejects it.
        self.reject("unsafe-output", self.produce)
        self.assertEqual(nested.read_text(), "Required original native artifact\n")

    def test_existing_source_probe_log_link_is_not_followed_and_runner_is_restored(self):
        logs = self.parent / "probe"
        logs.mkdir()
        original = (self.source / "thesis.typ").read_bytes()
        (logs / "root.log").symlink_to(self.source / "thesis.typ")
        state = evidence.runner.ROOT, evidence.runner.OUTPUT
        self.reject("unsafe-output", lambda: evidence.source_snapshot(self.source, self.request["revision"], self.request["tree"], logs))
        self.assertEqual((evidence.runner.ROOT, evidence.runner.OUTPUT), state)
        self.assertEqual((self.source / "thesis.typ").read_bytes(), original)

    def test_failed_attempt_invalidates_previous_success_without_old_sidecar(self):
        self.produce()
        del self.request["tree"]
        self.reject("invalid-schema", self.produce)
        self.assertEqual(evidence.read_json(self.receipt)["result"], "fail")
        self.assertFalse((self.output / "requirement-status.json").exists())
        self.assertFalse((self.output / "requirements.md").exists())

    def test_cli_malformed_request_invalidates_old_receipt_without_echoing_input(self):
        self.produce()
        bad = self.parent / "request.json"
        bad.write_text('{"private-sentinel":')
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = evidence.main(["produce", "--request", str(bad), "--source-root", str(self.source), "--output", str(self.output)])
        self.assertEqual(code, 2)
        self.assertNotIn("private-sentinel", err.getvalue())
        self.assertEqual(evidence.read_json(self.receipt)["result"], "fail")
        self.assertFalse((self.output / "requirement-status.json").exists())

    def test_missing_duplicate_key_or_nonfinite_json_is_rejected(self):
        path = self.parent / "malformed.json"
        for raw in ('{"x":1,"x":2}', "1e999", "NaN", "{", "[true] false"):
            with self.subTest(raw=raw):
                path.write_text(raw)
                self.reject("invalid-json", lambda: evidence.read_json(path))
        self.reject("invalid-json", lambda: evidence.read_json(self.parent / "missing.json"))
        with patch.object(evidence, "MAX_JSON_BYTES", 1):
            self.reject("report-too-large", lambda: evidence.read_json(path))

    def test_profile_bytes_and_exact_central_schema_identity_are_pinned(self):
        profile = self.parent / "profile"
        shutil.copytree(evidence.PROFILE, profile)
        (profile / "adapters.json").write_text("{}")
        self.reject("profile-drift", lambda: evidence.load_profile(profile))
        with patch.object(evidence, "CENTRAL_BLOB", "0" * 40):
            self.reject("central-schema-drift", evidence.load_profile)

    def test_artifact_change_during_consumption_is_rejected(self):
        self.save()
        source = evidence.source_snapshot(self.source, self.request["revision"], self.request["tree"], self.parent / "probe")
        inputs = evidence.Inputs(self.source, self.source, source)
        inputs.artifact(NATIVE, self.request["native"]["sha256"])
        (self.source / NATIVE).write_text("{}")
        self.reject("artifact-changed-during-read", inputs.unchanged)

    def test_source_change_between_snapshots_prevents_receipt_completion(self):
        original = evidence.source_snapshot
        calls = 0

        def mutate_after_snapshot(*args, **kwargs):
            nonlocal calls
            value = original(*args, **kwargs)
            calls += 1
            if calls == 2:
                value["inventory_sha256"] = "0" * 64
            return value

        with patch.object(evidence, "source_snapshot", side_effect=mutate_after_snapshot):
            self.reject("source-changed-during-read", self.produce)
        self.assertEqual(evidence.read_json(self.receipt)["result"], "fail")

    def test_actual_source_probe_failure_preserves_runner_state(self):
        state = evidence.runner.ROOT, evidence.runner.OUTPUT
        with patch.object(evidence.runner, "run", side_effect=evidence.runner.VerificationError("Synthetic Git failure")):
            self.reject("source-probe-failed", lambda: evidence.source_snapshot(self.source, self.request["revision"],
                        self.request["tree"], self.parent / "probe"))
        self.assertEqual((evidence.runner.ROOT, evidence.runner.OUTPUT), state)

    def test_wrapper_replacement_after_hash_cannot_change_the_parsed_commit(self):
        self.produce()
        valid = self.receipt.read_bytes()
        unrelated = evidence.read_json(self.receipt)
        unrelated["revision"] = "0" * 40
        write_json(self.receipt, unrelated)
        trusted = evidence.digest(self.receipt)
        original = evidence.digest

        def replace_after_hash(path):
            result = original(path)
            if Path(path) == self.receipt:
                self.receipt.write_bytes(valid)
            return result

        with patch.object(evidence, "digest", side_effect=replace_after_hash):
            self.reject("wrong-revision", lambda: evidence.verify_receipt(self.receipt, source_root=self.source,
                expected_revision=self.request["revision"], trusted_sha256=trusted, now=NOW,
                logs=self.parent / "consumer-probes"))

    def test_consumer_probe_logs_cannot_overwrite_the_wrapper(self):
        self.produce()
        alias = self.output / "root.log"
        alias.write_bytes(self.receipt.read_bytes())
        original = alias.read_bytes()
        self.reject("unsafe-output", lambda: evidence.verify_receipt(alias, source_root=self.source,
                    expected_revision=self.request["revision"], trusted_sha256=evidence.digest(alias),
                    now=NOW, logs=self.output))
        self.assertEqual(alias.read_bytes(), original)

    def test_sidecar_replacement_after_hash_cannot_extend_its_review_window(self):
        self.produce()
        path = self.output / "requirement-status.json"
        valid = path.read_bytes()
        expired = evidence.read_json(path)
        expired["review_by"] = expired["request"]["run"]["review_by"] = "2026-11-15T03:59:00Z"
        write_json(path, expired)
        self.repin(path.name)
        trusted = evidence.digest(self.receipt)
        original = evidence.digest

        def replace_after_hash(target):
            result = original(target)
            if Path(target) == path:
                path.write_bytes(valid)
            return result

        with patch.object(evidence, "digest", side_effect=replace_after_hash):
            self.reject("review-expired", lambda: evidence.verify_receipt(self.receipt, source_root=self.source,
                expected_revision=self.request["revision"], trusted_sha256=trusted, now=NOW,
                logs=self.parent / "consumer-probes"))

    def test_consumer_after_probe_directory_cannot_contain_a_required_artifact(self):
        self.produce()
        before = self.parent / "before"
        after = before.with_name("consumer-after")
        shutil.copytree(self.output, after)
        protected = after / "verification-receipt.json"
        original = protected.read_bytes()
        self.reject("unsafe-output", lambda: evidence.verify_receipt(protected, source_root=self.source,
                    expected_revision=self.request["revision"], trusted_sha256=evidence.digest(protected), now=NOW, logs=before))
        self.assertEqual(protected.read_bytes(), original)

    def test_exact_copied_artifact_buffer_must_match_its_digest(self):
        self.save()
        target = self.source / "build/verification/thesis.pdf"
        original = Path.read_bytes

        def changed_buffer(path):
            data = original(path)
            return b"Transient counterfeit artifact" if path == target else data

        with patch.object(Path, "read_bytes", changed_buffer):
            self.reject("artifact-tampered", lambda: evidence.produce(self.request, source_root=self.source,
                        output=self.output, now=NOW))

    def test_native_json_parser_uses_the_captured_hash_checked_buffer(self):
        self.save()
        source = evidence.source_snapshot(self.source, self.request["revision"], self.request["tree"], self.parent / "probe")
        inputs = evidence.Inputs(self.source, self.source, source)
        relative, _ = inputs.artifact(NATIVE, self.request["native"]["sha256"])
        (self.source / NATIVE).write_text('{"source_revision":"counterfeit"}')
        self.assertEqual(evidence.parse_json_bytes(inputs.contents[relative])["source_revision"], self.request["revision"])
        self.reject("artifact-changed-during-read", inputs.unchanged)

    def test_cli_partial_and_failed_results_have_distinct_exit_codes(self):
        request_path = self.parent / "request.json"
        for passed, code in ((True, 0), (False, 1)):
            with self.subTest(passed=passed):
                self.native["passed"] = passed
                self.save()
                write_json(request_path, self.request)
                with patch.object(evidence, "current_time", return_value=NOW), redirect_stdout(io.StringIO()):
                    self.assertEqual(evidence.main(["produce", "--request", str(request_path), "--source-root", str(self.source),
                                                   "--output", str(self.output)]), code)
                    self.assertEqual(evidence.main(["verify", "--receipt", str(self.receipt), "--source-root", str(self.source),
                        "--expected-revision", self.request["revision"], "--trusted-sha256", evidence.digest(self.receipt)]), code)


if __name__ == "__main__":
    unittest.main()
