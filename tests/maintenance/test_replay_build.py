"""Real-file lock/tamper controls; mocked compiler results are not native proof."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts import replay_build as replay


class ReplayBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="replay-unit-")
        self.area = Path(self.temporary.name)
        self.root = self.area / "source"
        self.root.mkdir()
        self.recipe = {
            "schema_version": 1, "id": "synthetic-unit", "entrypoint": "document.typ",
            "creation_timestamp": 42, "cli_inputs": {"profile": "default"},
            "required_native_inputs": ["document.typ", "asset.txt"],
            "fonts": ["fonts/One.otf"], "font_licenses": ["fonts/LICENSE"],
            "expected_pdf_fonts": ["SyntheticFace"], "expected_text": ["SYNTHETIC"],
            "scope": "Unit interface fixture; no native compilation claimed",
        }
        for name in (*replay.RUNTIME_PATHS, "document.typ", "asset.txt", "LICENSE"):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("Synthetic input: " + name).encode())
        (self.root / "typst.toml").write_text('[tool.typst]\nversion="0.15.1"\n')
        (self.root / "fonts").mkdir()
        (self.root / "fonts/One.otf").write_bytes(b"F")
        (self.root / "fonts/LICENSE").write_bytes(b"Synthetic licence fixture")
        (self.root / "recipe.json").write_text(json.dumps(self.recipe))
        self.cache = self.area / "cache"
        package = self.cache / "preview/synthetic/1.0.0"
        package.mkdir(parents=True)
        (package / "typst.toml").write_text('[package]\nname="synthetic"\nversion="1.0.0"\nlicense="MIT"\n')
        (package / "lib.typ").write_bytes(b"Synthetic package source")
        (package / "LICENSE").write_bytes(b"Synthetic retained licence")
        self.tools = {}
        for name in replay.TOOL_ARGUMENTS:
            path = self.area / ("tool-" + name)
            path.write_bytes(("Synthetic executable bytes: " + name).encode())
            self.tools[name] = path
        self.tool_records = {
            name: {"sha256": replay.digest(path), "version": "typst 0.15.1 (synthetic)" if name == "typst" else name + " synthetic"}
            for name, path in self.tools.items()
        }
        self.pdf = b"Synthetic unit PDF bytes, not a native document"
        self.bundle = self.area / "bundle"
        self.bundle.mkdir()
        project = self.bundle / "project"
        project.mkdir()
        for name in self.recipe["required_native_inputs"]:
            shutil.copyfile(self.root / name, project / name)
        shutil.copytree(self.cache, self.bundle / "packages")
        shutil.copytree(self.root / "fonts", self.bundle / "fonts")
        project_files = replay.inventory(project)
        package_files = replay.inventory(self.bundle / "packages")
        observed = {"project:" + name: item["sha256"] for name, item in project_files.items()}
        observed["package-cache:preview/synthetic/1.0.0/lib.typ"] = package_files["preview/synthetic/1.0.0/lib.typ"]["sha256"]
        _, packages = replay.package_records(self.cache, observed, package_files)
        self.lock = {
            "schema_version": 1, "artifact_kind": "bounded-typst-replay-lock", "recipe": deepcopy(self.recipe),
            "source": {"git_revision": None, "git_tree": None, "git_dirty": None},
            "tools": self.tool_records, "environment": replay.environment(),
            "producer_sha256": replay.producer_identity(), "project_files": project_files,
            "package_files": package_files, "font_files": replay.inventory(self.bundle / "fonts"),
            "packages": packages,
            "font_sources": [{"source": p, "filename": Path(p).name,
                              "role": "font" if p in self.recipe["fonts"] else "license",
                              **replay.identity(self.root / p)} for p in self.recipe["fonts"] + self.recipe["font_licenses"]],
            "observed_inputs": observed, "expected_pdf_sha256": hashlib.sha256(self.pdf).hexdigest(),
            "scope": "Synthetic unit interface only",
        }
        self.save_lock()

    def tearDown(self):
        self.temporary.cleanup()

    def save_lock(self):
        (self.bundle / "lock.json").write_bytes(replay.canonical(self.lock) + b"\n")
        self.lock_digest = replay.digest(self.bundle / "lock.json")

    def reject(self, code, callback):
        with self.assertRaises(replay.ReplayError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def fake_compile(self, project, cache, fonts, recipe, tools):
        target = Path(project) / "_replay/document.pdf"
        self.assertFalse(target.exists())
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(self.pdf)
        inputs = [{"path": "project:" + p, "sha256_observed_after_compile": replay.digest(Path(project) / p)}
                  for p in recipe["required_native_inputs"]]
        inputs.append({"path": "package-cache:preview/synthetic/1.0.0/lib.typ",
                       "sha256_observed_after_compile": replay.digest(Path(cache) / "preview/synthetic/1.0.0/lib.typ")})
        return {"result": "pass", "pdf": replay.identity(target), "output": str(target),
                "native_inventory": {"inputs": inputs}, "unit_mock": True}

    def replay_call(self, output, callback=None):
        with patch.object(replay.shutil, "which", side_effect=lambda name: str(self.tools[name])), \
             patch.object(replay, "compile_isolated", side_effect=callback or self.fake_compile):
            return replay.replay(self.bundle, self.lock_digest, output, self.tools["typst"])

    def capture_call(self, output, callback=None, tool_records=None):
        with patch.object(replay.shutil, "which", side_effect=lambda name: str(self.tools[name])), \
             patch.object(replay, "tool_inventory", return_value=tool_records or self.tool_records), \
             patch.object(replay, "compile_isolated", side_effect=callback or self.fake_compile):
            return replay.make_lock(self.root, "recipe.json", self.cache, output, self.tools["typst"])

    def test_canonical_digest_preserves_types_and_rejects_nonfinite_values(self):
        self.assertEqual(replay.canonical({"b": 2, "a": False}), b'{"a":false,"b":2}')
        self.assertNotEqual(replay.canonical({"a": False}), replay.canonical({"a": 0}))
        with self.assertRaises(ValueError):
            replay.canonical({"a": float("nan")})

    def test_paths_reject_traversal_absolute_and_nonstring_names(self):
        for name in ("", "../x", "x/../y", "/x", "a//b", "a/./b", "a\\b", "a/", "a\x00b", None):
            with self.subTest(name=name):
                self.reject("unsafe-path", lambda: replay.safe_name(name))
        self.assertEqual(replay.safe_name("assets/a.svg"), "assets/a.svg")

    def test_input_symlinks_and_nonregular_entries_are_rejected(self):
        link = self.root / "alias"
        link.symlink_to(self.root / "asset.txt")
        self.reject("symlink-input", lambda: replay.source_path(self.root, "alias"))
        self.reject("symlink-input", lambda: replay.inventory(self.root))
        link.unlink()
        os.mkfifo(self.root / "pipe")
        self.reject("invalid-input", lambda: replay.inventory(self.root))

    def test_inventory_limits_and_missing_inputs_fail(self):
        with patch.object(replay, "MAX_FILES", 1):
            self.reject("input-limit", lambda: replay.inventory(self.root))
        with patch.object(replay, "MAX_BYTES", 1):
            self.reject("input-limit", lambda: replay.inventory(self.root))
        self.reject("missing-input", lambda: replay.source_path(self.root, "absent"))
        self.reject("missing-input", lambda: replay.inventory(self.area / "absent"))

    def test_file_inventory_rejects_boolean_counts_and_malformed_hashes(self):
        for value in ({}, [], {"x": {"sha256": "0" * 64, "bytes": True}},
                      {"x": {"sha256": "bad", "bytes": 1}}, {"x": {"sha256": "0" * 64, "bytes": -1}}):
            with self.subTest(value=value):
                self.reject("invalid-lock", lambda: replay.validate_inventory(value))
        with patch.object(replay, "MAX_BYTES", 1):
            self.reject("input-limit", lambda: replay.validate_inventory({"x": {"sha256": "0" * 64, "bytes": 2}}))

    def test_copy_produces_independent_readonly_files_and_checks_source_hash(self):
        files = {"asset.txt": replay.identity(self.root / "asset.txt")}
        target = self.area / "copied"
        replay.copy_inputs(self.root, target, files)
        self.assertEqual((target / "asset.txt").read_bytes(), (self.root / "asset.txt").read_bytes())
        self.assertFalse((target / "asset.txt").samefile(self.root / "asset.txt"))
        self.assertEqual((target / "asset.txt").stat().st_mode & 0o222, 0)
        (self.root / "asset.txt").write_bytes(b"changed")
        self.reject("input-mismatch", lambda: replay.copy_inputs(self.root, self.area / "stale-copy", files))

    def test_copy_detects_a_source_change_during_read(self):
        source = self.root / "asset.txt"
        files = {"asset.txt": replay.identity(source)}
        original_read, calls = Path.read_bytes, []
        def mutate(path):
            data = original_read(path)
            if path == source:
                calls.append(1)
                if len(calls) == 2:
                    path.write_bytes(b"mutated during copy")
            return data
        with patch.object(Path, "read_bytes", mutate):
            self.reject("input-mismatch", lambda: replay.copy_inputs(self.root, self.area / "raced-copy", files))

    def test_new_outputs_do_not_overwrite_existing_or_symlinked_paths(self):
        existing = self.area / "existing"
        existing.mkdir()
        (existing / "report.json").write_text("Keep earlier evidence")
        self.reject("unsafe-output", lambda: replay.new_output(existing))
        link = self.area / "alias"
        link.symlink_to(existing, target_is_directory=True)
        self.reject("unsafe-output", lambda: replay.new_output(link / "new"))
        self.assertEqual((existing / "report.json").read_text(), "Keep earlier evidence")

    def test_recipe_requires_exact_fields_types_unique_inputs_and_font_names(self):
        changes = [
            ("schema_version", True), ("creation_timestamp", True), ("creation_timestamp", -1),
            ("cli_inputs", {"profile": False}), ("expected_text", []),
            ("fonts", ["fonts/One.otf", "other/One.otf"]),
            ("required_native_inputs", ["asset.txt"]),
            ("required_native_inputs", ["document.typ", "_replay/stale.pdf"]),
        ]
        for key, value in changes:
            with self.subTest(key=key, value=value):
                recipe = deepcopy(self.recipe);recipe[key] = value
                self.reject("invalid-recipe", lambda: replay.validate_recipe(recipe))
        changed = deepcopy(self.recipe);changed["unexpected"] = True
        self.reject("invalid-recipe", lambda: replay.validate_recipe(changed))

    def test_lock_structure_cannot_omit_native_font_or_package_identity(self):
        for key, value in (("schema_version", False), ("artifact_kind", "release"),
                           ("observed_inputs", {}), ("font_sources", []), ("packages", []),
                           ("producer_sha256", {}), ("tools", {}), ("source", {})):
            with self.subTest(key=key):
                lock = deepcopy(self.lock);lock[key] = value
                self.reject("invalid-lock", lambda: replay.validate_lock(lock))
        lock = deepcopy(self.lock);del lock["observed_inputs"]["project:asset.txt"]
        self.reject("invalid-lock", lambda: replay.validate_lock(lock))

    def test_environment_boolean_and_font_byte_boolean_do_not_equal_integer_one(self):
        lock = deepcopy(self.lock);lock["environment"]["compiler_jobs"] = True
        self.reject("invalid-lock", lambda: replay.validate_lock(lock))
        lock = deepcopy(self.lock);lock["font_sources"][0]["bytes"] = True
        self.reject("invalid-lock", lambda: replay.validate_lock(lock))

    def test_nested_lock_metadata_cannot_contradict_the_actual_file_inventories(self):
        for change in (
            lambda v: v["font_sources"][0].update(role="license"),
            lambda v: v["packages"][0].update(content_inventory_sha256="0" * 64),
            lambda v: v["packages"].append(deepcopy(v["packages"][0])),
            lambda v: v["producer_sha256"].update({"scripts/replay_build.py": "bad"}),
        ):
            with self.subTest(change=change):
                lock = deepcopy(self.lock);change(lock)
                self.reject("invalid-lock", lambda: replay.validate_lock(lock))

    def test_native_inputs_cannot_escape_or_change_the_declared_closure(self):
        for observed in ({"outside:x": "0" * 64}, {"project:document.typ": "0" * 64}, {1: "0" * 64}):
            with self.subTest(observed=observed):
                with self.assertRaises(replay.ReplayError):
                    replay.require_observed(observed, self.lock["project_files"], self.lock["package_files"])

    def test_complete_package_inventory_requires_actual_manifest_and_licence(self):
        observed = self.lock["observed_inputs"]
        (self.cache / "preview/synthetic/1.0.0/LICENSE").unlink()
        self.reject("missing-package-identity", lambda: replay.package_records(self.cache, observed, replay.inventory(self.cache)))
        self.reject("unsupported-package", lambda: replay.package_records(self.cache, {"package-cache:local/a/1.0.0/a.typ": "0" * 64}, {}))

    def test_replay_rejects_changed_lock_bytes_before_compilation(self):
        (self.bundle / "lock.json").write_bytes((self.bundle / "lock.json").read_bytes() + b" ")
        output = self.area / "changed-lock"
        with patch.object(replay, "compile_isolated") as compile_call:
            self.reject("lock-mismatch", lambda: replay.replay(self.bundle, self.lock_digest, output))
        compile_call.assert_not_called()
        self.assertFalse(json.loads((output / "report.json").read_text())["byte_replay_qualified"])

    def test_source_asset_package_and_font_tampering_all_fail_before_compilation(self):
        for folder, name in (("project", "document.typ"), ("project", "asset.txt"),
                             ("packages", "preview/synthetic/1.0.0/lib.typ"), ("fonts", "One.otf")):
            with self.subTest(folder=folder, name=name):
                path = self.bundle / folder / name;original = path.read_bytes()
                path.write_bytes(original + b"tampered")
                self.reject("input-mismatch", lambda: self.replay_call(self.area / ("tamper-" + folder + "-" + Path(name).name)))
                path.write_bytes(original)

    def test_missing_or_undeclared_dependency_files_are_rejected(self):
        path = self.bundle / "packages/preview/synthetic/1.0.0/lib.typ"
        original = path.read_bytes();path.unlink()
        self.reject("input-mismatch", lambda: self.replay_call(self.area / "missing-package"))
        path.write_bytes(original)
        (self.bundle / "fonts/hidden-font.otf").write_bytes(b"Ambient fallback")
        self.reject("input-mismatch", lambda: self.replay_call(self.area / "extra-font"))

    def test_changed_compiler_is_rejected_without_invocation(self):
        self.tools["typst"].write_bytes(b"Changed compiler bytes")
        with patch.object(replay, "compile_isolated") as compile_call:
            with patch.object(replay.shutil, "which", side_effect=lambda name: str(self.tools[name])):
                self.reject("tool-mismatch", lambda: replay.replay(self.bundle, self.lock_digest, self.area / "tool-change", self.tools["typst"]))
        compile_call.assert_not_called()

    def test_changed_producer_or_environment_cannot_reuse_the_lock(self):
        self.lock["producer_sha256"]["scripts/replay_build.py"] = "0" * 64;self.save_lock()
        self.reject("producer-mismatch", lambda: self.replay_call(self.area / "producer-change"))
        self.lock["producer_sha256"] = replay.producer_identity()
        self.lock["environment"]["kernel"] = "different-kernel";self.save_lock()
        self.reject("environment-mismatch", lambda: self.replay_call(self.area / "environment-change"))

    def test_success_uses_two_distinct_fresh_copy_roots_and_keeps_limits_explicit(self):
        roots = []
        def compile_case(project, *args):
            roots.append(project)
            self.assertFalse((project / "_replay/document.pdf").exists())
            return self.fake_compile(project, *args)
        result = self.replay_call(self.area / "positive", compile_case)
        self.assertEqual(len(roots), 2)
        self.assertNotEqual(roots[0], roots[1])
        self.assertFalse((roots[0] / "document.typ").samefile(roots[1] / "document.typ"))
        self.assertTrue(result["comparison"]["bytes_equal"])
        self.assertTrue(result["byte_replay_qualified"])
        self.assertFalse(result["release_bundle_qualified"])
        self.assertFalse(result["complete_environment_image_locked"])

    def test_first_or_second_compile_failure_keeps_a_fresh_failed_receipt(self):
        for failing in (1, 2):
            calls = []
            def compile_case(*args):
                calls.append(1)
                if len(calls) == failing:
                    raise subprocess.TimeoutExpired(["synthetic compiler"], 60)
                return self.fake_compile(*args)
            output = self.area / ("failure-" + str(failing))
            with self.assertRaises(subprocess.TimeoutExpired):
                self.replay_call(output, compile_case)
            record = json.loads((output / "report.json").read_text())
            self.assertEqual(record["result"], "fail")
            self.assertFalse(record["byte_replay_qualified"])
            self.assertEqual(len(record["builds"]), failing - 1)

    def test_changed_input_during_compile_is_detected(self):
        def compile_case(project, *args):
            result = self.fake_compile(project, *args)
            path = project / "asset.txt";path.chmod(0o644);path.write_bytes(b"Changed during compile")
            return result
        self.reject("input-mismatch", lambda: self.replay_call(self.area / "source-race", compile_case))

    def test_changed_bundle_during_first_build_cannot_seed_the_second(self):
        def compile_case(*args):
            result = self.fake_compile(*args)
            (self.bundle / "fonts/One.otf").write_bytes(b"Changed original bundle")
            return result
        self.reject("input-mismatch", lambda: self.replay_call(self.area / "bundle-race", compile_case))

    def test_native_dependency_omission_or_unexpected_identity_fails(self):
        def omitted(*args):
            result = self.fake_compile(*args)
            result["native_inventory"]["inputs"] = result["native_inventory"]["inputs"][1:]
            return result
        self.reject("dependency-set-mismatch", lambda: self.replay_call(self.area / "omitted", omitted))
        def unexpected(*args):
            result = self.fake_compile(*args)
            result["native_inventory"]["inputs"].append({"path": "project:unlisted.typ", "sha256_observed_after_compile": "0" * 64})
            return result
        self.reject("undeclared-dependency", lambda: self.replay_call(self.area / "unexpected", unexpected))

    def test_equal_semantic_marker_cannot_rescue_different_pdf_bytes(self):
        first, second = self.area / "first.pdf", self.area / "second.pdf"
        first.write_bytes(b"Same visible text; metadata A")
        second.write_bytes(b"Same visible text; metadata B")
        error = self.reject("byte-mismatch", lambda: replay.compare_pdfs(first, second, replay.digest(first)))
        self.assertFalse(error.details["bytes_equal"])
        self.assertEqual(error.details["first_difference_offset"], len(first.read_bytes()) - 1)
        second.write_bytes(first.read_bytes())
        self.reject("expected-artifact-mismatch", lambda: replay.compare_pdfs(first, second, "0" * 64))

    def test_lock_replacement_after_read_cannot_change_the_trusted_parsed_snapshot(self):
        lock_path = self.bundle / "lock.json"
        replacement = deepcopy(self.lock)
        replacement["source"] = {"git_revision": "a" * 40, "git_tree": "b" * 40, "git_dirty": False}
        original_read = Path.read_bytes
        changed = []

        def replace_after_read(path):
            contents = original_read(path)
            if path == lock_path and not changed:
                changed.append(True)
                path.write_bytes(replay.canonical(replacement) + b"\n")
            return contents

        with patch.object(Path, "read_bytes", replace_after_read):
            result = self.replay_call(self.area / "lock-read-race")
        self.assertEqual(changed, [True])
        self.assertEqual(result["source"], self.lock["source"])
        self.assertEqual(result["lock_sha256"], self.lock_digest)
        self.assertEqual(json.loads(lock_path.read_text())["source"], replacement["source"])

    def test_recipe_replacement_after_parsing_cannot_bind_a_different_copied_recipe(self):
        recipe_path = self.root / "recipe.json"
        replacement = deepcopy(self.recipe)
        replacement["id"] = "replacement-after-parsing"
        original_bytes, original_text = Path.read_bytes, Path.read_text
        changed, compiled = [], []

        def mutate(path, contents):
            if path == recipe_path and not changed:
                changed.append(True)
                path.write_text(json.dumps(replacement))
            return contents

        def bytes_read(path):
            return mutate(path, original_bytes(path))

        def text_read(path, *args, **kwargs):
            return mutate(path, original_text(path, *args, **kwargs))

        def compiler(*args):
            compiled.append(True)
            return self.fake_compile(*args)

        with patch.object(Path, "read_bytes", bytes_read), patch.object(Path, "read_text", text_read):
            self.reject("input-mismatch", lambda: self.capture_call(self.area / "recipe-read-race", compiler))
        self.assertEqual(changed, [True])
        self.assertEqual(compiled, [])

    def test_capture_binds_complete_packages_fonts_and_preserves_no_replay_claim(self):
        output = self.area / "captured"
        result = self.capture_call(output)
        self.assertEqual(result["result"], "pass")
        self.assertFalse(result["two_build_replay_qualified"])
        lock = replay.validate_lock(json.loads((output / "lock.json").read_text()))
        self.assertEqual(lock["packages"][0]["license"], "MIT")
        self.assertEqual(set(lock["font_files"]), {"One.otf", "LICENSE"})
        self.assertEqual(lock["source"], {"git_revision": None, "git_tree": None, "git_dirty": None})

    def test_capture_rejects_wrong_compiler_version_before_native_build(self):
        records = deepcopy(self.tool_records);records["typst"]["version"] = "typst 0.14.0"
        output = self.area / "wrong-version"
        self.reject("compiler-version-mismatch", lambda: self.capture_call(output, tool_records=records))
        self.assertFalse((output / "lock.json").exists())

    def test_capture_detects_original_source_change_after_copy(self):
        def mutate(*args):
            result = self.fake_compile(*args)
            (self.root / "asset.txt").write_bytes(b"Changed original source")
            return result
        self.reject("input-mismatch", lambda: self.capture_call(self.area / "capture-race", mutate))

    def test_missing_network_backend_is_unsupported_without_online_fallback(self):
        with patch.object(replay.shutil, "which", return_value=None):
            self.reject("missing-tool", lambda: replay.resolve_tools())
        with patch.object(replay.shutil, "which", side_effect=lambda n: None if n == "unshare" else str(self.tools[n])):
            self.reject("network-isolation-unavailable", lambda: replay.resolve_tools(self.tools["typst"]))
        with patch.object(replay.sys, "platform", "darwin"):
            with self.assertRaises(replay.ReplayError) as error:
                with replay.network_control():
                    self.fail("Unsupported isolation cannot continue")
            self.assertEqual(error.exception.code, "network-isolation-unavailable")

    def test_compile_wrapper_keeps_failure_commands_and_rejects_receipt_reuse(self):
        project = self.area / "compile-project";project.mkdir()
        def fail(*args):
            args[-1].append({"command": ["synthetic compiler"], "exit_code": 1})
            raise replay.ReplayError("synthetic-failure", "Unit controlled failure")
        with patch.object(replay, "_compile_fresh", side_effect=fail):
            self.reject("synthetic-failure", lambda: replay.compile_isolated(project, self.cache, self.root / "fonts", self.recipe, self.tools))
        record = json.loads((project / "_replay/compile-receipt.json").read_text())
        self.assertEqual(record["result"], "fail")
        self.assertEqual(record["commands"][0]["exit_code"], 1)
        self.reject("stale-output", lambda: replay.compile_isolated(project, self.cache, self.root / "fonts", self.recipe, self.tools))

    def test_worker_rejects_same_namespace_external_interfaces_and_reachable_parent(self):
        path = self.area / "worker.json"
        spec = {"network": {"parent_namespace": "net:[1]", "loopback_port": 1234,
                             "parent_connection_succeeded": True},
                "compiler_argv": ["/synthetic/typst", "compile"], "compiler_environment": {"TZ": "UTC"},
                "network_report": str(self.area / "network.json")}
        path.write_text(json.dumps(spec))
        for control in (False, None, 1, "true"):
            with self.subTest(parent_control=control):
                spec["network"]["parent_connection_succeeded"] = control
                path.write_text(json.dumps(spec))
                with patch.object(replay.os, "execve") as execute:
                    self.reject("network-not-isolated", lambda: replay.worker(path))
                execute.assert_not_called()
        spec["network"]["parent_connection_succeeded"] = True
        path.write_text(json.dumps(spec))
        original_read = Path.read_text
        def proc_text(p, *args, **kwargs):
            return "  lo: 0\n" if str(p) == "/proc/net/dev" else original_read(p, *args, **kwargs)
        with patch.object(Path, "read_text", proc_text), patch.object(replay.os, "readlink", return_value="net:[1]"):
            self.reject("network-not-isolated", lambda: replay.worker(path))
        with patch.object(Path, "read_text", proc_text), patch.object(replay.os, "readlink", return_value="net:[2]"), \
             patch.object(replay.socket, "create_connection"):
            self.reject("network-not-isolated", lambda: replay.worker(path))
        def external(p, *args, **kwargs):
            return " lo: 0\n eth0: 0\n" if str(p) == "/proc/net/dev" else original_read(p, *args, **kwargs)
        with patch.object(Path, "read_text", external), patch.object(replay.os, "readlink", return_value="net:[2]"):
            self.reject("network-not-isolated", lambda: replay.worker(path))

    def test_worker_executes_only_after_positive_parent_and_negative_child_control(self):
        path = self.area / "worker.json"
        spec = {"network": {"parent_namespace": "net:[1]", "loopback_port": 1234,
                             "parent_connection_succeeded": True},
                "compiler_argv": ["/synthetic/typst", "compile"], "compiler_environment": {"TZ": "UTC"},
                "network_report": str(self.area / "network.json")}
        path.write_text(json.dumps(spec));original_read = Path.read_text
        def proc_text(p, *args, **kwargs):
            return " lo: 0\n" if str(p) == "/proc/net/dev" else original_read(p, *args, **kwargs)
        with patch.object(Path, "read_text", proc_text), patch.object(replay.os, "readlink", return_value="net:[2]"), \
             patch.object(replay.socket, "create_connection", side_effect=OSError(errno.ENETUNREACH, "Synthetic isolated network")), \
             patch.object(replay.os, "execve") as execute:
            replay.worker(path)
        execute.assert_called_once_with(spec["compiler_argv"][0], spec["compiler_argv"], spec["compiler_environment"])
        self.assertEqual(json.loads((self.area / "network.json").read_text())["connection_error"]["errno"], errno.ENETUNREACH)

    def test_cli_reports_failed_and_unsupported_outcomes_without_success(self):
        for error, expected in ((replay.ReplayError("lock-mismatch", "Controlled rejection"), 1),
                                (replay.ReplayError("network-isolation-unavailable", "Controlled unsupported host"), 2)):
            stderr, stdout = io.StringIO(), io.StringIO()
            with patch.object(replay, "replay", side_effect=error), redirect_stderr(stderr), redirect_stdout(stdout):
                code = replay.main(["replay", "--bundle", str(self.bundle), "--lock-sha256", self.lock_digest,
                                    "--output", str(self.area / "cli")])
            self.assertEqual(code, expected)
            self.assertNotEqual(json.loads(stderr.getvalue())["result"], "pass")
            self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
