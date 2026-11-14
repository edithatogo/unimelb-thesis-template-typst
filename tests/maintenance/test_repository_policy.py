"""Behavioral tests for intended and observed solo-maintainer protection."""

import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest


from scripts import check_repository_policy as policy


def valid_policy():
    # Synthetic policy: contexts are examples, not evidence of hosted execution.
    return {
        "name": "solo-maintainer",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []}},
        "bypass_actors": [
            {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}
        ],
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [
                    {"context": "compile (default) / build", "integration_id": 15368},
                    {"context": "privacy-and-secrets", "integration_id": 15368},
                ],
            }},
            {"type": "pull_request", "parameters": {
                "required_approving_review_count": 0,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
            }},
        ],
    }


def rule(data, kind):
    return next(item for item in data["rules"] if item["type"] == kind)


class PolicyValidationTests(unittest.TestCase):
    def assert_invalid(self, value, fragment):
        errors = policy.validate_ruleset(value)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_minimal_valid_policy_and_owner_recovery(self):
        data = valid_policy()
        self.assertEqual(policy.validate_ruleset(data), [])
        data["rules"] = data["rules"][:3]
        data["conditions"]["ref_name"]["include"] = ["refs/heads/main"]
        data["bypass_actors"] = [
            {"actor_id": 15080672, "actor_type": "User", "bypass_mode": "always"}
        ]
        self.assertEqual(policy.validate_ruleset(data), [])

    def test_protection_cannot_be_disabled_or_retargeted(self):
        for key, value in [("enforcement", "disabled"), ("enforcement", "evaluate"),
                           ("target", "tag")]:
            with self.subTest(key=key, value=value):
                data = valid_policy()
                data[key] = value
                self.assert_invalid(data, "enforcement must be active")
        for refs in [
            {"include": ["refs/heads/dev"], "exclude": []},
            {"include": ["~ALL"], "exclude": []},
            {"include": ["refs/heads/main", "refs/heads/dev"], "exclude": []},
            {"include": ["~DEFAULT_BRANCH"], "exclude": ["refs/heads/main"]},
            {"include": ["~DEFAULT_BRANCH"]},
            None,
        ]:
            with self.subTest(refs=refs):
                data = valid_policy()
                data["conditions"]["ref_name"] = refs
                self.assert_invalid(data, "target only the default branch")
        data["conditions"] = {"ref_name": {}, "repository_name": {}}
        self.assert_invalid(data, "conditions must contain only")

    def test_deletion_and_force_push_protection_are_mandatory(self):
        for kind in ("deletion", "non_fast_forward", "required_status_checks"):
            with self.subTest(kind=kind):
                data = valid_policy()
                data["rules"] = [item for item in data["rules"] if item["type"] != kind]
                self.assert_invalid(data, f"missing required rule: {kind}")

    def test_approval_and_team_gates_are_rejected(self):
        mutations = [
            ("required_approving_review_count", 1, "approval count"),
            ("required_approving_review_count", False, "approval count"),
            ("require_code_owner_review", True, "human approval gate"),
            ("require_last_push_approval", True, "human approval gate"),
            ("require_extra_approval_for_unattributed_changes", True, "human approval gate"),
            ("required_reviewers", [{"type": "Team", "id": 42}], "user/team reviewers"),
            ("require_last_push_approval", "false", "must be boolean"),
            ("new_review_gate", True, "unsupported pull-request"),
            ("allowed_merge_methods", ["squash", "squash"], "unique known methods"),
            ("allowed_merge_methods", [[]], "unique known methods"),
        ]
        for key, value, message in mutations:
            with self.subTest(key=key, value=value):
                data = valid_policy()
                rule(data, "pull_request")["parameters"][key] = value
                self.assert_invalid(data, message)

    def test_required_checks_must_be_explicit_unique_and_bound(self):
        invalid_checks = [
            ([], "nonempty array"),
            (None, "nonempty array"),
            ([None], "check must be an object"),
            ([{"context": "", "integration_id": 15368}], "context must be nonempty"),
            ([{"context": " build", "integration_id": 15368}], "context must be nonempty"),
            ([{"context": "build"}], "bind GitHub Actions"),
            ([{"context": "build", "integration_id": 1}], "bind GitHub Actions"),
            ([{"context": "build", "integration_id": True}], "bind GitHub Actions"),
            ([{"context": "build", "integration_id": 15368}] * 2, "duplicate required check"),
        ]
        for checks, message in invalid_checks:
            with self.subTest(checks=checks):
                data = valid_policy()
                rule(data, "required_status_checks")["parameters"]["required_status_checks"] = checks
                self.assert_invalid(data, message)
        for key, value, message in [
            ("strict_required_status_checks_policy", False, "must be strict"),
            ("strict_required_status_checks_policy", 1, "must be strict"),
            ("do_not_enforce_on_create", True, "apply on creation"),
            ("unrecognized_option", True, "unsupported required-status"),
        ]:
            data = valid_policy()
            rule(data, "required_status_checks")["parameters"][key] = value
            self.assert_invalid(data, message)

    def test_bypass_is_owner_recovery_only(self):
        for actors in [
            [],
            valid_policy()["bypass_actors"] * 2,
            [{"actor_id": 2740, "actor_type": "Integration", "bypass_mode": "always"}],
            [{"actor_id": 15080672, "actor_type": "User", "bypass_mode": "pull_request"}],
            [{"actor_id": 4, "actor_type": "RepositoryRole", "bypass_mode": "always"}],
            [{"actor_id": 5, "actor_type": [], "bypass_mode": "always"}],
            [{"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always",
              "extra": True}],
            [None],
            None,
        ]:
            with self.subTest(actors=actors):
                data = valid_policy()
                data["bypass_actors"] = actors
                self.assertTrue(policy.validate_ruleset(data))

    def test_malformed_and_unsupported_rules_fail_closed(self):
        for data in [None, [], "active", {}, {"rules": None}]:
            self.assertTrue(policy.validate_ruleset(data))
        for value, message in [
            (None, "string type"),
            ({"type": 1}, "string type"),
            ({"type": "deletion"}, "duplicate rule"),
            ({"type": "required_deployments"}, "unsupported additional rule"),
            ({"type": "deletion", "parameters": []}, "parameters must be an object"),
            ({"type": "non_fast_forward", "parameters": {"allow": True}}, "unexpected parameters"),
            ({"type": "deletion", "extra": True}, "unsupported rule fields"),
        ]:
            data = valid_policy()
            data["rules"].append(value)
            self.assert_invalid(data, message)


class ObservedSettingsTests(unittest.TestCase):
    def test_server_metadata_order_and_default_values_do_not_cause_drift(self):
        desired = valid_policy()
        actual = copy.deepcopy(desired)
        actual.update({"id": 42, "source_type": "Repository", "node_id": "synthetic"})
        actual["rules"].reverse()
        params = rule(actual, "required_status_checks")["parameters"]
        params["required_status_checks"].reverse()
        params["do_not_enforce_on_create"] = False
        rule(actual, "deletion")["parameters"] = {}
        self.assertEqual(policy.compare_rulesets(desired, [actual]), [])

    def test_missing_and_duplicate_observed_policy_are_drift(self):
        desired = valid_policy()
        self.assertTrue(policy.compare_rulesets(desired, []))
        self.assertTrue(policy.compare_rulesets(desired, [desired, copy.deepcopy(desired)]))
        other = copy.deepcopy(desired)
        other["name"] = "different"
        self.assertTrue(policy.compare_rulesets(desired, [other]))

    def test_summary_error_and_missing_bypass_are_unknown(self):
        for observed in [None, {}, {"error": "HTTP 403"}, ["unavailable"],
                         [{"id": 42, "name": "solo-maintainer"}]]:
            with self.subTest(observed=observed):
                with self.assertRaises(policy.ObservationUnavailable):
                    policy.compare_rulesets(valid_policy(), observed)
        actual = valid_policy()
        del actual["bypass_actors"]
        with self.assertRaises(policy.ObservationUnavailable):
            policy.compare_rulesets(valid_policy(), [actual])

    def test_extra_and_missing_checks_and_changed_config_are_drift(self):
        for change in ("extra", "missing", "strict", "bypass", "approval"):
            with self.subTest(change=change):
                actual = valid_policy()
                params = rule(actual, "required_status_checks")["parameters"]
                if change == "extra":
                    params["required_status_checks"].append(
                        {"context": "unqualified-service", "integration_id": 15368})
                elif change == "missing":
                    params["required_status_checks"].pop()
                elif change == "strict":
                    params["strict_required_status_checks_policy"] = False
                elif change == "bypass":
                    actual["bypass_actors"][0]["actor_type"] = "Integration"
                else:
                    rule(actual, "pull_request")["parameters"]["required_approving_review_count"] = 1
                self.assertTrue(policy.compare_rulesets(valid_policy(), [actual]))

    def test_additional_active_branch_ruleset_requires_review(self):
        desired = valid_policy()
        extra = copy.deepcopy(desired)
        extra["name"] = "unexpected human gate"
        self.assertTrue(policy.compare_rulesets(desired, [desired, extra]))
        extra["enforcement"] = "disabled"
        self.assertEqual(policy.compare_rulesets(desired, [desired, extra]), [])

    def test_malformed_extra_observations_are_unknown(self):
        # A matching primary policy must not hide an incomplete secondary one.
        mutations = [
            ("name", None), ("name", ""),
            ("target", None), ("target", []), ("target", "unknown"),
            ("enforcement", None), ("enforcement", []), ("enforcement", "unknown"),
            ("conditions", []), ("conditions", None),
            ("bypass_actors", {}), ("bypass_actors", [None]),
            ("rules", {}), ("rules", [None]),
            ("rules", [{"type": None}]),
            ("rules", [{"type": "deletion", "parameters": []}]),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                desired = valid_policy()
                extra = copy.deepcopy(desired)
                extra.update(name="secondary", target="tag")
                extra[field] = value
                with self.assertRaises(policy.ObservationUnavailable):
                    policy.compare_rulesets(desired, [desired, extra])

    def test_additional_active_push_ruleset_requires_review(self):
        desired = valid_policy()
        extra = {
            "name": "restrict template pushes",
            "target": "push",
            "enforcement": "active",
            "conditions": None,
            "bypass_actors": [],
            "rules": [{"type": "file_extension_restriction", "parameters": {
                "restricted_file_extensions": [".typ"],
            }}],
        }
        errors = policy.compare_rulesets(desired, [desired, extra])
        self.assertTrue(any("branch/push rulesets require review" in error for error in errors))

    def test_valid_non_enforcing_and_tag_rulesets_are_outside_branch_inventory(self):
        desired = valid_policy()
        for target, enforcement in (("push", "disabled"), ("push", "evaluate"),
                                    ("tag", "active")):
            with self.subTest(target=target, enforcement=enforcement):
                extra = copy.deepcopy(desired)
                extra.update(name="secondary", target=target, enforcement=enforcement)
                self.assertEqual(policy.compare_rulesets(desired, [desired, extra]), [])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, desired, observed=...):
        with tempfile.TemporaryDirectory() as folder:
            expected = Path(folder) / "desired.json"
            expected.write_text(desired, encoding="utf-8")
            args = ["--desired", str(expected)]
            if observed is not ...:
                actual = Path(folder) / "observed.json"
                actual.write_text(observed, encoding="utf-8")
                args += ["--observed", str(actual)]
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                status = policy.main(args)
            return status, output.getvalue()

    def test_desired_only_does_not_claim_active_protection(self):
        status, output = self.run_cli(json.dumps(valid_policy()))
        self.assertEqual(status, 0)
        self.assertIn("desired-only", output)
        self.assertIn("were not observed", output)

    def test_matching_snapshot_is_qualified_by_provenance(self):
        data = valid_policy()
        status, output = self.run_cli(json.dumps(data), json.dumps([data]))
        self.assertEqual(status, 0)
        self.assertIn("MATCH:", output)
        self.assertIn("freshness and provenance", output)

    def test_empty_observation_is_drift_and_null_is_unknown(self):
        status, output = self.run_cli(json.dumps(valid_policy()), "[]")
        self.assertEqual(status, 1)
        self.assertIn("DRIFT", output)
        status, output = self.run_cli(json.dumps(valid_policy()), "null")
        self.assertEqual(status, 2)
        self.assertIn("UNKNOWN", output)

    def test_malformed_json_is_unknown_not_pass(self):
        for desired, observed in [("{broken", ...), (json.dumps(valid_policy()), "{broken")]:
            status, output = self.run_cli(desired, observed)
            self.assertEqual(status, 2)
            self.assertIn("UNKNOWN", output)

    def test_invalid_desired_is_nonzero(self):
        status, output = self.run_cli("{}")
        self.assertEqual(status, 1)
        self.assertIn("INVALID desired policy", output)

    def test_missing_file_is_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "missing.json"
            output = io.StringIO()
            with contextlib.redirect_stderr(output):
                status = policy.main(["--desired", str(missing)])
            self.assertEqual(status, 2)
            self.assertIn("UNKNOWN", output.getvalue())

    def test_unknown_extra_observation_cannot_produce_match(self):
        desired = valid_policy()
        extra = copy.deepcopy(desired)
        extra.update(name="unknown", target=None, enforcement=None)
        status, output = self.run_cli(json.dumps(desired), json.dumps([desired, extra]))
        self.assertEqual(status, 2)
        self.assertIn("UNKNOWN", output)
        self.assertNotIn("MATCH", output)

    def test_active_push_ruleset_produces_drift(self):
        desired = valid_policy()
        extra = copy.deepcopy(desired)
        extra.update(name="push restrictions", target="push")
        status, output = self.run_cli(json.dumps(desired), json.dumps([desired, extra]))
        self.assertEqual(status, 1)
        self.assertIn("DRIFT", output)
        self.assertNotIn("MATCH", output)


if __name__ == "__main__":
    unittest.main()
