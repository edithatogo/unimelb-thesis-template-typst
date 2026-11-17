"""Independent bundle structure/safety oracles; all examples are synthetic."""
from __future__ import annotations

import hashlib
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import web_bundle_validation as web


class WebBundleValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.work = Path(temp.name)
        self.bundle = self.work / "bundle"
        self.bundle.mkdir()
        (self.bundle / "chapters").mkdir()
        (self.bundle / "assets").mkdir()
        self.valid_pages()

    def write(self, relative, content):
        path = self.bundle / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def valid_pages(self):
        self.write("index.html", (
            '<!doctype html><html lang="en"><head><title>Thesis</title></head><body>'
            '<h1 id="home">Synthetic thesis</h1>'
            '<p><a href="chapters/methods.html#methods">Methods</a></p>'
            '<img src="assets/figure.svg" alt="Synthetic method flow"/>'
            '<math><mi>x</mi><mo>=</mo><mn>1</mn></math>'
            '</body></html>'))
        self.write("chapters/methods.html", (
            '<!doctype html><html lang="en"><head><title>Methods</title></head><body>'
            '<h1 id="methods">Methods</h1><a href="../index.html#home">Home</a>'
            '<h2>Study design</h2><p>Only synthetic public material.</p>'
            '</body></html>'))
        self.write("assets/figure.svg", '<svg xmlns="http://www.w3.org/2000/svg"></svg>')

    def check(self, **kw):
        return web.inspect_bundle(
            self.bundle, required_pages=("index.html", "chapters/methods.html"), **kw)

    def test_valid_public_two_page_bundle_and_mathml(self):
        result = self.check(forbidden=("DO-NOT-PUBLISH",))
        self.assertEqual(result["html_pages"], 2)
        self.assertEqual(result["mathml_elements"], 1)
        self.assertEqual(len(result["files"]), 3)
        self.assertEqual(result["files"]["index.html"],
                         hashlib.sha256((self.bundle / "index.html").read_bytes()).hexdigest())
        self.assertEqual(result["status"], "structural-validation-only")

    def test_missing_and_ambiguous_required_pages_fail(self):
        (self.bundle / "chapters/methods.html").unlink()
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_missing_local_target_and_fragment_fail(self):
        for href in ('chapters/missing.html', 'chapters/methods.html#unknown', '#absent'):
            with self.subTest(href=href):
                self.valid_pages()
                p = self.bundle / "index.html"
                p.write_text(p.read_text().replace("chapters/methods.html#methods", href))
                with self.assertRaises(web.WebBundleError):
                    self.check()

    def test_normalized_parent_link_allowed_but_escape_rejected(self):
        self.assertEqual(self.check()["html_pages"], 2)
        for link in ("../outside.html", "chapters/%2e%2e/%2e%2e/private.html",
                     "javascript:alert(1)", "//example.test/tracker.js"):
            with self.subTest(link=link):
                self.valid_pages()
                p = self.bundle / "index.html"
                p.write_text(p.read_text().replace("chapters/methods.html#methods", link))
                with self.assertRaises(web.WebBundleError):
                    self.check()

    def test_missing_alt_and_unlabeled_math_handled_separately(self):
        p = self.bundle / "index.html"
        p.write_text(p.read_text().replace('alt="Synthetic method flow"', ""))
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_html_semantics_and_language_are_checked(self):
        p = self.bundle / "index.html"
        for replacement in ('<html>', '<html lang="">', '<html lang="   ">'):
            self.valid_pages()
            p.write_text(p.read_text().replace('<html lang="en">', replacement))
            with self.assertRaises(web.WebBundleError):
                self.check()
        self.valid_pages()
        p.write_text(p.read_text().replace("<h1 id=", "<h3 id="))
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_unsafe_executable_content_and_bad_tables_fail(self):
        p = self.bundle / "index.html"
        for addition in ('<script>alert(1)</script>',
                         '<iframe src="https://example.org"></iframe>',
                         '<table><tr><td>data</td></tr></table>'):
            with self.subTest(content=addition):
                self.valid_pages()
                p.write_text(p.read_text().replace('</body>', addition + '</body>'))
                with self.assertRaises(web.WebBundleError):
                    self.check()


    def test_all_event_handlers_are_rejected_not_only_onload(self):
        page = self.bundle / "index.html"
        for handler in ('onerror="steal()"', 'onmouseover="steal()"',
                        'onfocus="steal()"'):
            with self.subTest(handler=handler):
                self.valid_pages()
                page.write_text(page.read_text().replace(
                    '<img src=', '<img ' + handler + ' src='))
                with self.assertRaises(web.WebBundleError):
                    self.check()

    def test_external_stylesheet_is_not_an_author_link(self):
        page = self.bundle / "index.html"
        page.write_text(page.read_text().replace(
            '</head>', '<link rel="stylesheet" href="https://example.test/remote.css"></head>'
        ))
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_duplicate_ids_are_rejected(self):
        p = self.bundle / "index.html"
        p.write_text(p.read_text().replace('</body>', '<h2 id="home">Duplicate</h2></body>'))
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_restricted_sentinels_checked_across_assets_without_leakage(self):
        (self.bundle / "assets/figure.svg").write_text("DO-NOT-PUBLISH-SENTINEL")
        with self.assertRaises(web.WebBundleError) as exception:
            self.check(forbidden=("DO-NOT-PUBLISH-SENTINEL",))
        self.assertNotIn("DO-NOT-PUBLISH-SENTINEL", str(exception.exception))

    def test_symlink_assets_and_unapproved_extensions_are_rejected(self):
        outside = self.work / "outside.svg"
        outside.write_text("OTHER-PRIVATE")
        (self.bundle / "assets/figure.svg").unlink()
        (self.bundle / "assets/figure.svg").symlink_to(outside)
        with self.assertRaises(web.WebBundleError):
            self.check()
        (self.bundle / "assets/figure.svg").unlink()
        self.valid_pages()
        (self.bundle / "secret.py").write_text("unexpected")
        with self.assertRaises(web.WebBundleError):
            self.check()

    def test_cli_emits_only_an_inspectable_summary(self):
        cmd = [sys.executable, "-m", "scripts.web_bundle_validation", "--root", str(self.bundle),
               "--expect", "index.html", "--expect", "chapters/methods.html"]
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["html_pages"], 2)


if __name__ == "__main__":
    unittest.main()
