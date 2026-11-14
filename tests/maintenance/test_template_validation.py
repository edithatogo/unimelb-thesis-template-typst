"""Tests of repository validation using a temporary synthetic template.

The legacy delimiter scan is advisory. Actual Typst compilation remains a
separate gate; Python coverage does not measure rendered document correctness.
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from scripts import validate_template


class TemplateValidationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="typst validation ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)
        for directory in (
            "utils", "pages", "layouts", "assets/logos", "assets/colors",
            "assets/fonts", "docs", ".github/workflows",
        ):
            Path(directory).mkdir(parents=True, exist_ok=True)
        for filename in (
            "thesis.typ", "lib.typ", "typst.toml", "README.md",
            "utils/style.typ", "pages/title.typ", "pages/abstract.typ",
            "pages/declaration.typ", "layouts/document.typ",
            "assets/colors/unimelb-colors.typ",
        ):
            Path(filename).write_text("", encoding="utf-8")
        Path("typst.toml").write_text(
            '[package]\nname = "synthetic-thesis"\n'
            'version = "0.1.0"\nentrypoint = "lib.typ"\n',
            encoding="utf-8",
        )
        Path("assets/colors/unimelb-colors.typ").write_text(
            '#let traditional-heritage-100 = rgb("#000F46")\n',
            encoding="utf-8",
        )
        self.output = io.StringIO()
        redirect = redirect_stdout(self.output)
        redirect.__enter__()
        self.addCleanup(redirect.__exit__, None, None, None)

    def test_complete_directory_structure_passes(self):
        self.assertTrue(validate_template.validate_directory_structure())

    def test_missing_required_directory_fails_with_path(self):
        Path("assets/fonts").rmdir()
        self.assertFalse(validate_template.validate_directory_structure())
        self.assertIn("assets/fonts", self.output.getvalue())

    def test_file_cannot_satisfy_a_required_directory(self):
        Path("assets/fonts").rmdir()
        Path("assets/fonts").write_text("not a directory", encoding="utf-8")
        self.assertFalse(validate_template.validate_directory_structure())

    def test_required_files_pass_without_optional_official_logo(self):
        self.assertTrue(validate_template.validate_required_files())
        self.assertIn("Missing optional files", self.output.getvalue())
        self.assertIn("assets/logos/README.md", self.output.getvalue())

    def test_present_optional_logo_removes_optional_warning(self):
        Path("assets/logos/unimelb-logo-official.svg").write_text(
            "<svg></svg>\n", encoding="utf-8"
        )
        self.assertTrue(validate_template.validate_required_files())
        self.assertNotIn("Missing optional files", self.output.getvalue())

    def test_missing_entrypoint_fails_with_path(self):
        Path("lib.typ").unlink()
        self.assertFalse(validate_template.validate_required_files())
        self.assertIn("lib.typ", self.output.getvalue())

    def test_directory_cannot_satisfy_a_required_file(self):
        Path("thesis.typ").unlink()
        Path("thesis.typ").mkdir()
        self.assertFalse(validate_template.validate_required_files())
        self.assertIn("thesis.typ", self.output.getvalue())

    def test_valid_package_table_is_accepted(self):
        self.assertTrue(validate_template.validate_typst_toml())

    def test_missing_metadata_field_fails_with_field_name(self):
        Path("typst.toml").write_text(
            '[package]\nname = "synthetic-thesis"\nentrypoint = "lib.typ"\n',
            encoding="utf-8",
        )
        self.assertFalse(validate_template.validate_typst_toml())
        self.assertIn("Package field 'version' must be a non-empty string", self.output.getvalue())

    def test_unreadable_metadata_fails_with_diagnostic(self):
        Path("typst.toml").unlink()
        self.assertFalse(validate_template.validate_typst_toml())
        self.assertIn("Error reading typst.toml", self.output.getvalue())

    def test_supported_brand_color_spellings_pass(self):
        for color in ("#000F46", "000F46"):
            with self.subTest(color=color):
                Path("assets/colors/unimelb-colors.typ").write_text(
                    f'#let traditional-heritage-100 = rgb("{color}")\n',
                    encoding="utf-8",
                )
                self.assertTrue(validate_template.validate_color_definitions())

    def test_changed_brand_color_fails(self):
        Path("assets/colors/unimelb-colors.typ").write_text(
            '#let traditional-heritage-100 = rgb("#FFFFFF")\n',
            encoding="utf-8",
        )
        self.assertFalse(validate_template.validate_color_definitions())
        self.assertIn("Primary brand color not found", self.output.getvalue())

    def test_missing_color_file_fails_with_diagnostic(self):
        Path("assets/colors/unimelb-colors.typ").unlink()
        self.assertFalse(validate_template.validate_color_definitions())
        self.assertIn("Error reading color definitions", self.output.getvalue())

    def test_delimiters_inside_strings_math_and_code_are_ignored(self):
        Path("thesis.typ").write_text(
            '#let sample = "{[("\n'
            "$ { [ ( $\n"
            "\x60\x60\x60typ\n{[(\n\x60\x60\x60\n",
            encoding="utf-8",
        )
        self.assertTrue(validate_template.validate_typst_syntax())
        self.assertNotIn("Possible unmatched", self.output.getvalue())

    def test_delimiter_warnings_remain_explicitly_advisory(self):
        Path("thesis.typ").write_text("{ [ (\n", encoding="utf-8")
        self.assertTrue(validate_template.validate_typst_syntax())
        for delimiter in ("braces", "brackets", "parentheses"):
            self.assertIn(f"Possible unmatched {delimiter}", self.output.getvalue())
        self.assertIn("typst compile", self.output.getvalue())

    def test_syntax_read_errors_are_reported_as_advisory_warnings(self):
        with (
            patch.object(validate_template.Path, "rglob", return_value=[Path("denied.typ")]),
            patch("builtins.open", side_effect=PermissionError("synthetic access denied")),
        ):
            self.assertTrue(validate_template.validate_typst_syntax())
        self.assertIn("Error reading denied.typ", self.output.getvalue())
        self.assertIn("synthetic access denied", self.output.getvalue())
        self.assertIn("may include false positives", self.output.getvalue())

    def test_main_returns_success_only_when_all_required_checks_pass(self):
        self.assertEqual(validate_template.main(), 0)
        self.assertIn("5/5 checks passed", self.output.getvalue())

    def test_main_reports_multiple_failures_and_returns_nonzero(self):
        Path("assets/fonts").rmdir()
        Path("README.md").unlink()
        Path("typst.toml").write_text("[package]\n", encoding="utf-8")
        Path("assets/colors/unimelb-colors.typ").write_text("", encoding="utf-8")
        self.assertEqual(validate_template.main(), 1)
        report = self.output.getvalue()
        self.assertIn("1/5 checks passed", report)
        self.assertIn("Missing directories", report)
        self.assertIn("Missing required files", report)
        self.assertIn("Package field 'name' must be a non-empty string", report)
        self.assertIn("Primary brand color not found", report)


if __name__ == "__main__":
    unittest.main()
