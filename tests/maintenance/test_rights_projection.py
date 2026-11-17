"""Fail-closed source projection contract for examination and public deposit.

Only synthetic data is used. These tests do not establish actual permissions,
university approval or accessibility of any resulting PDF.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import rights_projection as rights


class RightsProjectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.source = self.folder / "private-source"
        self.source.mkdir()
        self.out = self.folder / "public-output"

    def material(self, name: str, content: str, visibility: str):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {
            "id": name.replace("/", "-"),
            "source": name,
            "visibility": visibility,
            "kind": "literal-text",
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }

    def manifest(self, *items):
        path = self.folder / "private-manifest.json"
        path.write_text(json.dumps({"schema_version": 1, "items": list(items)}), encoding="utf-8")
        return path

    def test_public_projection_omits_private_bytes_names_and_manifest(self):
        public = self.material("chapter.txt", "Public research result.", "public")
        private = self.material("sensitive-email-ana.txt", "SENTINEL-PRIVATE-ANA", "restricted")
        private["id"] = "author-private-name"
        result = rights.project(
            self.manifest(public, private), self.source, self.out,
            target="deposit-public",
        )
        self.assertEqual(result["included_count"], 1)
        self.assertEqual(result["withheld_count"], 1)
        combined = "\n".join(p.read_text() for p in self.out.rglob("*") if p.is_file())
        self.assertIn("Public research result.", combined)
        self.assertIn("Rights-restricted material omitted", combined)
        for value in ("SENTINEL-PRIVATE-ANA", "sensitive-email-ana", "author-private-name",
                      "private-source", "private-manifest"):
            self.assertNotIn(value, combined)
        self.assertEqual(sorted(p.name for p in self.out.iterdir()),
                         ["main.typ", "projection.json"])
        self.assertEqual(result["main_sha256"],
                         hashlib.sha256((self.out / "main.typ").read_bytes()).hexdigest())

    def test_examination_contains_restricted_material_in_controlled_output(self):
        public = self.material("intro.txt", "Research introduction.", "public")
        restricted = self.material("embargo.txt", "CONTROLLED-EXAMINATION-TEXT", "restricted")
        result = rights.project(self.manifest(public, restricted), self.source,
                                self.out, target="examination")
        self.assertEqual(result["included_count"], 2)
        self.assertEqual(result["withheld_count"], 0)
        self.assertIn("CONTROLLED-EXAMINATION-TEXT", (self.out / "main.typ").read_text())

    def test_quote_hash_and_typst_markup_are_literal_not_evaluated(self):
        public = self.material("public.txt", 'Quoted "\\ #import "secrets.typ" #let x = 42', "public")
        rights.project(self.manifest(public), self.source, self.out, target="deposit-public")
        rendered = (self.out / "main.typ").read_text()
        self.assertEqual(rendered.count("#par("), 1)
        self.assertNotIn('#import "secrets.typ"', rendered)
        self.assertIn('\\\"secrets.typ\\\"', rendered)

    def test_unknown_rights_refuse_public_output_without_partial_files(self):
        item = self.material("undecided.txt", "SENTINEL-UNKNOWN", "unresolved")
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out, target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_hash_mismatch_rejected_without_output(self):
        item = self.material("chapter.txt", "Original", "public")
        item["sha256"] = "0" * 64
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out, target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_missing_source_and_symlink_rejected_without_output(self):
        item = self.material("chapter.txt", "Visible", "public")
        (self.source / "chapter.txt").unlink()
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out, target="deposit-public")
        self.assertFalse(self.out.exists())
        outside = self.folder / "outside.txt"
        outside.write_text("SECRET-OUTSIDE")
        (self.source / "chapter.txt").symlink_to(outside)
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out, target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_traversal_absolute_windows_and_repeated_source_refused(self):
        item = self.material("chapter.txt", "Visible", "public")
        for value in ("../outside.txt", "/tmp/absolute.txt", r"..\\private.txt",
                      "./chapter.txt", "part//chapter.txt", ""):
            with self.subTest(path=value):
                bad = dict(item, source=value)
                with self.assertRaises(rights.ProjectionError):
                    rights.project(self.manifest(bad), self.source,
                                   self.out, target="deposit-public")
                self.assertFalse(self.out.exists())
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item, dict(item, id="other")), self.source,
                           self.out, target="deposit-public")


    def test_backslash_in_existing_source_path_is_rejected(self):
        # On POSIX a backslash can be a filename character, but Typst paths
        # forbid it. Reject it even when such a file exists and hashes match.
        invalid = "chapter" + chr(92) + "private.txt"
        item = self.material(invalid, "SENTINEL-NO-PROJECTION", "public")
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out,
                           target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_literal_nul_byte_cannot_enter_compiled_input(self):
        item = self.material("nul.txt", "Visible" + chr(0) + "hidden", "public")
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out,
                           target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_unhashable_visibility_is_rejected_with_stable_error(self):
        item = self.material("chapter.txt", "Visible", "public")
        item["visibility"] = {"malformed": True}
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out,
                           target="deposit-public")
        self.assertFalse(self.out.exists())

    def test_schema_strictness_and_unsupported_binary_is_fail_closed(self):
        item = self.material("chapter.txt", "Visible", "public")
        mutations = [
            dict(item, visibility="sometimes"),
            dict(item, kind="pdf-attachment"),
            dict(item, sha256="xyz"),
            dict(item, unexpected="value"),
            dict(item, id=""),
        ]
        for bad in mutations:
            with self.subTest(bad=bad):
                with self.assertRaises(rights.ProjectionError):
                    rights.project(self.manifest(bad), self.source,
                                   self.out, target="deposit-public")
                self.assertFalse(self.out.exists())
        with self.assertRaises(rights.ProjectionError):
            rights.project(self.manifest(item), self.source, self.out, target="blind-review")

    def test_destination_cannot_overwrite_or_overlap_source(self):
        item = self.material("chapter.txt", "Visible", "public")
        manifest = self.manifest(item)
        self.out.mkdir()
        with self.assertRaises(rights.ProjectionError):
            rights.project(manifest, self.source, self.out, target="deposit-public")
        with self.assertRaises(rights.ProjectionError):
            rights.project(manifest, self.source, self.source / "output",
                           target="deposit-public")

    def test_cli_projection_report_contains_only_public_data(self):
        item = self.material("public.txt", "Public content.", "public")
        secret = self.material("secret.txt", "DO-NOT-PUBLISH-SECRET", "restricted")
        args = [sys.executable, "-m", "scripts.rights_projection", "--manifest",
                str(self.manifest(item, secret)), "--source-root", str(self.source),
                "--destination", str(self.out), "--target", "deposit-public"]
        completed = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        public_report = json.loads((self.out / "projection.json").read_text())
        self.assertEqual(public_report["target"], "deposit-public")
        for value in ("secret.txt", "DO-NOT-PUBLISH-SECRET", "private-manifest"):
            self.assertNotIn(value, completed.stdout + json.dumps(public_report))


if __name__ == "__main__":
    unittest.main()
