"""Exercise verifier subprocess evidence and bounded POSIX descendant cleanup."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("watchdog_verifier", ROOT / "scripts" / "verify.py")
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)
LINUX_PROCESS_STATE = (
    sys.platform == "linux" and Path("/proc/self/stat").is_file()
    and hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal")
)


def process_state(pid):
    """Return Linux state and start ticks, or None after the process disappears."""
    try:
        raw = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    fields = raw[raw.rfind(")") + 2:].split()
    return {"state": fields[0], "start_ticks": fields[19]}


class VerifierProcessTests(unittest.TestCase):
    def setUp(self):
        self.output = ROOT / "build" / "verifier-watchdog" / self._testMethodName
        self.output.mkdir(parents=True, exist_ok=True)
        self.scratch = tempfile.TemporaryDirectory(prefix="child-", dir=self.output)
        self.child_file = Path(self.scratch.name) / "child.json"
        self.commands = []
        self.child_observations = []
        self.settings = patch.multiple(
            VERIFY, ROOT=ROOT, OUTPUT=self.output,
            TIMEOUT_SECONDS=1, CLEANUP_TIMEOUT_SECONDS=5,
        )
        self.settings.start()

    def tearDown(self):
        try:
            if self.child_file.is_file():
                child = json.loads(self.child_file.read_text(encoding="utf-8"))
                try:
                    descriptor = os.pidfd_open(child["pid"])
                except ProcessLookupError:
                    descriptor = None
                try:
                    current = process_state(child["pid"])
                    self.child_observations.append({"child": child, "before_cleanup": current})
                    # A pidfd binds signalling to the opened process, never a reused PID.
                    if descriptor is not None and current:
                        if current["start_ticks"] == child["start_ticks"] and current["state"] not in {"Z", "X"}:
                            try:
                                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                finally:
                    if descriptor is not None:
                        os.close(descriptor)
            (self.output / "observations.json").write_text(
                json.dumps({
                    "scope": "verifier-process-observations",
                    "test_method": self._testMethodName,
                    "commands": self.commands,
                    "children": self.child_observations,
                    "note": "The unittest result determines pass/fail; cleanup is not a passing assertion.",
                }, indent=2) + "\n",
                encoding="utf-8",
            )
        finally:
            self.settings.stop()
            self.scratch.cleanup()

    def run_python(self, code, name, **kwargs):
        return VERIFY.run(
            [sys.executable, "-c", code], name, self.commands, **kwargs,
        )

    def assert_evidence(self, record, *, stdout, stderr, exit_code):
        self.assertEqual(record["exit_code"], exit_code)
        self.assertEqual(record["stdout_sha256"], hashlib.sha256(stdout.encode()).hexdigest())
        self.assertEqual(record["stderr_sha256"], hashlib.sha256(stderr.encode()).hexdigest())
        log = ROOT / record["log"]
        self.assertTrue(log.is_file())
        self.assertEqual(record["log_sha256"], hashlib.sha256(log.read_bytes()).hexdigest())
        self.assertIn(stdout, log.read_text(encoding="utf-8"))
        self.assertIn(stderr, log.read_text(encoding="utf-8"))

    def test_success_and_expected_nonzero_retain_output(self):
        out = self.run_python(
            "import os,sys; print('ready:'+os.environ['SOURCE_DATE_EPOCH']); "
            "print('notice',file=sys.stderr)",
            "success.log",
        )
        self.assertEqual(out, "ready:0\n")
        self.assert_evidence(self.commands[-1], stdout="ready:0\n", stderr="notice\n", exit_code=0)
        self.assertFalse(self.commands[-1]["timed_out"])
        result = self.run_python(
            "import sys; print('rejected'); print('expected diagnostic',file=sys.stderr); sys.exit(7)",
            "expected-nonzero.log", expected_exit=7, combined=True,
        )
        self.assertEqual(result, "rejected\nexpected diagnostic\n")
        self.assert_evidence(
            self.commands[-1], stdout="rejected\n", stderr="expected diagnostic\n", exit_code=7,
        )
        self.assertFalse(self.commands[-1]["timed_out"])

    def test_unexpected_nonzero_fails_with_diagnostics(self):
        with self.assertRaisesRegex(VERIFY.VerificationError, "exit 3 != expected 0"):
            self.run_python(
                "import sys; print('partial output'); print('broken input',file=sys.stderr); sys.exit(3)",
                "unexpected-nonzero.log",
            )
        self.assertEqual(len(self.commands), 1)
        self.assert_evidence(
            self.commands[0], stdout="partial output\n", stderr="broken input\n", exit_code=3,
        )
        self.assertFalse(self.commands[0]["timed_out"])

    def test_missing_executable_fails_and_retains_attempt(self):
        missing = str(Path(self.scratch.name) / "absent-executable")
        with self.assertRaisesRegex(VERIFY.VerificationError, "could not start"):
            VERIFY.run([missing], "missing.log", self.commands)
        self.assertEqual(len(self.commands), 1)
        self.assert_evidence(self.commands[0], stdout="", stderr="", exit_code=None)
        self.assertFalse(self.commands[0]["timed_out"])
        self.assertIn("could not start", self.commands[0]["error"])

    def exercise_descendant_timeout(self, *, parent_exits):
        child_code = (
            "import json,os,sys,time\n"
            "from pathlib import Path\n"
            "raw=Path('/proc/self/stat').read_text()\n"
            "fields=raw[raw.rfind(')')+2:].split()\n"
            "Path(sys.argv[1]).write_text(json.dumps({'pid':os.getpid(),'start_ticks':fields[19]}))\n"
            "print('child-ready',flush=True)\n"
            "time.sleep(30)\n"
        )
        parent_code = (
            "import subprocess,sys,time\n"
            "subprocess.Popen([sys.executable,'-c',sys.argv[1],sys.argv[2]])\n"
            "print('parent-ready',flush=True)\n"
            "print('parent-diagnostic',file=sys.stderr,flush=True)\n"
            + ("sys.exit(0)\n" if parent_exits else "time.sleep(30)\n")
        )
        started = time.monotonic()
        with self.assertRaisesRegex(VERIFY.VerificationError, "exceeded its 1s time budget"):
            VERIFY.run(
                [sys.executable, "-c", parent_code, child_code, str(self.child_file)],
                "timeout.log", self.commands,
            )
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 8, "The command exceeded its 1s + 5s cleanup budget and 2s test slack")
        self.assertTrue(self.child_file.is_file(), "The child must actually start before the timeout")
        child = json.loads(self.child_file.read_text(encoding="utf-8"))
        current = process_state(child["pid"])
        deadline = time.monotonic() + 1
        while (current and current["start_ticks"] == child["start_ticks"]
               and current["state"] not in {"Z", "X"} and time.monotonic() < deadline):
            time.sleep(0.01)
            current = process_state(child["pid"])
        self.child_observations.append({
            "child": child, "after_command": current, "elapsed_seconds": elapsed,
        })
        self.assertTrue(
            current is None or current["start_ticks"] != child["start_ticks"] or current["state"] in {"Z", "X"},
            "A descendant survived the verifier timeout",
        )
        self.assertEqual(len(self.commands), 1)
        record = self.commands[0]
        self.assertTrue(record["timed_out"])
        self.assertEqual(record["process_isolation"], "posix-session")
        self.assertEqual(record["cleanup_timeout_seconds"], 5)
        if parent_exits:
            self.assertEqual(record["exit_code"], 0, "The exited parent must not hide its live pipe holder")
        else:
            self.assertEqual(record["exit_code"], -signal.SIGKILL)
        log = (ROOT / record["log"]).read_text(encoding="utf-8")
        self.assertIn("parent-ready", log)
        self.assertIn("child-ready", log)
        self.assertIn("parent-diagnostic", log)
        self.assertIn("Timed out: True", log)
        expected_stdout = ("parent-ready\nchild-ready\n", "child-ready\nparent-ready\n")
        self.assertIn(record["stdout_sha256"], {hashlib.sha256(value.encode()).hexdigest() for value in expected_stdout})
        self.assertEqual(record["stderr_sha256"], hashlib.sha256(b"parent-diagnostic\n").hexdigest())
        self.assertEqual(record["log_sha256"], hashlib.sha256((ROOT / record["log"]).read_bytes()).hexdigest())

    @unittest.skipUnless(LINUX_PROCESS_STATE, "Requires Linux /proc and pidfds to verify and clean up actual descendants")
    def test_running_parent_and_child_are_stopped(self):
        self.exercise_descendant_timeout(parent_exits=False)

    @unittest.skipUnless(LINUX_PROCESS_STATE, "Requires Linux /proc and pidfds to verify and clean up actual descendants")
    def test_exited_parent_does_not_hide_child_holding_pipes(self):
        self.exercise_descendant_timeout(parent_exits=True)


if __name__ == "__main__":
    unittest.main()
