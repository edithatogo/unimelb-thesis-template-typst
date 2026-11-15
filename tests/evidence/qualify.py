#!/usr/bin/env python3
"""Post-build producer/consumer controls; preserve the completed native report."""
from __future__ import annotations

import argparse
from datetime import timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import requirement_evidence as api

ROOT = api.ROOT
NATIVE = "build/verification/report.json"
PROPERTIES = "build/property-tests.json"


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False).encode() + b"\n"


def native_input(source_root):
    path = api.confined_file(source_root, NATIVE)
    data = path.read_bytes()
    return api.parse_json_bytes(data), hashlib.sha256(data).hexdigest()


def optional_sidecars(native, source_root):
    """Attach declared policy/replay files without claiming semantic support."""
    result = []
    source_root = Path(source_root).resolve()
    for key, role, path_key, digest_key in (
        ("submission_policy_corpus", "policy", "report", "report_sha256"),
        ("replay_corpus", "reproducibility", "sidecar", "sidecar_sha256"),
    ):
        if key not in native:
            continue
        corpus = native[key]
        if (isinstance(corpus, dict) and corpus.get("result") == "unexecuted"
                and path_key not in corpus and digest_key not in corpus):
            # The copied native report retains this explicit unexecuted result.
            # No artifact has been declared, so there are no bytes to attach.
            continue
        api.require(isinstance(corpus, dict) and isinstance(corpus.get(path_key), str)
                    and isinstance(corpus.get(digest_key), str) and api.SHA.fullmatch(corpus[digest_key]),
                    "sidecar-declaration", "A declared optional corpus must identify its report and digest.")
        path = Path(corpus[path_key])
        if path.is_absolute():
            # Relative lexical conversion keeps symlink components visible to
            # confined_file; resolving first would hide an internal symlink.
            api.require(path.is_relative_to(source_root), "unsafe-path", "A sidecar lies outside the source root.")
            relative = path.relative_to(source_root).as_posix()
        else:
            relative = corpus[path_key]
        path = api.confined_file(source_root, relative)
        data = path.read_bytes()
        api.require(hashlib.sha256(data).hexdigest() == corpus[digest_key], "artifact-tampered", "An optional sidecar changed.")
        value = api.parse_json_bytes(data)
        api.require(isinstance(value, dict) and type(value.get("schema_version")) is int
                    and value["schema_version"] == 1, "sidecar-version", "This attachment profile expects a version1 report.")
        if role == "reproducibility":
            api.require(value.get("artifact_kind") == "bounded-replay-native-controls", "sidecar-kind", "The replay control sidecar kind is unsupported.")
        result.append({"id": "policy" if role == "policy" else "replay", "role": role, "path": relative,
                       "sha256": corpus[digest_key], "schema_version": "1", "required": False})
    return result


def declared_inputs(native, source_root):
    """Protect declared paths from the same native buffer that we will bind."""
    result = [source_root / NATIVE, source_root / PROPERTIES]
    result.extend(api.native_input_paths(native, source_root))
    return result


def qualify(source_root, output, not_before, review_by):
    source_root = Path(source_root).resolve()
    now = api.current_time()
    input_error, native, native_hash = None, None, None
    try:
        native, native_hash = native_input(source_root)
    except (api.ReceiptError, OSError, ValueError) as error:
        input_error = error
    protected = declared_inputs(native, source_root)
    output = api.output_directory(output, protected)
    report_path = output / "qualification.json"
    report = {"schema_version": 1, "artifact_kind": "requirement-evidence-consumer-qualification",
              "started_at": now.isoformat(), "passed": False, "cases": [],
              "driver_sha256": api.digest(Path(__file__)), "helper_sha256": api.digest(Path(api.__file__)),
              "renderer_reexecuted": False, "full_issue_qualified": False,
              "institutional_approval": False, "blind_safe": False,
              "review_window_kind": "automation-freshness-window-not-human-approval"}
    api.atomic_bytes(report_path, encoded(report))
    try:
        if input_error is not None:
            raise input_error
        negative = api.output_directory(output / "negative", protected)
        api.require(not negative.exists(), "unsafe-output", "Choose a new qualification directory; existing negative evidence is preserved.")
        api.require(isinstance(native, dict), "native-interface", "A completed native report is required.")
        extras = optional_sidecars(native, source_root)
        api.require(api.datetime_value(not_before) <= now <= api.datetime_value(review_by),
                    "invalid-time-window", "The explicit automated observation window is invalid or expired.")
        properties = api.confined_file(source_root, PROPERTIES)
        property_hash = api.digest(properties)
        probes = []
        with api.command_logs(output / "identity-probes"):
            revision = api.runner.run(["git", "--no-optional-locks", "-C", str(source_root), "rev-parse", "HEAD"], "revision.log", probes).strip()
            tree = api.runner.run(["git", "--no-optional-locks", "-C", str(source_root), "rev-parse", "HEAD^{tree}"], "tree.log", probes).strip()
        api.require(api.GIT.fullmatch(revision) and api.GIT.fullmatch(tree), "source-identity", "Actual immutable Git identities are required.")
        request = {"schema_version": 1, "repository": api.REPOSITORY, "revision": revision, "tree": tree,
                   "run": {"not_before": not_before, "review_by": review_by},
                   "native": {"path": NATIVE, "sha256": native_hash, "schema_version": 1},
                   "properties": {"path": PROPERTIES, "sha256": property_hash, "schema_version": 1}, "sidecars": extras}
        api.atomic_bytes(output / "request.json", encoded(request))
        positive = api.output_directory(output / "positive", protected)
        wrapper, sidecar = api.produce(request, source_root=source_root, output=positive, now=now)
        receipt = positive / "verification-receipt.json"
        trusted = api.digest(receipt)
        report.update(source_revision=revision, source_tree=tree, request=request,
                      native_report_sha256=native_hash, property_report_sha256=property_hash,
                      wrapper_sha256=trusted, sidecar_sha256=api.digest(positive / "requirement-status.json"),
                      readable_sha256=api.digest(positive / "requirements.md"), identity_probes=probes,
                      source_inventory_sha256=sidecar["source"]["inventory_sha256"],
                      requirements=len(sidecar["requirements"]), artifacts=len(sidecar["artifacts"]),
                      optional_sidecars=sidecar["sidecars"], result=wrapper["result"],
                      whole_requirement_results={value: sum(row["result"] == value for row in sidecar["requirements"])
                                                 for value in ("blocked", "unexecuted", "executed-fail")},
                      applicability={value: sum(row["applicability"] == value for row in sidecar["requirements"])
                                     for value in ("applicable", "unassessed")})

        def consume(path=receipt, expected=revision, digest=trusted, when=now):
            return api.verify_receipt(path, source_root=source_root, expected_revision=expected,
                                      trusted_sha256=digest, now=when, logs=output / "consumer-probes")

        def record(name, function, expected=None):
            try:
                result = function()
                valid = expected is None and result.get("integrity_verified") is True and result["result"] == "partial"
                observed = "consistent-partial" if valid else "unexpected-acceptance-or-failure"
            except api.ReceiptError as error:
                observed, valid = error.code, error.code == expected
            report["cases"].append({"id": name, "expected": expected or "consistent-partial", "observed": observed, "passed": valid})

        record("actual-clean-native-and-property-files", consume)
        record("unrelated-commit-is-not-this-execution", lambda: consume(expected="0" * 40), "wrong-revision")
        record("expired-review-window", lambda: consume(when=api.datetime_value(review_by) + timedelta(seconds=1)), "review-expired")
        record("untrusted-wrapper-digest", lambda: consume(digest="0" * 64), "wrapper-tampered")
        shutil.copytree(positive, negative)
        copied_receipt = negative / "verification-receipt.json"
        pdf_name = next(item["pdf"] for item in native["documents"] if item["source"] == "thesis.typ")
        pdf = api.confined_file(negative, "artifacts/" + api.safe_relative(pdf_name))
        original = pdf.read_bytes()
        api.atomic_bytes(pdf, original + b"\nIntentional receipt tamper control\n")
        record("changed-actual-pdf-bytes", lambda: consume(path=copied_receipt), "artifact-tampered")
        pdf.unlink()
        record("missing-actual-pdf", lambda: consume(path=copied_receipt), "missing-artifact")
        api.atomic_bytes(pdf, original)
        descriptor = native["native_evidence_corpus"]["supplement"]
        supplement = api.confined_file(negative, "artifacts/" + api.safe_relative(descriptor["path"]))
        original_supplement = supplement.read_bytes()
        api.atomic_bytes(supplement, original_supplement + b"\nIntentional descriptor tamper control\n")
        record("changed-path-descriptor-artifact", lambda: consume(path=copied_receipt), "artifact-tampered")
        supplement.unlink()
        record("missing-path-descriptor-artifact", lambda: consume(path=copied_receipt), "missing-artifact")
        api.atomic_bytes(supplement, original_supplement)
        status = negative / "requirement-status.json"
        forged = api.read_json(status)
        forged["requirements"][0]["result"] = "executed-pass"
        api.atomic_bytes(status, encoded(forged))
        forged_wrapper = api.read_json(copied_receipt)
        next(item for item in forged_wrapper["artifacts"] if item["path"] == "requirement-status.json")["sha256"] = api.digest(status)
        api.atomic_bytes(copied_receipt, encoded(forged_wrapper))
        record("rehashed-whole-requirement-pass-forgery",
               lambda: consume(path=copied_receipt, digest=api.digest(copied_receipt)), "sidecar-semantic-drift")
        status.unlink()
        record("missing-required-versioned-sidecar",
               lambda: consume(path=copied_receipt, digest=api.digest(copied_receipt)), "missing-artifact")
        # Keep the original positive bundle independently valid after all
        # mutations, and keep intentional negative evidence clearly separate.
        final = consume()
        report["positive_bundle_still_valid"] = final["integrity_verified"] and final["result"] == "partial"
        report["native_bytes_unchanged"] = api.digest(source_root / NATIVE) == native_hash
        report["property_bytes_unchanged"] = api.digest(properties) == property_hash
        report["passed"] = len(report["cases"]) == 10 and all(case["passed"] for case in report["cases"]) \
            and report["positive_bundle_still_valid"] and report["native_bytes_unchanged"] and report["property_bytes_unchanged"]
    except (api.ReceiptError, api.runner.VerificationError, OSError, KeyError, StopIteration, ValueError) as error:
        report["error_code"] = getattr(error, "code", "orchestration-failed")
        report["passed"] = False
    finally:
        report["finished_at"] = api.current_time().isoformat()
        api.atomic_bytes(report_path, encoded(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=api.OUTPUT_ROOT / "qualification")
    parser.add_argument("--not-before", required=True)
    parser.add_argument("--review-by", required=True)
    args = parser.parse_args(argv)
    try:
        result = qualify(args.source_root, args.output, args.not_before, args.review_by)
    except (api.ReceiptError, OSError, ValueError) as error:
        print("Post-build evidence controls rejected: " + getattr(error, "code", "io-or-value-error"), file=sys.stderr)
        return 1
    print("Post-build evidence controls: " + ("passed" if result["passed"] else "failed")
          + "; ten consumer cases; whole-programme result remains partial or fail.")
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
