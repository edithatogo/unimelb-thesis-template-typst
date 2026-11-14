"""Behavioral tests for the Python preflight helper.

Compiler calls are mocked; these tests do not claim Typst/PDF coverage.
The subprocess wrapper itself is exercised with a harmless Python process.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import preflight


class PreflightTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="typst preflight ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.build = self.root / "build" / "preflight"
        self.document = self.root / "thesis.typ"
        self.document.write_text("= Synthetic thesis\n", encoding="utf-8")
        self.sample = self.root / "sample-chapter.typ"
        self.sample.write_text("= Synthetic sample\n", encoding="utf-8")
        self.absent_optional = self.root / "test-layout-only.typ"
        for name, value in {
            "REPO_ROOT": self.root,
            "BUILD_DIR": self.build,
            "DEFAULT_DOCUMENT": self.document,
            "EXTRA_TARGETS": (self.absent_optional, self.sample),
        }.items():
            patcher = patch.object(preflight, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_run_preserves_exit_status_and_stdout_and_stderr(self):
        status, output = preflight.run(
            [
                sys.executable,
                "-c",
                (
                    "import pathlib, sys; "
                    "print(pathlib.Path.cwd()); "
                    "print('synthetic diagnostic', file=sys.stderr); "
                    "sys.exit(7)"
                ),
            ],
            cwd=self.root,
        )
        self.assertEqual(status, 7)
        self.assertIn(str(self.root), output)
        self.assertIn("synthetic diagnostic", output)

    def test_missing_typst_has_actionable_error(self):
        with patch.object(preflight.shutil, "which", return_value=None):
            with self.assertRaisesRegex(preflight.PreflightError, "Typst CLI not found"):
                preflight.ensure_typst_available()

    def test_available_typst_is_accepted(self):
        with patch.object(preflight.shutil, "which", return_value="/toolchain/typst"):
            self.assertIsNone(preflight.ensure_typst_available())

    def test_missing_document_never_starts_compiler(self):
        missing = self.root / "missing.typ"
        with patch.object(preflight, "run") as run:
            with self.assertRaisesRegex(preflight.PreflightError, "does not exist"):
                preflight.compile_document(missing, "default")
        run.assert_not_called()

    def test_default_compilation_uses_separate_arguments_and_output_directory(self):
        output = self.build / "default" / "thesis.pdf"
        with patch.object(preflight, "run", return_value=(0, "")) as run:
            self.assertEqual(preflight.compile_document(self.document, "default"), output)
        self.assertTrue(output.parent.is_dir())
        run.assert_called_once_with(
            ["typst", "compile", str(self.document), str(output)],
            cwd=self.root,
        )

    def test_named_profiles_are_forwarded_and_have_distinct_outputs(self):
        outputs = set()
        for profile in ("draft", "screen", "print"):
            with self.subTest(profile=profile):
                expected = self.build / profile / f"thesis-{profile}.pdf"
                with patch.object(preflight, "run", return_value=(0, "")) as run:
                    output = preflight.compile_document(self.document, profile)
                outputs.add(output)
                self.assertEqual(output, expected)
                run.assert_called_once_with(
                    [
                        "typst",
                        "compile",
                        str(self.document),
                        str(expected),
                        "--input",
                        f"profile={profile}",
                    ],
                    cwd=self.root,
                )
        self.assertEqual(len(outputs), 3)

    def test_compiler_failure_preserves_document_profile_and_diagnostic(self):
        with patch.object(
            preflight, "run", return_value=(17, "error: unresolved synthetic reference")
        ):
            with self.assertRaises(preflight.PreflightError) as error:
                preflight.compile_document(self.document, "print")
        message = str(error.exception)
        self.assertIn(str(self.document), message)
        self.assertIn("profile 'print'", message)
        self.assertIn("error: unresolved synthetic reference", message)

    def test_placeholder_scan_reports_each_marker_once(self):
        markers = ("<title>", "<author>", "<degree>", "<department>", "<school>")
        self.document.write_text(" ".join(markers + markers), encoding="utf-8")
        issues = preflight.scan_for_placeholders(self.document)
        self.assertEqual(
            set(issues),
            {f"Placeholder '{marker}' found in thesis.typ" for marker in markers},
        )
        self.assertEqual(len(issues), len(markers))

    def test_completed_metadata_has_no_placeholder_warnings(self):
        self.assertEqual(preflight.scan_for_placeholders(self.document), [])

    def test_missing_input_preserves_read_failure_cause(self):
        with self.assertRaisesRegex(preflight.PreflightError, "Failed to read") as error:
            preflight.scan_for_placeholders(self.root / "absent.typ")
        self.assertIsInstance(error.exception.__cause__, FileNotFoundError)

    def test_cli_defaults_use_the_primary_document(self):
        args = preflight.parse_args([])
        self.assertEqual(args.document, self.document)
        self.assertIsNone(args.profiles)
        self.assertIsNone(args.extra_targets)
        self.assertFalse(args.emit_json)

    def test_cli_preserves_repeated_profiles_and_extra_paths(self):
        args = preflight.parse_args(
            [
                "--document", "primary.typ",
                "--profile", "default",
                "--profile", "print",
                "--extra", "first.typ",
                "--extra", "second.typ",
                "--json",
            ]
        )
        self.assertEqual(args.document, Path("primary.typ"))
        self.assertEqual(args.profiles, ["default", "print"])
        self.assertEqual(args.extra_targets, [Path("first.typ"), Path("second.typ")])
        self.assertTrue(args.emit_json)

    def test_cli_rejects_unknown_arguments(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                preflight.parse_args(["--unknown-option"])
        self.assertEqual(error.exception.code, 2)

    def test_main_json_lists_each_requested_document_and_profile(self):
        captured = io.StringIO()
        with (
            patch.object(preflight, "ensure_typst_available"),
            patch.object(preflight, "run", return_value=(0, "")) as run,
            redirect_stdout(captured),
        ):
            status = preflight.main(
                ["--profile", "default", "--profile", "screen", "--json"]
            )
        self.assertEqual(status, 0)
        self.assertEqual(run.call_count, 4)
        report = json.loads(captured.getvalue())
        self.assertEqual(report["profiles"], ["default", "screen"])
        self.assertEqual(report["metadata_warnings"], [])
        self.assertEqual(
            report["compiled"],
            [
                "build/preflight/default/thesis.pdf",
                "build/preflight/default/sample-chapter.pdf",
                "build/preflight/screen/thesis-screen.pdf",
                "build/preflight/screen/sample-chapter-screen.pdf",
            ],
        )

    def test_default_run_skips_absent_optional_example(self):
        captured = io.StringIO()
        with (
            patch.object(preflight, "ensure_typst_available"),
            patch.object(preflight, "run", return_value=(0, "")) as run,
            redirect_stdout(captured),
        ):
            self.assertEqual(preflight.main([]), 0)
        self.assertEqual(run.call_count, 2)
        commands = [item.args[0] for item in run.call_args_list]
        self.assertEqual([command[2] for command in commands], [
            str(self.document), str(self.sample)
        ])
        self.assertNotIn(str(self.absent_optional), captured.getvalue())
        self.assertIn("Preflight successful", captured.getvalue())

    def test_explicit_extra_replaces_default_examples(self):
        appendix = self.root / "appendix.typ"
        appendix.write_text("= Synthetic appendix\n", encoding="utf-8")
        with (
            patch.object(preflight, "ensure_typst_available"),
            patch.object(preflight, "run", return_value=(0, "")) as run,
            redirect_stdout(io.StringIO()),
        ):
            self.assertEqual(preflight.main(["--extra", str(appendix)]), 0)
        commands = [item.args[0] for item in run.call_args_list]
        self.assertEqual([command[2] for command in commands], [
            str(self.document), str(appendix)
        ])

    def test_metadata_warning_fails_validation_after_compilation(self):
        self.document.write_text("= <title>\n", encoding="utf-8")
        captured = io.StringIO()
        with (
            patch.object(preflight, "ensure_typst_available"),
            patch.object(preflight, "run", return_value=(0, "")) as run,
            redirect_stdout(captured),
        ):
            self.assertEqual(preflight.main([]), 2)
        self.assertEqual(run.call_count, 2)
        self.assertIn("Warnings:", captured.getvalue())
        self.assertIn("Placeholder '<title>' found in thesis.typ", captured.getvalue())

    def test_main_stops_on_first_compiler_failure(self):
        captured = io.StringIO()
        with (
            patch.object(preflight, "ensure_typst_available"),
            patch.object(preflight, "run", return_value=(1, "synthetic compile failure")) as run,
            redirect_stdout(captured),
        ):
            with self.assertRaisesRegex(preflight.PreflightError, "synthetic compile failure"):
                preflight.main(["--profile", "default", "--profile", "print"])
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("Preflight successful", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
