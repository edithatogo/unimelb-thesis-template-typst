#!/usr/bin/env python3
"""Validate a solo-maintainer ruleset; optionally compare a full GitHub snapshot.

No network calls or settings mutations are performed. Desired-only success is
not evidence that GitHub protection is active. Observations must contain full
ruleset objects, including bypass actors, rather than the summary list endpoint.
"""

import argparse
import json
from pathlib import Path
import sys


ACTIONS_APP_ID = 15368
OWNER_ID = 15080672
REQUIRED_RULES = {"deletion", "non_fast_forward", "required_status_checks"}
PR_FLAGS = {
    "dismiss_stale_reviews_on_push", "require_code_owner_review",
    "require_last_push_approval", "required_review_thread_resolution",
    "require_extra_approval_for_unattributed_changes",
}
OBSERVATION_FIELDS = {
    "name", "target", "enforcement", "conditions", "bypass_actors", "rules",
}


class ObservationUnavailable(ValueError):
    """The supplied snapshot cannot establish the effective settings."""


def validate_ruleset(data):
    """Return policy violations without interpreting unavailable data as valid."""
    errors = []
    if not isinstance(data, dict):
        return ["ruleset must be a JSON object"]
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        errors.append("name must be nonempty")
    if data.get("target") != "branch" or data.get("enforcement") != "active":
        errors.append("target must be branch and enforcement must be active")
    conditions = data.get("conditions")
    if not isinstance(conditions, dict) or set(conditions) != {"ref_name"}:
        errors.append("conditions must contain only ref_name")
    else:
        refs = conditions["ref_name"]
        if (not isinstance(refs, dict) or set(refs) != {"include", "exclude"}
                or refs.get("include") not in (["~DEFAULT_BRANCH"], ["refs/heads/main"])
                or refs.get("exclude") != []):
            errors.append("target only the default branch, without exclusions")
    bypass = data.get("bypass_actors")
    if not isinstance(bypass, list) or len(bypass) != 1:
        errors.append("exactly one owner recovery bypass is required")
    else:
        actor = bypass[0]
        if (not isinstance(actor, dict)
                or set(actor) != {"actor_id", "actor_type", "bypass_mode"}
                or type(actor.get("actor_id")) is not int
                or not isinstance(actor.get("actor_type"), str)
                or (actor.get("actor_type"), actor.get("actor_id")) not in {
                    ("RepositoryRole", 5), ("User", OWNER_ID)}
                or actor.get("bypass_mode") != "always"):
            errors.append("bypass must be owner/admin recovery only, in always mode")
    rules = data.get("rules")
    if not isinstance(rules, list):
        return errors + ["rules must be an array"]
    seen = set()
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("type"), str):
            errors.append("each rule must have a string type")
            continue
        kind = rule["type"]
        if kind in seen:
            errors.append(f"duplicate rule: {kind}")
        seen.add(kind)
        if set(rule) - {"type", "parameters"}:
            errors.append(f"unsupported rule fields: {kind}")
        params = rule.get("parameters", {})
        if not isinstance(params, dict):
            errors.append(f"parameters must be an object: {kind}")
            continue
        if kind in {"deletion", "non_fast_forward"}:
            if params:
                errors.append(f"unexpected parameters: {kind}")
        elif kind == "required_status_checks":
            allowed = {"required_status_checks", "strict_required_status_checks_policy",
                       "do_not_enforce_on_create"}
            if set(params) - allowed:
                errors.append("unsupported required-status-check parameters")
            if params.get("strict_required_status_checks_policy") is not True:
                errors.append("required status checks must be strict")
            if params.get("do_not_enforce_on_create", False) is not False:
                errors.append("required status checks must apply on creation")
            checks = params.get("required_status_checks")
            if not isinstance(checks, list) or not checks:
                errors.append("required status checks must be a nonempty array")
                continue
            contexts = set()
            for check in checks:
                if not isinstance(check, dict):
                    errors.append("required check must be an object")
                    continue
                context = check.get("context")
                if (not isinstance(context, str) or not context.strip()
                        or context != context.strip()):
                    errors.append("required check context must be nonempty and trimmed")
                elif context in contexts:
                    errors.append(f"duplicate required check: {context}")
                else:
                    contexts.add(context)
                if (set(check) != {"context", "integration_id"}
                        or type(check.get("integration_id")) is not int
                        or check.get("integration_id") != ACTIONS_APP_ID):
                    errors.append("every required check must bind GitHub Actions 15368")
        elif kind == "pull_request":
            allowed = PR_FLAGS | {"required_approving_review_count",
                                  "required_reviewers", "allowed_merge_methods"}
            if set(params) - allowed:
                errors.append("unsupported pull-request parameters")
            if (type(params.get("required_approving_review_count")) is not int
                    or params.get("required_approving_review_count") != 0):
                errors.append("mandatory approval count must be zero")
            for flag in sorted(PR_FLAGS):
                value = params.get(flag, False)
                if type(value) is not bool:
                    errors.append(f"{flag} must be boolean")
                elif flag in {"require_code_owner_review", "require_last_push_approval",
                              "require_extra_approval_for_unattributed_changes"} and value:
                    errors.append(f"human approval gate is forbidden: {flag}")
            if params.get("required_reviewers", []) != []:
                errors.append("required user/team reviewers are forbidden")
            methods = params.get("allowed_merge_methods", ["merge", "squash", "rebase"])
            if (not isinstance(methods, list) or not methods
                    or any(m not in ("merge", "squash", "rebase") for m in methods)
                    or len(set(methods)) != len(methods)):
                errors.append("allowed_merge_methods must contain unique known methods")
        else:
            errors.append(f"unsupported additional rule: {kind}")
    for missing in sorted(REQUIRED_RULES - seen):
        errors.append(f"missing required rule: {missing}")
    return errors


def normalized(data):
    """Ignore server metadata and order; retain all policy-relevant settings."""
    result = {key: data[key] for key in OBSERVATION_FIELDS}
    rules = []
    for rule in data["rules"]:
        kind = rule["type"]
        params = dict(rule.get("parameters", {}))
        if kind == "required_status_checks":
            params.setdefault("do_not_enforce_on_create", False)
            params["required_status_checks"] = sorted(
                params["required_status_checks"], key=lambda check: check["context"])
        elif kind == "pull_request":
            for flag in sorted(PR_FLAGS):
                params.setdefault(flag, False)
            params.setdefault("required_reviewers", [])
            params["allowed_merge_methods"] = sorted(
                params.get("allowed_merge_methods", ["merge", "squash", "rebase"]))
        rules.append({"type": kind, "parameters": params})
    result["rules"] = sorted(rules, key=lambda rule: rule["type"])
    return result


def require_observation_shape(item):
    """Validate enough response structure to classify every ruleset safely."""
    if not isinstance(item, dict) or not OBSERVATION_FIELDS <= item.keys():
        raise ObservationUnavailable("observed ruleset lacks full settings or bypass actors")
    if not isinstance(item["name"], str) or not item["name"].strip():
        raise ObservationUnavailable("observed ruleset name must be nonempty")
    for field, values in (("target", {"branch", "tag", "push"}),
                          ("enforcement", {"active", "disabled", "evaluate"})):
        if not isinstance(item[field], str) or item[field] not in values:
            raise ObservationUnavailable(f"observed ruleset has unknown {field}")
    # Push rulesets can have no ref conditions; branch/tag rulesets need an object.
    if not isinstance(item["conditions"], dict) and not (
        item["target"] == "push" and item["conditions"] is None
    ):
        raise ObservationUnavailable("observed ruleset conditions have an invalid type")
    for field in ("bypass_actors", "rules"):
        if not isinstance(item[field], list) or any(
            not isinstance(entry, dict) for entry in item[field]
        ):
            raise ObservationUnavailable(f"observed ruleset {field} must be an array of objects")
    for rule in item["rules"]:
        if (not isinstance(rule.get("type"), str) or not rule["type"].strip()
                or not isinstance(rule.get("parameters", {}), dict)):
            raise ObservationUnavailable("observed ruleset contains a malformed rule")


def compare_rulesets(desired, observed):
    """Return drift; raise when a complete observation is unavailable."""
    if not isinstance(observed, list):
        raise ObservationUnavailable("observed data must be a list of full rulesets")
    for item in observed:
        require_observation_shape(item)
    matches = [item for item in observed if item["name"] == desired["name"]]
    if len(matches) != 1:
        return [f"expected one observed ruleset named {desired['name']!r}; found {len(matches)}"]
    actual = matches[0]
    errors = [f"observed: {error}" for error in validate_ruleset(actual)]
    extras = [item["name"] for item in observed if item is not actual
              and item["target"] in {"branch", "push"} and item["enforcement"] == "active"]
    if extras:
        errors.append(f"additional active branch/push rulesets require review: {extras!r}")
    if errors:
        return errors
    expected = normalized(desired)
    current = normalized(actual)
    for field in sorted(OBSERVATION_FIELDS):
        if expected[field] != current[field]:
            errors.append(f"drift in {field}: expected {json.dumps(expected[field], sort_keys=True)}"
                          f"; observed {json.dumps(current[field], sort_keys=True)}")
    return errors


def read_json(path):
    return Path(path).read_text(encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desired", required=True, help="desired ruleset JSON file")
    parser.add_argument("--observed", help="JSON list of full observed GitHub rulesets")
    args = parser.parse_args(argv)
    try:
        desired = json.loads(read_json(args.desired))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"UNKNOWN: cannot read desired policy: {exc}", file=sys.stderr)
        return 2
    violations = validate_ruleset(desired)
    if violations:
        print("INVALID desired policy:\n- " + "\n- ".join(violations), file=sys.stderr)
        return 1
    if args.observed is None:
        print("VALID desired-only policy; active GitHub settings were not observed.")
        return 0
    try:
        observed = json.loads(read_json(args.observed))
        drift = compare_rulesets(desired, observed)
    except (OSError, UnicodeError, json.JSONDecodeError, ObservationUnavailable) as exc:
        print(f"UNKNOWN: cannot verify active settings: {exc}", file=sys.stderr)
        return 2
    if drift:
        print("DRIFT in observed settings:\n- " + "\n- ".join(drift), file=sys.stderr)
        return 1
    print("MATCH: supplied branch policy and active branch/push inventory match; "
          "snapshot freshness and provenance must be verified separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
