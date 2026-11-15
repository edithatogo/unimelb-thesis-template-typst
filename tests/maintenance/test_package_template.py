"""Real-file controls for the local package builder/installer; no compiler proof."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import gzip
import io
import json
import os
from pathlib import Path
import runpy
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from scripts import package_template as package

REPOSITORY = Path(__file__).resolve().parents[2]
VERIFY = runpy.run_path(str(REPOSITORY / "scripts/verify_package.py"))
MANIFEST = """[package]
name = "unimelb-thesis-template"
version = "0.2.1"
entrypoint = "lib.typ"
authors = ["Synthetic Test Author"]
license = "Apache-2.0"
description = "Synthetic package test"
categories = ["thesis"]
compiler = "0.15.1"
exclude = ["/build/"]
[template]
path = "template"
entrypoint = "main.typ"
thumbnail = "thumbnail.png"
[tool.typst]
version = "0.15.1"
"""


class PackageTemplateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="package-unit-")
        self.area = Path(self.temporary.name)
        self.root = self.area / "source"
        self.root.mkdir()
        for name in package.PAYLOAD_PATHS:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("Synthetic byte fixture: " + name + "\n").encode())
        (self.root / "typst.toml").write_text(MANIFEST, encoding="utf-8")
        (self.root / "template/LICENSE").write_bytes((self.root / "LICENSE").read_bytes())
        self.archive = self.area / "package.tar.gz"
        self.receipt = package.build(self.root, self.archive)
        self.cache = self.area / "cache"

    def tearDown(self):
        self.temporary.cleanup()

    def rejected(self, code, call):
        with self.assertRaises(package.PackageError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def rewrite(self, change):
        members = []
        with tarfile.open(self.archive, "r:gz") as source:
            for item in source:
                members.append((item, source.extractfile(item).read()))
        members = change(members)
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as target:
            for item, data in members:
                item.size = len(data)
                target.addfile(item, io.BytesIO(data))
        self.archive.write_bytes(gzip.compress(raw.getvalue(), mtime=0))
        self.receipt["archive_bytes"] = self.archive.stat().st_size
        self.receipt["archive_sha256"] = package.sha256(self.archive.read_bytes())

    def test_deterministic_archive_keeps_only_audited_files_and_metadata(self):
        extra = self.root / "assets/fonts/PRIVATE-NOT-A-FONT.ttf"
        extra.parent.mkdir(parents=True, exist_ok=True)
        extra.write_text("Must not be distributed")
        (self.root / "private-notes.txt").write_text("Must not be distributed")
        again = self.area / "repeat.tar.gz"
        receipt = package.build(self.root, again)
        self.assertEqual(self.archive.read_bytes(), again.read_bytes())
        self.assertEqual(self.receipt, receipt)
        self.assertEqual(len(receipt["files"]), 50)
        self.assertFalse(receipt["registry_submission_qualified"])
        self.assertFalse(receipt["fonts_included"])
        with tarfile.open(again, "r:gz") as archive:
            members = archive.getmembers()
        self.assertEqual(len(members), 50)
        self.assertTrue(all(item.isfile() and item.mode == 0o644 and item.mtime == 0 for item in members))
        self.assertTrue(all(item.uid == item.gid == 0 and item.uname == item.gname == "" for item in members))
        self.assertNotIn("private-notes.txt", {item.name for item in members})
        self.assertFalse(any(item.name.startswith(("assets/fonts/", ".github/", "tests/")) for item in members))

    def test_manifest_rejects_incompatible_identity_template_and_vocabulary(self):
        original = package.tomllib.loads(MANIFEST)
        changes = [
            ("package", "name", "../escape"), ("package", "version", "1.0"),
            ("package", "entrypoint", "missing.typ"), ("package", "license", "MIT"),
            ("package", "compiler", "0.14.0"), ("package", "categories", ["academic"]),
            ("package", "disciplines", ["science"]), ("template", "path", "."),
            ("template", "thumbnail", "missing.jpg"), ("tool", "typst", None),
        ]
        for table, key, value in changes:
            with self.subTest(table=table, key=key, value=value):
                changed = deepcopy(original)
                changed[table][key] = value
                self.rejected("invalid-manifest", lambda: package.validate_manifest(changed))
        for invalid in (None, [], {"package": []}, {"package": original["package"]}):
            with self.subTest(value=invalid):
                self.rejected("invalid-manifest", lambda: package.validate_manifest(invalid))

    def test_manifest_requires_authors_exclusions_and_description(self):
        original = package.tomllib.loads(MANIFEST)
        for key, value in (("authors", []), ("authors", [None]), ("exclude", ""),
                           ("exclude", [""]), ("description", " "), ("description", None)):
            with self.subTest(key=key, value=value):
                changed = deepcopy(original)
                changed["package"][key] = value
                self.rejected("invalid-manifest", lambda: package.validate_manifest(changed))

    def test_missing_input_does_not_produce_an_archive(self):
        (self.root / "lib.typ").unlink()
        target = self.area / "missing.tar.gz"
        self.rejected("missing-source", lambda: package.build(self.root, target))
        self.assertFalse(target.exists())

    def test_input_symlinks_cannot_smuggle_external_files(self):
        source = self.root / "lib.typ"
        source.unlink()
        outside = self.area / "outside.typ"
        outside.write_text("Private external text")
        source.symlink_to(outside)
        self.rejected("symlink-source", lambda: package.collect_payload(self.root))
        self.assertEqual(outside.read_text(), "Private external text")

    def test_starter_licence_cannot_drift_from_repository_licence(self):
        (self.root / "template/LICENSE").write_text("Different rights")
        self.rejected("license-mismatch", lambda: package.collect_payload(self.root))

    def test_size_limits_fail_before_installation(self):
        with patch.object(package, "MAX_FILE_BYTES", 1):
            self.rejected("oversize-source", lambda: package.collect_payload(self.root))
            self.rejected("oversize-source", lambda: package.inspect_archive(self.archive, self.receipt))
        with patch.object(package, "MAX_PAYLOAD_BYTES", 1):
            self.rejected("oversize-payload", lambda: package.collect_payload(self.root))
        with patch.object(package, "MAX_ARCHIVE_BYTES", 1):
            self.rejected("oversize-archive", lambda: package.build(self.root, self.area / "oversize.tgz"))
            self.rejected("oversize-archive", lambda: package.inspect_archive(self.archive, self.receipt))
        with patch.object(package, "MAX_TAR_BYTES", 1):
            self.rejected("oversize-archive", lambda: package.inspect_archive(self.archive, self.receipt))

    def test_install_reproduces_payload_and_refuses_to_replace_a_version(self):
        destination = package.install(self.archive, self.receipt, self.cache)
        self.assertEqual(destination, self.cache / "local/unimelb-thesis-template/0.2.1")
        actual = {item.relative_to(destination).as_posix(): item.read_bytes()
                  for item in destination.rglob("*") if item.is_file()}
        expected = {name: (self.root / name).read_bytes() for name in package.PAYLOAD_PATHS}
        self.assertEqual(actual, expected)
        self.rejected("already-installed", lambda: package.install(self.archive, self.receipt, self.cache))
        self.assertEqual((destination / "lib.typ").read_bytes(), expected["lib.typ"])
        self.assertFalse(list(destination.parent.glob(".package-install-*")))


    def test_failed_install_removes_only_its_owned_staging_directory(self):
        with patch.object(Path, "chmod", side_effect=OSError("Synthetic write failure")):
            with self.assertRaises(OSError):
                package.install(self.archive, self.receipt, self.cache)
        namespace = self.cache / "local/unimelb-thesis-template"
        self.assertTrue(namespace.is_dir())
        self.assertEqual(list(namespace.iterdir()), [])
        self.assertEqual((self.root / "typst.toml").read_text(encoding="utf-8"), MANIFEST)

    def test_namespace_symlinks_and_files_do_not_redirect_writes(self):
        for depth in ("cache", "local", "name", "file"):
            with self.subTest(depth=depth):
                cache = self.area / ("redirect-" + depth)
                outside = self.area / ("outside-" + depth)
                outside.mkdir()
                (outside / "sentinel").write_text("Preserve me")
                if depth == "cache":
                    cache.symlink_to(outside, target_is_directory=True)
                else:
                    cache.mkdir()
                    if depth == "local":
                        (cache / "local").symlink_to(outside, target_is_directory=True)
                    elif depth == "file":
                        (cache / "local").write_text("Preserve namespace file")
                    else:
                        (cache / "local").mkdir()
                        (cache / "local/unimelb-thesis-template").symlink_to(outside, target_is_directory=True)
                self.rejected("unsafe-cache", lambda: package.install(self.archive, self.receipt, cache))
                self.assertEqual([item.name for item in outside.iterdir()], ["sentinel"])

    def test_archive_hash_and_byte_count_must_match_the_receipt(self):
        altered = deepcopy(self.receipt)
        altered["archive_sha256"] = "0" * 64
        self.rejected("archive-hash-mismatch", lambda: package.inspect_archive(self.archive, altered))
        altered = deepcopy(self.receipt)
        altered["archive_bytes"] += 1
        self.rejected("archive-hash-mismatch", lambda: package.inspect_archive(self.archive, altered))

    def test_member_tampering_cannot_hide_behind_a_new_archive_hash(self):
        def change(members):
            return [(item, b"Tampered library" if item.name == "lib.typ" else data) for item, data in members]
        self.rewrite(change)
        self.rejected("member-hash-mismatch", lambda: package.install(self.archive, self.receipt, self.cache))
        self.assertFalse(self.cache.exists())

    def test_unsafe_duplicate_missing_and_unexpected_members_are_rejected(self):
        original = self.archive.read_bytes()
        receipt = deepcopy(self.receipt)
        for mode, code in (("traversal", "unsafe-path"), ("duplicate", "duplicate-member"),
                           ("missing", "missing-member"), ("extra", "unexpected-member"),
                           ("symlink", "unexpected-member"), ("mode", "unexpected-member")):
            with self.subTest(mode=mode):
                self.archive.write_bytes(original)
                self.receipt = deepcopy(receipt)
                def change(members):
                    if mode == "missing":
                        return members[1:]
                    if mode == "duplicate":
                        return members + [deepcopy(members[0])]
                    item = tarfile.TarInfo("../escaped" if mode == "traversal" else "extra.typ")
                    item.mode = 0o644
                    if mode in ("traversal", "extra"):
                        return members + [(item, b"Must not extract")]
                    first, data = members[0]
                    if mode == "symlink":
                        first.type, first.linkname = tarfile.SYMTYPE, "/outside"
                    else:
                        first.mode = 0o755
                    return [(first, data), *members[1:]]
                self.rewrite(change)
                self.rejected(code, lambda: package.install(self.archive, self.receipt, self.cache))
                self.assertFalse(self.cache.exists())
                self.assertFalse((self.area / "escaped").exists())

    def test_receipt_schema_member_inventory_and_identity_are_required(self):
        for key, value in (("schema_version", True), ("files", {}), ("archive_bytes", False),
                           ("archive_sha256", "not-a-digest"), ("artifact_kind", "release")):
            with self.subTest(key=key):
                changed = deepcopy(self.receipt)
                changed[key] = value
                self.rejected("invalid-receipt", lambda: package.inspect_archive(self.archive, changed))
        for key, value in (("bytes", True), ("sha256", "invalid")):
            changed = deepcopy(self.receipt)
            changed["files"]["lib.typ"][key] = value
            self.rejected("invalid-receipt", lambda: package.inspect_archive(self.archive, changed))
        changed = deepcopy(self.receipt)
        changed["payload_bytes"] = 1
        self.rejected("invalid-receipt", lambda: package.inspect_archive(self.archive, changed))
        changed = deepcopy(self.receipt)
        changed["version"] = "0.2.2"
        self.rejected("identity-mismatch", lambda: package.inspect_archive(self.archive, changed))

    def test_paths_must_be_normalized_and_relative(self):
        for name in ("", "../escape", "a/../escape", "/absolute", "a//b", "a/./b", "a\\b", "a/", "a\x00b"):
            with self.subTest(name=name):
                self.rejected("unsafe-path", lambda: package.safe_name(name))
        self.assertEqual(package.safe_name("template/main.typ"), "template/main.typ")

    def test_build_outputs_cannot_alias_inputs_or_each_other(self):
        source = self.root / "typst.toml"
        original = source.read_bytes()
        archive = self.area / "fresh.tar.gz"
        receipt = self.area / "receipt.json"
        link = self.area / "linked-source"
        link.symlink_to(source)
        hardlink = self.area / "hardlinked-source"
        os.link(source, hardlink)
        for first, second in ((archive, source), (archive, link), (archive, hardlink),
                              (archive, archive), (link, receipt), (hardlink, receipt)):
            with self.subTest(archive=first.name, receipt=second.name):
                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    code = package.main(["build", "--root", str(self.root), "--archive", str(first), "--receipt", str(second)])
                self.assertEqual(code, 1)
                self.assertEqual(source.read_bytes(), original)
                self.assertFalse(archive.exists())
                self.assertFalse(receipt.exists())
        self.rejected("unsafe-output", lambda: package.build(self.root, hardlink))
        archive.write_bytes(b"Preserve existing archive")
        alias = self.area / "archive-hardlink"
        os.link(archive, alias)
        self.rejected("unsafe-output", lambda: package.validate_outputs(self.root, archive, alias))
        self.assertEqual(archive.read_bytes(), b"Preserve existing archive")

    def test_cli_build_install_and_failures_report_actual_status(self):
        archive, receipt = self.area / "cli.tgz", self.area / "cli.json"
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(package.main(["build", "--root", str(self.root), "--archive", str(archive), "--receipt", str(receipt)]), 0)
            self.assertEqual(package.main(["install", "--archive", str(archive), "--receipt", str(receipt), "--cache", str(self.cache)]), 0)
        self.assertEqual(json.loads(output.getvalue().splitlines()[0])["sha256"], package.sha256(archive.read_bytes()))
        receipt.write_text("{")
        errors = io.StringIO()
        with redirect_stderr(errors):
            self.assertEqual(package.main(["install", "--archive", str(archive), "--receipt", str(receipt), "--cache", str(self.cache)]), 1)
        self.assertIn("Package operation failed", errors.getvalue())

    def test_cli_outputs_preserve_existing_nonpayload_source_and_aliases(self):
        for relative in ("scripts/package_template.py", "scripts/verify.py",
                         "docs/packaging.md", "thumbnail.png", "docs/build/notes.txt"):
            source = self.root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            original = ("Preserve non-payload source: " + relative).encode()
            for role in ("archive", "receipt"):
                for kind in ("direct", "symlink", "hardlink"):
                    with self.subTest(source=relative, role=role, alias=kind):
                        source.write_bytes(original)
                        output = self.area / (relative.replace("/", "-") + "-" + role + "-" + kind)
                        output.mkdir()
                        destination = source
                        if kind != "direct":
                            destination = output / "source-alias"
                            if kind == "symlink":
                                destination.symlink_to(source)
                            else:
                                os.link(source, destination)
                        archive = destination if role == "archive" else output / "package.tgz"
                        receipt = destination if role == "receipt" else output / "receipt.json"
                        diagnostics = io.StringIO()
                        with redirect_stderr(diagnostics), redirect_stdout(io.StringIO()):
                            code = package.main(["build", "--root", str(self.root),
                                                 "--archive", str(archive), "--receipt", str(receipt)])
                        self.assertEqual(code, 1)
                        self.assertIn("unsafe-output", diagnostics.getvalue())
                        self.assertEqual(source.read_bytes(), original)
                        self.assertFalse((output / "package.tgz").exists())
                        self.assertFalse((output / "receipt.json").exists())

    def test_direct_build_preserves_source_hardlinks_inside_generated_output(self):
        source = self.root / "unlisted-source.txt"
        original = b"Existing source must not be replaced through an output alias"
        source.write_bytes(original)
        for directory in ("build", "dist", "target"):
            with self.subTest(directory=directory):
                output = self.root / directory
                output.mkdir()
                alias = output / "archive.tgz"
                os.link(source, alias)
                self.rejected("unsafe-output", lambda: package.build(self.root, alias))
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(alias.read_bytes(), original)

    def test_ordinary_build_outputs_can_be_rebuilt_without_touching_source(self):
        original = {name: (self.root / name).read_bytes() for name in package.PAYLOAD_PATHS}
        for parent in (self.root / "build/package", self.root / "dist/package",
                       self.root / "target/package", self.area / "external-output"):
            with self.subTest(parent=parent):
                parent.mkdir(parents=True)
                archive, receipt = parent / "package.tgz", parent / "receipt.json"
                archive.write_bytes(b"Previous archive output")
                receipt.write_text("Previous receipt output")
                for repeat in range(2):
                    with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                        code = package.main(["build", "--root", str(self.root),
                                             "--archive", str(archive), "--receipt", str(receipt)])
                    self.assertEqual(code, 0)
                    observed = json.loads(receipt.read_text())
                    self.assertEqual(package.inspect_archive(archive, observed)[1], original)
                self.assertEqual({name: (self.root / name).read_bytes() for name in original}, original)

    def test_package_cleanup_cannot_delete_source_external_or_symlink_targets(self):
        guarded = self.root / "build/verification/package"
        guarded.mkdir(parents=True)
        (guarded / "old.pdf").write_bytes(b"stale")
        VERIFY["clean_output"](self.root, guarded)
        self.assertTrue(guarded.is_dir())
        self.assertEqual(list(guarded.iterdir()), [])
        source = self.root / "lib.typ"
        original = source.read_bytes()
        outside = self.area / "package"
        outside.mkdir()
        marker = outside / "retain.txt"
        marker.write_text("Preserve outside")
        linked = self.root / "build/linked/package"
        linked.parent.mkdir()
        linked.symlink_to(outside, target_is_directory=True)
        for unsafe in (self.root, self.root / "build", self.root / "config", outside, linked):
            with self.subTest(path=unsafe):
                with self.assertRaises(ValueError):
                    VERIFY["clean_output"](self.root, unsafe)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual(marker.read_text(), "Preserve outside")
