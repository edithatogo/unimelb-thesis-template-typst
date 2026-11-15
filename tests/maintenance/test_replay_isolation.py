"""Namespace launcher/identity contracts; mocked launches are not native proof."""
from contextlib import contextmanager
from copy import deepcopy
import errno
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import replay_build as replay
from tests.maintenance import test_replay_build as fixtures


class ReplayIsolationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="isolation-unit-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.isolation = {"backend": "privileged-network", "uid": 1001, "gid": 1001}
        self.privileges = {"uid": [1001] * 4, "gid": [1001] * 4, "groups": [],
                           "capabilities": {"CapEff": 0, "CapPrm": 0, "CapAmb": 0}, "no_new_privs": 1}

    def test_default_launcher_never_invokes_privileged_setup(self):
        command, isolation = replay.namespace_command({"unshare": Path("/usr/bin/unshare")}, self.root / "invocation.json")
        self.assertEqual(isolation, {"backend": "user-network"})
        self.assertEqual(command[0], Path("/usr/bin/unshare"))
        self.assertIn("--user", command)
        self.assertNotIn("sudo", " ".join(str(x) for x in command))

    def test_explicit_launcher_drops_identity_before_any_project_code(self):
        tools = {name: Path("/usr/bin") / name for name in ("sudo", "unshare", "setpriv")}
        with patch.object(replay.os, "getuid", return_value=1001), patch.object(replay.os, "geteuid", return_value=1001), \
             patch.object(replay.os, "getgid", return_value=1001), patch.object(replay.os, "getegid", return_value=1001):
            command, isolation = replay.namespace_command(tools, self.root / "invocation.json")
        self.assertEqual(isolation, self.isolation)
        self.assertEqual(command[:5], [tools["sudo"], "--non-interactive", "--", tools["unshare"], "--net"])
        self.assertLess(command.index("--setuid"), command.index(tools["setpriv"]))
        self.assertLess(command.index("--setgid"), command.index(tools["setpriv"]))
        self.assertLess(command.index("--no-new-privs"), command.index(replay.sys.executable))
        self.assertEqual(command[command.index("--setuid") + 1], "1001")
        self.assertEqual(command[command.index("--setgid") + 1], "1001")
        self.assertNotIn("--user", command)

    def test_privileged_launcher_rejects_root_and_mismatched_effective_ids(self):
        tools = {name: Path("/usr/bin") / name for name in ("sudo", "unshare", "setpriv")}
        for uid, gid, euid, egid in ((0, 1001, 0, 1001), (1001, 0, 1001, 0),
                                     (1001, 1001, 0, 1001), (1001, 1001, 1001, 0)):
            with self.subTest(ids=(uid, gid, euid, egid)), \
                 patch.object(replay.os, "getuid", return_value=uid), patch.object(replay.os, "getgid", return_value=gid), \
                 patch.object(replay.os, "geteuid", return_value=euid), patch.object(replay.os, "getegid", return_value=egid), \
                 self.assertRaises(replay.ReplayError) as caught:
                replay.namespace_command(tools, self.root / "invocation.json")
            self.assertEqual(caught.exception.code, "privileges-not-dropped")

    def test_privilege_guard_requires_all_saved_ids_groups_caps_and_no_new_privs(self):
        replay.check_privilege_drop(self.isolation, self.privileges)
        changes = [("uid", [1001, 1001, 0, 1001]), ("gid", [1001, 0, 1001, 1001]),
                   ("groups", [1001]), ("no_new_privs", 0), ("capabilities", {})]
        for cap in self.privileges["capabilities"]:
            caps = self.privileges["capabilities"].copy(); caps[cap] = 1
            changes.append(("capabilities", caps))
        for key, value in changes:
            observed = deepcopy(self.privileges); observed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(replay.ReplayError):
                replay.check_privilege_drop(self.isolation, observed)
        for key, value in (("uid", True), ("uid", 0), ("gid", -1), ("gid", "1001")):
            selection = self.isolation.copy(); selection[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(replay.ReplayError):
                replay.check_privilege_drop(selection, self.privileges)

    def test_privilege_observation_parses_the_actual_proc_field_shapes(self):
        status = "Uid:\t1001\t1001\t1001\t1001\nGid:\t1001\t1001\t1001\t1001\nGroups:\t\nCapEff:\t00000000\nCapPrm:\t00000000\nCapAmb:\t00000000\nNoNewPrivs:\t1\n"
        with patch.object(Path, "read_text", return_value=status):
            self.assertEqual(replay.privilege_observation(), self.privileges)
        with patch.object(Path, "read_text", return_value=status.replace("00000000", "invalid")), self.assertRaises(ValueError):
            replay.privilege_observation()

    def test_privileged_worker_cannot_execute_without_observed_drop(self):
        spec = {"isolation": self.isolation, "network": {"parent_connection_succeeded": True}}
        path = self.root / "spec.json"; path.write_text(json.dumps(spec))
        bad = deepcopy(self.privileges); bad["uid"] = [0] * 4
        with patch.object(replay, "privilege_observation", return_value=bad), patch.object(replay.os, "execve") as execute, \
             patch.object(replay.socket, "create_connection") as connection, self.assertRaises(replay.ReplayError):
            replay.worker(path)
        execute.assert_not_called(); connection.assert_not_called()
        spec["isolation"]["backend"] = "online-fallback"; path.write_text(json.dumps(spec))
        with self.assertRaises(replay.ReplayError): replay.worker(path)

    def test_privileged_worker_retains_drop_proof_and_minimal_compiler_environment(self):
        spec = {"isolation": self.isolation, "network": {"parent_namespace": "net:[1]", "parent_connection_succeeded": True, "loopback_port": 12345},
                "supervisor_pid": 500,
                "compiler_argv": ["/synthetic/typst", "compile"], "compiler_environment": {"TZ": "UTC"},
                "network_report": str(self.root / "network.json")}
        path = self.root / "spec.json"; path.write_text(json.dumps(spec)); original_read = Path.read_text
        def read(source, *args, **kwargs):
            return " lo: 0\n" if str(source) == "/proc/net/dev" else original_read(source, *args, **kwargs)
        with patch.object(replay, "privilege_observation", return_value=self.privileges), patch.object(Path, "read_text", read), \
             patch.object(replay, "process_control", return_value={"supervisor_pid": 500, "launcher_pid": 501, "process_group": 501, "session": 501}), \
             patch.object(replay.os, "readlink", return_value="net:[2]"), \
             patch.object(replay.socket, "create_connection", side_effect=OSError(errno.ENETUNREACH, "explicit unit mock")), \
             patch.object(replay.os, "execve") as execute:
            replay.worker(path)
        proof = json.loads((self.root / "network.json").read_text())
        self.assertEqual(proof["privilege_observation"], self.privileges)
        self.assertEqual(proof["isolation"], self.isolation)
        execute.assert_called_once_with(spec["compiler_argv"][0], spec["compiler_argv"], spec["compiler_environment"])

    def test_privileged_setup_rejects_user_owned_or_writable_system_executables(self):
        for uid, mode in ((1001, 0o100755), (0, 0o100775), (0, 0o100757)):
            with self.subTest(uid=uid, mode=mode), patch.object(replay.shutil, "which", side_effect=lambda name: "/usr/bin/" + name), \
                 patch.object(Path, "is_file", return_value=True), patch.object(Path, "stat", return_value=SimpleNamespace(st_uid=uid, st_mode=mode)), \
                 self.assertRaises(replay.ReplayError) as caught:
                replay.resolve_tools(isolation="privileged-network")
            self.assertEqual(caught.exception.code, "unsafe-namespace-tool")
        with patch.object(replay.shutil, "which", side_effect=lambda name: "/usr/bin/" + name), \
             patch.object(Path, "is_file", return_value=True), patch.object(Path, "stat", return_value=SimpleNamespace(st_uid=0, st_mode=0o100755)):
            tools = replay.resolve_tools(isolation="privileged-network")
        self.assertEqual(tools["sudo"], Path("/usr/bin/sudo"))
        self.assertEqual(tools["setpriv"], Path("/usr/bin/setpriv"))
        with self.assertRaises(replay.ReplayError): replay.resolve_tools(isolation="automatic-online")

    def test_backend_is_locked_and_must_be_explicitly_selected_for_replay(self):
        case = fixtures.ReplayBuildTests(); case.setUp(); self.addCleanup(case.tearDown)
        with self.assertRaises(replay.ReplayError) as caught:
            replay.replay(case.bundle, case.lock_digest, self.root / "wrong-backend", isolation="privileged-network")
        self.assertEqual(caught.exception.code, "isolation-mismatch")
        bad = deepcopy(case.lock); bad["environment"]["network_isolation_backend"] = "automatic-online"
        with self.assertRaises(replay.ReplayError): replay.validate_lock(bad)
        bad["environment"]["network_isolation_backend"] = "privileged-network"
        with self.assertRaises(replay.ReplayError): replay.validate_lock(bad)

    def test_worker_must_stay_in_the_actual_launcher_session_and_group(self):
        valid = {"supervisor_pid": 100, "launcher_pid": 200, "process_group": 200, "session": 200}
        replay.check_process_control(valid, 100)
        for key, value in (("supervisor_pid", 99), ("launcher_pid", True), ("process_group", 300), ("session", 300)):
            bad = valid.copy(); bad[key] = value
            with self.subTest(key=key), self.assertRaises(replay.ReplayError): replay.check_process_control(bad, 100)
        with patch.object(replay.os, "getpid", return_value=300), patch.object(replay.os, "getpgrp", return_value=200), \
             patch.object(replay.os, "getsid", return_value=200), \
             patch.object(Path, "read_text", side_effect=["300 (worker) S 200 200 200", "200 (launcher) S 100 200 200"]):
            self.assertEqual(replay.process_control(100), valid)
        with patch.object(replay.os, "getpid", return_value=300), \
             patch.object(Path, "read_text", return_value="300 (orphan) S 1 300 300"), self.assertRaises(replay.ReplayError):
            replay.process_control(100)

    def test_observed_uid_map_failure_is_unsupported_before_worker_or_compiler(self):
        project = self.root / "project"; output = project / "_replay"; output.mkdir(parents=True)
        class FailedLauncher:
            def __init__(self, root): self.output = output
            def run(self, command, log, records, **kwargs):
                (output / log).write_text("unshare: write failed /proc/self/uid_map: Operation not permitted\n")
                records.append({"command": [str(x) for x in command], "exit_code": 1, "unit_mock": True})
                raise RuntimeError("observed launcher rejection, reproduced with a mocked process")
        @contextmanager
        def control(): yield {"parent_namespace": "net:[1]", "parent_connection_succeeded": True, "loopback_port": 1234}
        recipe = {"creation_timestamp": 42, "cli_inputs": {}, "entrypoint": "document.typ"}
        with patch.object(replay, "Runner", FailedLauncher), patch.object(replay, "network_control", control), self.assertRaises(replay.ReplayError) as caught:
            replay._compile_fresh(project, self.root / "cache", self.root / "fonts", recipe,
                                  {"typst": Path("/synthetic/typst"), "unshare": Path("/usr/bin/unshare")}, [])
        self.assertEqual(caught.exception.code, "network-isolation-unavailable")
        self.assertFalse((output / "network.json").exists())
        self.assertFalse((output / "document.pdf").exists())


if __name__ == "__main__":
    unittest.main()
