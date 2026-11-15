"""Native descriptor integrity controls using explicit synthetic artifacts.

These tests exercise real files, isolated Git fixtures and receipt consumers.
They do not run a compiler or claim rendered PDF/native-tool qualification.
"""
from copy import deepcopy
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest

from scripts import requirement_evidence as evidence

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = runpy.run_path(str(ROOT / "tests/evidence/fixture_support.py"))
DRIVER = runpy.run_path(str(ROOT / "tests/evidence/qualify.py"))
NOW, NATIVE, PROPERTIES = (FIXTURES[name] for name in ("NOW", "NATIVE", "PROPERTIES"))
write_json = FIXTURES["write_json"]


class NativeDescriptorEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        evidence.OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
        cls.container = tempfile.TemporaryDirectory(prefix="descriptor-base-", dir=evidence.OUTPUT_ROOT)
        cls.base = Path(cls.container.name) / "source"
        cls.fixture = FIXTURES["make_fixture"](cls.base)

    @classmethod
    def tearDownClass(cls):
        cls.container.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="descriptor-unit-", dir=evidence.OUTPUT_ROOT)
        self.parent = Path(self.temp.name)
        self.source = self.parent / "source"
        shutil.copytree(self.base, self.source)
        self.request, self.native, self.properties = deepcopy(self.fixture)
        self.output = self.parent / "receipt"
        self.receipt = self.output / "verification-receipt.json"

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        write_json(self.source / NATIVE, self.native)
        write_json(self.source / PROPERTIES, self.properties)
        self.request["native"]["sha256"] = evidence.digest(self.source / NATIVE)
        self.request["properties"]["sha256"] = evidence.digest(self.source / PROPERTIES)

    def produce(self):
        self.save()
        return evidence.produce(self.request, source_root=self.source, output=self.output, now=NOW)

    def verify(self, **options):
        values = {"source_root": self.source, "expected_revision": self.request["revision"],
                  "trusted_sha256": evidence.digest(self.receipt), "now": NOW,
                  "logs": self.parent / "consumer-probes"}
        values.update(options)
        return evidence.verify_receipt(self.receipt, **values)

    def reject(self, codes, call):
        codes = {codes} if isinstance(codes, str) else set(codes)
        with self.assertRaises(evidence.ReceiptError) as caught:
            call()
        self.assertIn(caught.exception.code, codes)

    def descriptor(self, name="supplement.json"):
        path = self.source / "build/verification/descriptors" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"SYNTHETIC DESCRIPTOR CONTENT; NOT NATIVE EVIDENCE\n" + name.encode())
        return {"path": path.relative_to(self.source).as_posix(), "sha256": evidence.digest(path)}

    def attach(self, location, descriptor):
        if location == "supplement":
            self.native["native_evidence_corpus"]["supplement"] = descriptor
        elif location == "dependency":
            self.native["native_evidence_corpus"]["specimens"] = [{"dependency_inventory": descriptor}]
        elif location == "color-stream":
            self.native["configuration_corpus"]["specimens"] = [{"color_streams": [descriptor]}]
        elif location == "package-inventory":
            self.native["packaging_corpus"]["output_inventory"] = [descriptor]
        elif location == "package-output":
            self.native["packaging_corpus"]["specimens"] = [{"output": {"pdf": descriptor}}]
        else:
            raise AssertionError("Unknown fixture location")

    def test_current_native_descriptor_locations_are_copied_and_consumed(self):
        descriptors = []
        for location in ("supplement", "dependency", "color-stream", "package-inventory", "package-output"):
            item = self.descriptor(location + ".bin")
            descriptors.append(item)
            self.attach(location, item)
        wrapper, sidecar = self.produce()
        artifacts = {item["original_path"]: item for item in sidecar["artifacts"]}
        for item in descriptors:
            with self.subTest(path=item["path"]):
                self.assertIn(item["path"], artifacts)
                self.assertEqual((self.output / artifacts[item["path"]]["path"]).read_bytes(),
                                 (self.source / item["path"]).read_bytes())
        self.assertEqual(wrapper["result"], "partial")
        self.assertTrue(self.verify()["integrity_verified"])
        self.assertFalse(sidecar["full_programme_qualified"])

    def test_missing_current_descriptor_files_reject_production(self):
        for location in ("supplement", "dependency", "color-stream", "package-inventory"):
            with self.subTest(location=location):
                self.native = deepcopy(self.fixture[1])
                item = self.descriptor(location + ".json")
                self.attach(location, item)
                (self.source / item["path"]).unlink()
                self.reject("missing-artifact", self.produce)

    def test_tampered_current_descriptor_files_reject_production(self):
        for location in ("supplement", "dependency", "color-stream", "package-inventory"):
            with self.subTest(location=location):
                self.native = deepcopy(self.fixture[1])
                item = self.descriptor(location + ".json")
                self.attach(location, item)
                (self.source / item["path"]).write_bytes(b"CHANGED DISPOSABLE INPUT")
                self.reject("artifact-tampered", self.produce)

    def test_missing_copied_descriptor_rejects_consumer(self):
        item = self.descriptor()
        self.attach("supplement", item)
        self.produce()
        copied = self.output / "artifacts" / item["path"]
        self.assertTrue(copied.is_file())
        copied.unlink()
        self.reject("missing-artifact", self.verify)

    def test_tampered_copied_descriptor_rejects_consumer(self):
        item = self.descriptor()
        self.attach("supplement", item)
        original = (self.source / item["path"]).read_bytes()
        self.produce()
        copied = self.output / "artifacts" / item["path"]
        self.assertTrue(copied.is_file())
        copied.write_bytes(b"CHANGED COPIED ARTIFACT")
        self.reject("artifact-tampered", self.verify)
        self.assertEqual((self.source / item["path"]).read_bytes(), original)

    def test_duplicate_identical_descriptors_share_one_bound_artifact(self):
        item = self.descriptor()
        self.attach("supplement", item)
        self.attach("dependency", dict(item))
        _, sidecar = self.produce()
        self.assertEqual(sum(x["original_path"] == item["path"] for x in sidecar["artifacts"]), 1)
        self.assertTrue(self.verify()["integrity_verified"])

    def test_conflicting_descriptor_digests_cannot_choose_a_winner(self):
        item = self.descriptor()
        self.attach("supplement", item)
        self.attach("dependency", dict(item, sha256="0" * 64))
        self.reject({"artifact-tampered", "conflicting-artifact"}, self.produce)

    def test_missing_or_nonstrings_in_descriptor_paths_reject(self):
        item = self.descriptor()
        for path in (None, 7, True, ["build", "specimen.json"]):
            with self.subTest(path=path):
                self.attach("supplement", dict(item, path=path))
                self.reject("missing-artifact-path", self.produce)
        self.attach("supplement", {"sha256": item["sha256"]})
        self.reject("missing-artifact-path", self.produce)

    def test_missing_and_malformed_descriptor_hashes_reject(self):
        item = self.descriptor()
        self.attach("supplement", {"path": item["path"]})
        self.reject("missing-artifact-digest", self.produce)
        for digest in (None, True, 7, "abc", "A" * 64):
            with self.subTest(digest=digest):
                self.attach("supplement", dict(item, sha256=digest))
                self.reject("invalid-digest", self.produce)

    def test_absolute_traversal_and_non_normal_paths_reject(self):
        item = self.descriptor()
        for path in (str(self.source / item["path"]), "../outside.json", "build/../outside.json",
                     "build//verification/specimen.json", "build/./verification/specimen.json",
                     "build\\verification\\specimen.json", "build/verification/specimen\n.json"):
            with self.subTest(path=path):
                self.attach("supplement", dict(item, path=path))
                self.reject("unsafe-path", self.produce)

    def test_leaf_and_parent_links_cannot_supply_descriptor_artifacts(self):
        item = self.descriptor()
        target = self.source / item["path"]
        leaf = target.with_name("alias.json")
        leaf.symlink_to(target)
        parent = self.source / "build/descriptor-link"
        parent.symlink_to(target.parent, target_is_directory=True)
        for path in (leaf, parent / target.name):
            with self.subTest(path=path):
                self.attach("supplement", dict(item, path=path.relative_to(self.source).as_posix()))
                self.reject("unsafe-path", self.produce)

    def test_tracked_source_descriptor_is_checked_without_copying_as_output(self):
        item = {"path": "thesis.typ", "sha256": evidence.digest(self.source / "thesis.typ")}
        self.attach("package-inventory", item)
        _, sidecar = self.produce()
        self.assertFalse(any(x["original_path"] == "thesis.typ" for x in sidecar["artifacts"]))
        self.assertTrue(self.verify()["integrity_verified"])
        self.attach("package-inventory", dict(item, sha256="0" * 64))
        self.reject("source-evidence-mismatch", self.produce)
        self.attach("package-inventory", dict(item, path="unregistered-source.typ"))
        self.reject("source-evidence-mismatch", self.produce)

    def test_tool_observations_and_user_maps_are_not_artifact_descriptors(self):
        self.native["executables"]["typst"] = {"path": "/unavailable/observed-tool", "sha256": "0" * 64}
        excluded = {"path": "build/unavailable-user-input.json", "sha256": "not-an-artifact-digest"}
        for name in ("inputs", "metadata", "normalized_configuration"):
            self.native[name] = deepcopy(excluded)
            self.native["packaging_corpus"][name] = deepcopy(excluded)
        _, sidecar = self.produce()
        self.assertFalse(any(x["original_path"] == excluded["path"] for x in sidecar["artifacts"]))
        self.assertTrue(self.verify()["integrity_verified"])

    def test_non_file_path_arrays_remain_data_observations(self):
        self.native["blind_corpus"]["residual_observations"] = [
            {"path": ["metadata", "author"], "status": "synthetic-path-observation"}]
        wrapper, _ = self.produce()
        self.assertEqual(wrapper["result"], "partial")
        self.assertTrue(self.verify()["integrity_verified"])

    def test_producer_preflight_preserves_descriptor_inside_its_output(self):
        self.output = self.source / "build/protected-receipt"
        self.receipt = self.output / "verification-receipt.json"
        self.output.mkdir(parents=True)
        original = b"PRESERVE THIS DECLARED DISPOSABLE INPUT"
        self.receipt.write_bytes(original)
        item = {"path": self.receipt.relative_to(self.source).as_posix(), "sha256": evidence.digest(self.receipt)}
        self.attach("supplement", item)
        self.reject("unsafe-output", self.produce)
        self.assertEqual(self.receipt.read_bytes(), original)
        self.assertFalse((self.output / "requirement-status.json").exists())

    def test_driver_preflight_preserves_output_and_identity_probe_inputs(self):
        for name in ("qualification.json", "identity-probes/revision.log"):
            with self.subTest(name=name):
                self.native = deepcopy(self.fixture[1])
                output = self.source / "build" / ("driver-" + str(len(name)))
                target = output / name
                target.parent.mkdir(parents=True)
                original = b"PRESERVE DECLARED DRIVER INPUT " + name.encode()
                target.write_bytes(original)
                self.attach("supplement", {"path": target.relative_to(self.source).as_posix(),
                                           "sha256": evidence.digest(target)})
                self.save()
                self.reject("unsafe-output", lambda: DRIVER["qualify"](
                    self.source, output, self.request["run"]["not_before"], self.request["run"]["review_by"]))
                self.assertEqual(target.read_bytes(), original)
                if name != "qualification.json":
                    self.assertFalse((output / "qualification.json").exists())

    def test_consumer_probe_directory_cannot_replace_copied_descriptor(self):
        item = self.descriptor("revision.log")
        self.attach("supplement", item)
        self.produce()
        copied = self.output / "artifacts" / item["path"]
        self.assertTrue(copied.is_file())
        original = copied.read_bytes()
        self.reject("unsafe-output", lambda: self.verify(logs=copied.parent))
        self.assertEqual(copied.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
