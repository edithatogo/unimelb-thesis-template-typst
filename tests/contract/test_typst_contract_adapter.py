"""Failure-boundary tests for the native adapter; mocked tools are not PDF evidence."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import copy, deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import typst_contract_adapter as adapter
from scripts import verify_typst_contract_adapter as corpus
from scripts.thesis_contract import ContractError, load_bundle

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts/thesis/v1"
CONTRACT_PIN = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
FIXTURES_PIN = "af82359a786b2be565e49de594e32a5d2edb3354221dfd5371d5d954b33c5757"


class AdapterBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load_bundle(CONTRACT, CONTRACT_PIN)

    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(prefix="adapter-unit-", dir=ROOT / "build")
        self.root = Path(self.directory.name)
        self.output = self.root / "output"
        self.old_verify = (adapter.verify.ROOT, adapter.verify.OUTPUT)

    def tearDown(self):
        adapter.verify.ROOT, adapter.verify.OUTPUT = self.old_verify
        self.directory.cleanup()

    def args(self, identifier="draft-minimal", **pins):
        return ["--contract", str(CONTRACT), "--contract-sha256", pins.get("contract", CONTRACT_PIN),
                "--fixture-manifest-sha256", pins.get("manifest", FIXTURES_PIN),
                "--output", str(self.output), "fixture", identifier,
                "--fixture-sha256", pins.get("fixture", self.bundle.fixtures.get(identifier, {}).get("sha256", "0" * 64))]

    def invoke(self, args):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            status = adapter.main(args)
        return status, json.loads((self.output / "native-report.json").read_text())

    def render_args(self, metadata=None, explicit=None, cli=()):
        args = self.args()
        args = args[:args.index("fixture")] + ["render"]
        for name, value in (("metadata", metadata), ("explicit", explicit)):
            if value is not None:
                path = self.root / (name + ".json")
                path.write_text(json.dumps(value))
                args.extend(["--" + name, str(path)])
        for value in cli:
            args.extend(["--set", value])
        return args

    def fake_tools(self, mode="ok"):
        def response(command):
            name = Path(command[0]).name
            if command[-1] in ("--version", "-v"):
                if mode == "missing-tool":
                    raise FileNotFoundError("synthetic tool missing")
                version = ("typst 0.14.0 unit-control\n" if mode == "wrong-compiler" else "typst 0.15.1 unit-control\n") if name == "typst" else name + " unit-version\n"
                return subprocess.CompletedProcess(command, 0, "" if mode == "empty-version" else version, "")
            if command[:2] == ["typst", "compile"]:
                if mode == "timeout":
                    raise subprocess.TimeoutExpired(command, 60, output=b"partial stdout", stderr=b"partial diagnostic")
                if mode == "compiler-failure":
                    return subprocess.CompletedProcess(command, 7, "", "synthetic compiler failure")
                if mode != "missing-pdf":
                    Path(command[-1]).write_bytes(b"%PDF synthetic unit control, not a real document\n")
                return subprocess.CompletedProcess(command, 0, "", "")
            if name == "qpdf" and command[1] == "--check":
                return subprocess.CompletedProcess(command, 2 if mode == "pdf-failure" else 0, "", "synthetic qpdf diagnostic")
            if name == "pdfinfo":
                value = "Pages: 1\n" if mode != "missing-page-count" else "No page count\n"
            elif name == "qpdf":
                value = "not-json" if mode == "malformed-native" else json.dumps({"pages": [] if mode == "native-page-mismatch" else [{}]})
            elif command[1] == "-layout":
                value = "" if mode == "empty-text" else "UNIT BODY CONTROL\f"
            else:
                value = "<document></document>" if mode == "bbox-page-mismatch" else "<document><page/></document>"
            return subprocess.CompletedProcess(command, 0, value, "")

        def run(command, log_name, commands=None, *, combined=False, expected_exit=0):
            # Mock the stable runner boundary. The runner's OS supervision has
            # separate real-command tests; this corpus checks adapter behavior.
            self.assertEqual(adapter.verify.TIMEOUT_SECONDS, 60)
            stdout = stderr = ""
            record = {
                "command": command, "timeout_seconds": 60, "unit_mock": True,
                "exit_code": None, "expected_exit_code": expected_exit, "timed_out": False,
            }
            failure = None
            try:
                result = response(command)
                stdout, stderr = result.stdout, result.stderr
                record["exit_code"] = result.returncode
            except subprocess.TimeoutExpired:
                stdout, stderr = "partial stdout", "partial diagnostic"
                record.update(timed_out=True, exit_code=-9)
                failure = "synthetic runner timeout"
            except OSError as exc:
                failure = str(exc)
            log = adapter.verify.OUTPUT / log_name
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("UNIT MOCK RUNNER RESPONSE\n" + stdout + stderr + (failure or ""))
            record.update(log=log.relative_to(ROOT).as_posix(),
                          log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
            if commands is not None:
                commands.append(record)
            if failure or record["exit_code"] != expected_exit:
                raise adapter.verify.VerificationError(failure or "synthetic command failure")
            return stdout + stderr if combined else stdout
        return run

    def test_five_layers_and_explicit_false(self):
        metadata = {"layout": "print", "metadata": {"author": {"student_record_name": "Metadata author", "orcid": None}}}
        cli = ["metadata.author.student_record_name=CLI author", "double_sided=true"]
        explicit = {"double_sided": False, "metadata": {"title": "Explicit title"}}
        before = deepcopy((metadata, cli, explicit))
        result = adapter.resolve_inputs(self.bundle, metadata, cli, explicit)["configuration"]
        self.assertIs(result["double_sided"], False)
        self.assertEqual(result["layout"], "print")
        self.assertEqual(result["metadata"], {"author": {"student_record_name": "CLI author", "orcid": None}, "title": "Explicit title"})
        self.assertEqual((metadata, cli, explicit), before)

    def test_highest_layout_selects_profile_before_defaults(self):
        result = adapter.resolve_inputs(self.bundle, {"layout": "print"}, ["layout=screen"], {"layout": "default"})
        self.assertEqual(result["configuration"]["layout"], "default")
        self.assertIs(result["configuration"]["double_sided"], False)
        print_result = adapter.resolve_inputs(self.bundle, {"layout": "print"})
        self.assertIs(print_result["configuration"]["double_sided"], True)

    def test_invalid_lower_layer_is_not_hidden_by_explicit_value(self):
        with self.assertRaises(ContractError) as caught:
            adapter.resolve_inputs(self.bundle, {"double_sided": "false"}, [], {"double_sided": False})
        self.assertEqual(caught.exception.code, "invalid-type")

    def test_all_shared_invalid_inputs_stop_before_tools(self):
        for identifier, row in self.bundle.fixtures.items():
            fixture = json.loads((CONTRACT / row["path"]).read_text())
            if fixture["expected"]["result"] != "invalid":
                continue
            with self.subTest(identifier=identifier), patch.object(adapter.verify, "run") as tool:
                status, report = self.invoke(self.args(identifier))
                self.assertEqual(status, 1)
                self.assertEqual(report["result"], "rejected")
                self.assertEqual(report["error_code"], fixture["expected"]["error_code"])
                self.assertEqual(report["commands"], [])
                self.assertIsNone(report["normalized_configuration"])
                self.assertFalse((self.output / "document.pdf").exists())
                tool.assert_not_called()

    def test_shared_unsupported_cases_are_valid_but_not_rendered(self):
        for identifier in ("blind-draft", "joint-resubmission", "masters-publication", "non-english-creative", "public-deposit-input"):
            with self.subTest(identifier=identifier), patch.object(adapter.verify, "run") as tool:
                status, report = self.invoke(self.args(identifier))
                self.assertEqual(status, 2)
                self.assertEqual(report["normalization"], "valid")
                self.assertEqual(report["result"], "unsupported")
                self.assertTrue(report["unsupported_paths"])
                self.assertFalse((self.output / "document.pdf").exists())
                tool.assert_not_called()

    def test_additional_unimplemented_dimensions_are_explicit(self):
        inputs = [({"output": "html"}, "output"), ({"label_locale": "zh"}, "label_locale"),
                  ({"pdf_standards": ["pdf/ua-1"]}, "pdf_standards"),
                  ({"bibliography": {"mode": "per-publication"}}, "bibliography"),
                  ({"metadata": {"declarations": {"original_work": False}}}, "metadata.declarations.original_work"),
                  ({"metadata": {"declarations": {"contributions": "Synthetic contribution"}}}, "metadata.declarations.contributions")]
        for metadata, path in inputs:
            with self.subTest(path=path), patch.object(adapter.verify, "run") as tool:
                status, report = self.invoke(self.render_args(metadata))
                self.assertEqual(status, 2)
                self.assertIn(path, report["unsupported_paths"])
                tool.assert_not_called()

    def test_wrong_pins_or_unknown_fixture_stop_before_tools(self):
        attempts = [(self.args(contract="0" * 64), "wrong-contract"),
                    (self.args(manifest="0" * 64), "stale-fixture"),
                    (self.args(fixture="0" * 64), "stale-fixture"),
                    (self.args("missing-fixture"), "stale-fixture")]
        for args, code in attempts:
            with self.subTest(code=code), patch.object(adapter.verify, "run") as tool:
                status, report = self.invoke(args)
                self.assertEqual(status, 1)
                self.assertEqual(report["error_code"], code)
                tool.assert_not_called()

    def test_stale_adapter_api_rejected(self):
        stale = copy(self.bundle)
        stale.compatibility = deepcopy(self.bundle.compatibility)
        stale.compatibility["adapter_api_version"] = "2.0.0"
        with patch.object(adapter, "load_bundle", return_value=stale):
            status, report = self.invoke(self.args())
        self.assertEqual(status, 1)
        self.assertEqual(report["error_code"], "stale-adapter")

    def test_supported_output_retains_bounded_commands_and_real_artifact_hashes(self):
        with patch.object(adapter.verify, "run", side_effect=self.fake_tools()):
            status, report = self.invoke(self.args())
        self.assertEqual(status, 0)
        self.assertEqual(report["result"], "rendered")
        self.assertEqual(len(report["commands"]), 10)
        self.assertTrue(all(c["timeout_seconds"] == 60 and not c["timed_out"] and c["exit_code"] == 0 for c in report["commands"]))
        for name, expected in report["artifacts"].items():
            self.assertEqual(hashlib.sha256((self.output / name).read_bytes()).hexdigest(), expected)
        self.assertEqual(report["contract_acceptance"], "blocked-pending-adapter-registration-and-qualified-source")

    def test_wrong_compiler_is_rejected_before_compilation(self):
        with patch.object(adapter.verify, "run", side_effect=self.fake_tools("wrong-compiler")):
            status, report = self.invoke(self.args())
        self.assertEqual(status, 1)
        self.assertEqual(report["result"], "failed")
        self.assertIn("Expected Typst 0.15.1", report["error"])
        self.assertEqual([r["command"] for r in report["commands"]], [["typst", "--version"]])
        self.assertFalse((self.output / "document.pdf").exists())
        self.assertEqual(report["typst_manifest_sha256"], report["source_sha256_before"]["typst.toml"])

    def test_file_cli_and_explicit_inputs_feed_one_prepared_configuration(self):
        args = self.render_args({"layout": "print", "double_sided": True}, {"double_sided": False}, ["layout=screen"])
        with patch.object(adapter.verify, "run", side_effect=self.fake_tools()):
            status, report = self.invoke(args)
        prepared = json.loads((self.output / "input.json").read_text())
        self.assertEqual(status, 0)
        self.assertEqual(prepared["configuration"], report["normalized_configuration"])
        self.assertIs(prepared["configuration"]["double_sided"], False)
        self.assertEqual(prepared["configuration"]["layout"], "screen")

    def test_tool_failures_missing_outputs_and_malformed_reports_fail_closed(self):
        for mode in ("missing-tool", "empty-version", "compiler-failure", "missing-pdf", "pdf-failure",
                     "missing-page-count", "empty-text", "malformed-native", "native-page-mismatch", "bbox-page-mismatch"):
            with self.subTest(mode=mode), patch.object(adapter.verify, "run", side_effect=self.fake_tools(mode)):
                status, report = self.invoke(self.args())
                self.assertEqual(status, 1)
                self.assertEqual(report["result"], "failed")
                self.assertEqual(report["error_code"], "execution-failed")
                self.assertNotEqual(report["rendering"], "executed")

    def test_timeout_keeps_partial_diagnostic_and_cannot_be_pass(self):
        with patch.object(adapter.verify, "run", side_effect=self.fake_tools("timeout")):
            status, report = self.invoke(self.args())
        self.assertEqual(status, 1)
        self.assertEqual(report["rendering"], "failed")
        command = report["commands"][-1]
        self.assertTrue(command["timed_out"])
        self.assertNotEqual(command["exit_code"], 0)
        text = (ROOT / command["log"]).read_text()
        self.assertIn("partial stdout", text)
        self.assertIn("partial diagnostic", text)
        self.assertFalse((self.output / "document.pdf").exists())

    def test_stale_success_and_generated_outputs_do_not_survive_rejection(self):
        self.output.mkdir()
        for name in adapter.GENERATED_NAMES:
            (self.output / name).write_text('{"passed":true}')
        preserved = self.output / "caller-data.json"
        preserved.write_text('{"keep":true}')
        status, report = self.invoke(self.args("bad-month"))
        self.assertEqual(status, 1)
        self.assertEqual(report["result"], "rejected")
        self.assertEqual(set(report["artifacts"]), set())
        self.assertFalse((self.output / "document.pdf").exists())
        self.assertEqual(preserved.read_text(), '{"keep":true}')

    def test_missing_body_replaces_a_prior_success_receipt(self):
        self.output.mkdir()
        (self.output / "native-report.json").write_text('{"result":"rendered"}')
        (self.output / "document.pdf").write_bytes(b"old successful output")
        args = self.args()
        args[args.index("fixture"):args.index("fixture")] = ["--body", "missing-body.typ"]
        status, report = self.invoke(args)
        self.assertEqual(status, 1)
        self.assertEqual(report["error_code"], "invalid-resource")
        self.assertFalse((self.output / "document.pdf").exists())

    def test_missing_or_nonobject_metadata_is_rejected(self):
        for value in ([], None):
            args = self.render_args([] if value == [] else {})
            if value is None:
                (self.root / "metadata.json").unlink()
            with self.subTest(value=value):
                status, report = self.invoke(args)
                self.assertEqual(status, 1)
                self.assertEqual(report["error_code"], "invalid-type" if value == [] else "bundle-invalid")

    def test_body_symlink_is_rejected(self):
        alias = self.root / "body-link.typ"
        alias.symlink_to(ROOT / adapter.DEFAULT_BODY)
        args = self.args()
        args[args.index("fixture"):args.index("fixture")] = ["--body", str(alias)]
        status, report = self.invoke(args)
        self.assertEqual(status, 1)
        self.assertEqual(report["error_code"], "invalid-resource")

    def test_output_must_be_a_build_subdirectory(self):
        args = self.args()
        args[args.index("--output") + 1] = str(ROOT / "build")
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            adapter.main(args)
        self.assertEqual(caught.exception.code, 2)

    def test_source_change_or_loss_invalidates_a_success(self):
        for final in ({"fixture": "changed"}, FileNotFoundError("synthetic source missing")):
            with self.subTest(final=str(final)), patch.object(adapter, "source_hashes", side_effect=[{"fixture": "original"}, final]), \
                    patch.object(adapter.verify, "run", side_effect=self.fake_tools()):
                status, report = self.invoke(self.args())
                self.assertEqual(status, 1)
                self.assertEqual(report["result"], "failed")
                self.assertEqual(report["error_code"], "stale-source")
                self.assertFalse(report["sources_unchanged"])

    def test_corpus_invocation_uses_the_parser_without_a_nested_process(self):
        self.output.mkdir()
        entry = {"invocations": []}
        saved = adapter.verify.ROOT, adapter.verify.OUTPUT

        def main(arguments):
            self.assertEqual(arguments, ["synthetic", "arguments"])
            adapter.verify.ROOT, adapter.verify.OUTPUT = self.root, self.output
            print("synthetic parser output")
            return 0

        with patch.object(corpus.adapter, "main", side_effect=main), \
                patch.object(corpus.verify, "run", side_effect=AssertionError("Unexpected process wrapper")):
            corpus.invoke_adapter(["synthetic", "arguments"], self.output, entry, 0)
        self.assertEqual((adapter.verify.ROOT, adapter.verify.OUTPUT), saved)
        self.assertFalse(entry["invocations"][0]["external_process"])
        self.assertEqual(entry["invocations"][0]["return_code"], 0)
        self.assertIn("synthetic parser output", (self.output / "adapter-invocation.log").read_text())

    def test_corpus_invocation_restores_state_and_rejects_failure_or_boolean_status(self):
        self.output.mkdir()
        saved = adapter.verify.ROOT, adapter.verify.OUTPUT
        for failure in (True, False):
            entry = {"invocations": []}

            def main(arguments):
                adapter.verify.ROOT, adapter.verify.OUTPUT = self.root, self.output
                print("synthetic parser diagnostic", file=adapter.sys.stderr)
                if failure:
                    raise RuntimeError("synthetic parser failure")
                return False

            with self.subTest(failure=failure), patch.object(corpus.adapter, "main", side_effect=main), \
                    self.assertRaises(RuntimeError if failure else adapter.verify.VerificationError):
                corpus.invoke_adapter([], self.output, entry, 0)
            self.assertEqual((adapter.verify.ROOT, adapter.verify.OUTPUT), saved)
            self.assertIn("synthetic parser diagnostic", (self.output / "adapter-invocation.log").read_text())


if __name__ == "__main__":
    unittest.main()
