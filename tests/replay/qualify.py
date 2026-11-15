#!/usr/bin/env python3
"""Bounded native replay controls; invoke directly, not inside a command wrapper."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import replay_build as replay


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def qualify(root, cache, output, compiler=None, *, isolation="user-network"):
    root, cache = Path(root).resolve(), Path(cache).resolve()
    output = replay.new_output(output)
    report = {
        "schema_version": 1, "artifact_kind": "bounded-replay-native-controls",
        "result": "fail", "cases": [],
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "One synthetic fixture and explicit negative controls; no release qualification",
        "source": replay.source_identity(root), "producer_sha256": replay.producer_identity(),
        "fixture_sha256": {p.relative_to(root).as_posix(): replay.digest(p)
                           for p in sorted((root / "tests/replay").iterdir()) if p.is_file()},
        "recipe_sha256": replay.digest(root / "replay/synthetic.json"),
        "isolation_backend": isolation,
    }
    replay.write_report(output, report)

    def case(name, expected, action):
        record = {"name": name, "expected": expected, "result": "fail"}
        report["cases"].append(record)
        replay.write_report(output, report)
        result = action()
        record.update({"result": "pass", "evidence": result})
        replay.write_report(output, report)
        return result

    try:
        bundle = output / "lock"
        capture = case("isolated-lock-capture", "successful native capture", lambda: replay.make_lock(
            root, "replay/synthetic.json", cache, bundle, compiler, isolation=isolation))
        lock = replay.validate_lock(json.loads((bundle / "lock.json").read_text()))
        lock_sha = replay.digest(bundle / "lock.json")
        require(capture["network_disabled_discovery"] is True, "Discovery must execute inside isolation")

        def pair():
            # Ambient values intentionally differ from the locked compiler world.
            overrides = {"TYPST_FONT_PATHS": str(root / "assets/fonts"),
                         "TYPST_PACKAGE_CACHE_PATH": str(output / "absent-ambient-cache"),
                         "SOURCE_DATE_EPOCH": "1", "TZ": "Pacific/Honolulu"}
            previous = {key: os.environ.get(key) for key in overrides}
            os.environ.update(overrides)
            try:
                result = replay.replay(bundle, lock_sha, output / "pair", compiler, isolation=isolation)
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
            builds = result["builds"]
            require(len(builds) == 2, "Exactly two independent builds are required")
            paths = [Path(item["output"]) for item in builds]
            require(paths[0].resolve() != paths[1].resolve(), "Build output roots must differ")
            require(paths[0].read_bytes() == paths[1].read_bytes(), "Actual PDF bytes differ")
            require(replay.digest(paths[0]) == lock["expected_pdf_sha256"], "PDF identity differs from capture")
            for item in builds:
                network = item["network"]
                require(network["parent_connection_succeeded"] is True, "Positive network control was not established")
                require(network["child_connection_failed"] is True, "Isolated connection unexpectedly succeeded")
                require(network["parent_namespace"] != network["child_namespace"], "No actual network namespace change")
                require(network["interfaces"] == ["lo"], "An external interface was visible")
                require(network["isolation"]["backend"] == isolation, "A different namespace backend ran")
                if isolation == "privileged-network":
                    replay.check_privilege_drop(network["isolation"], network["privilege_observation"])
                require(set(network["compiler_environment"]) == {"TZ", "LANG", "LC_ALL", "SOURCE_DATE_EPOCH"},
                        "Ambient compiler environment leaked into replay")
                require(network["compiler_environment"]["TZ"] == "UTC", "Compiler timezone changed")
                require({f["name"] for f in item["fonts"]} == {
                    "SourceSerifPro-Regular", "SourceSerifPro-Bold", "SourceSerifPro-It"},
                    "Actual PDF fonts differ from the three declared faces")
            return {"report": str(output / "pair/report.json"),
                    "report_sha256": replay.digest(output / "pair/report.json"),
                    "pdf_sha256": replay.digest(paths[0]), "pdf_bytes": paths[0].stat().st_size,
                    "ambient_override_control": overrides}

        pair_result = case("two-fresh-byte-replay", "byte-identical isolated PDFs", pair)

        def copied_bundle(name):
            target = output / (name + "-bundle")
            target.mkdir()
            shutil.copyfile(bundle / "lock.json", target / "lock.json")
            for folder in ("project", "packages", "fonts"):
                shutil.copytree(bundle / folder, target / folder)
            return target

        def reject_bundle(name, mutate, expected_code, *, alternate_compiler=None):
            target = copied_bundle(name)
            mutate(target)
            destination = output / (name + "-result")
            try:
                replay.replay(target, lock_sha, destination, alternate_compiler or compiler, isolation=isolation)
            except replay.ReplayError as exc:
                require(exc.code == expected_code, "Wrong rejection for " + name + ": " + exc.code)
            else:
                raise AssertionError("Tampered input was accepted: " + name)
            receipt = json.loads((destination / "report.json").read_text())
            require(receipt["result"] == "fail" and receipt["byte_replay_qualified"] is False,
                    "A tamper rejection reported qualification")
            require(not (destination / "first").exists(), "Tampered input reached compilation")
            return {"code": expected_code, "report": str(destination / "report.json"),
                    "report_sha256": replay.digest(destination / "report.json"),
                    "compiler_invoked": False}

        def append(target, relative):
            path = target / relative
            path.chmod(0o644)
            path.write_bytes(path.read_bytes() + b"\nREPLAY TAMPER CONTROL\n")

        package_input = next(name.partition(":")[2] for name in lock["observed_inputs"]
                             if name.startswith("package-cache:") and name.endswith(".typ"))
        controls = (
            ("source-tamper", "project/tests/replay/document.typ"),
            ("asset-tamper", "project/tests/replay/icon.svg"),
            ("package-tamper", "packages/" + package_input),
            ("font-tamper", "fonts/SourceSerifPro-Regular.otf"),
        )
        for name, path in controls:
            case(name, "rejection before compilation", lambda n=name, p=path:
                 reject_bundle(n, lambda target: append(target, p), "input-mismatch"))
        case("lock-tamper", "rejection before compilation", lambda: reject_bundle(
            "lock-tamper", lambda target: append(target, "lock.json"), "lock-mismatch"))
        wrong_compiler = output / "altered-compiler"
        wrong_compiler.write_bytes(b"Synthetic changed compiler bytes; must never execute\n")
        case("compiler-tamper", "rejection before invocation", lambda: reject_bundle(
            "compiler-tamper", lambda target: None, "tool-mismatch", alternate_compiler=wrong_compiler))
        case("missing-package", "actionable rejection before compilation", lambda: reject_bundle(
            "missing-package", lambda target: (target / "packages" / package_input).unlink(), "input-mismatch"))

        def empty_cache():
            area = output / "empty-cache"
            area.mkdir()
            replay.copy_inputs(bundle / "project", area / "project", lock["project_files"])
            replay.copy_inputs(bundle / "fonts", area / "fonts", lock["font_files"])
            (area / "packages").mkdir()
            try:
                replay.compile_isolated(area / "project", area / "packages", area / "fonts",
                                        lock["recipe"], replay.resolve_tools(compiler, lock["tools"], isolation=isolation))
            except Exception:
                pass
            else:
                raise AssertionError("Missing packages unexpectedly compiled")
            record_path = area / "project/_replay/compile-receipt.json"
            record = json.loads(record_path.read_text())
            proof = json.loads((area / "project/_replay/network.json").read_text())
            require(record["result"] == "fail" and len(record["commands"]) == 1,
                    "Expected one real failed compiler invocation")
            command = record["commands"][0]
            require(command["exit_code"] != 0 and command["timed_out"] is False,
                    "Missing packages must fail before the unchanged deadline")
            require(proof["parent_namespace"] != proof["child_namespace"]
                    and proof["parent_connection_succeeded"] is True
                    and proof["child_connection_failed"] is True and proof["interfaces"] == ["lo"],
                    "The negative package test lacks actual network isolation")
            require(proof["isolation"]["backend"] == isolation, "The empty-cache control changed backends")
            if isolation == "privileged-network":
                replay.check_privilege_drop(proof["isolation"], proof["privilege_observation"])
            require(not (area / "project/_replay/document.pdf").exists(), "A failed compile retained an output PDF")
            require(not replay.inventory(area / "packages"), "The isolated compiler populated a missing dependency")
            log = area / "project" / command["log"]
            require("failed to download package" in log.read_text(errors="replace"),
                    "The negative control failed for an unrelated reason")
            return {"report": str(record_path), "report_sha256": replay.digest(record_path),
                    "compiler_exit_code": command["exit_code"], "timed_out": command["timed_out"],
                    "network": proof}

        case("empty-cache-network-rejection", "real isolated compiler failure without downloads", empty_cache)

        def changed_pdf():
            area = output / "different-bytes"
            area.mkdir()
            first = output / "pair/first/project/_replay/document.pdf"
            changed = area / "changed.pdf"
            changed.write_bytes(first.read_bytes() + b"\n% Bounded replay byte control\n")
            runner = replay.Runner(area)
            commands = []
            tools = replay.resolve_tools(compiler, lock["tools"], isolation=isolation)
            original_text = runner.run([tools["pdftotext"], first, "-"], "original-text.log", commands)
            changed_text = runner.run([tools["pdftotext"], changed, "-"], "changed-text.log", commands)
            require(original_text == changed_text, "The byte comparison control changed extracted text")
            try:
                replay.compare_pdfs(first, changed, pair_result["pdf_sha256"])
            except replay.ReplayError as exc:
                require(exc.code == "byte-mismatch", "Wrong differing-byte rejection")
                diagnostic = exc.details
            else:
                raise AssertionError("Different PDF bytes were accepted because text matched")
            return {"commands": commands, "text_equal": True,
                    "text_sha256": hashlib.sha256(original_text.encode()).hexdigest(),
                    "diagnostic": diagnostic}

        case("equal-text-different-pdf-bytes", "rejection despite equal actual PDF text", changed_pdf)
        report.update({"result": "pass", "case_count": len(report["cases"]),
                       "native_compiler_attempts": 4, "successful_native_pdfs": 3,
                       "expected_native_compiler_failures": 1, "lock_sha256": lock_sha,
                       "pdf_sha256": pair_result["pdf_sha256"],
                       "release_bundle_qualified": False, "complete_environment_image_locked": False,
                       "cross_environment_semantic_repeatability_qualified": False})
        return report
    except Exception as exc:
        report.update({"error": str(exc), "code": getattr(exc, "code", type(exc).__name__)})
        if report["code"] == "network-isolation-unavailable":
            report["result"] = "unsupported"
        raise
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        replay.write_report(output, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--package-cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--isolation", choices=replay.ISOLATION_BACKENDS, default="user-network")
    args = parser.parse_args(argv)
    try:
        result = qualify(args.root, args.package_cache, args.output, args.compiler, isolation=args.isolation)
        print(json.dumps({key: result[key] for key in ("result", "case_count", "lock_sha256", "pdf_sha256")}))
        return 0
    except Exception as exc:
        unsupported = getattr(exc, "code", None) == "network-isolation-unavailable"
        print(json.dumps({"result": "unsupported" if unsupported else "fail", "error": str(exc)}), file=sys.stderr)
        return 2 if unsupported else 1


if __name__ == "__main__":
    raise SystemExit(main())
