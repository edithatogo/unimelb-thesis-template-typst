"""Exercise the real parallel Make target with controlled compiler processes.

The synthetic compiler checks build orchestration, not Typst or PDF semantics.
Each child waits for an explicit release, so both completion orders are tested
without relying on different compilation speeds.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = ("thesis.typ", "sample-chapter.typ")
PROFILES = ("default", "draft", "screen", "print")
TIMEOUT_SECONDS = 5

COMPILER = r'''import json
import os
from pathlib import Path
import sys
import time

source = sys.argv[-2]
root = Path.cwd()
started = root / f"started-{source}.json"
temporary = started.with_suffix(".tmp")
temporary.write_text(json.dumps({"argv": sys.argv[1:], "pid": os.getpid()}))
temporary.replace(started)
deadline = time.monotonic() + 5
while not (root / f"release-{source}").is_file():
    if time.monotonic() >= deadline:
        print(f"Synthetic compiler release timed out: {source}", file=sys.stderr)
        raise SystemExit(99)
    time.sleep(0.01)
status = json.loads((root / "exit-codes.json").read_text())[source]
(root / f"finished-{source}").write_text(str(status))
print(f"Synthetic compiler exit for {source}: {status}", flush=True)
raise SystemExit(status)
'''


class ParallelBuildTests(unittest.TestCase):
    def wait_until(self, predicate, description):
        deadline = time.monotonic() + TIMEOUT_SECONDS
        while not predicate():
            if time.monotonic() >= deadline:
                self.fail(f"Timed out waiting for {description}")
            time.sleep(0.01)

    @staticmethod
    def process_exists(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def run_build(self, profile, exit_codes, first_finished):
        make = shutil.which("make")
        self.assertIsNotNone(make, "GNU Make is required to test its build targets")
        with tempfile.TemporaryDirectory(prefix="typst parallel ") as temporary:
            root = Path(temporary)
            compiler = root / "compiler.py"
            compiler.write_text(COMPILER, encoding="utf-8")
            binary_directory = root / "bin"
            binary_directory.mkdir()
            wrapper = binary_directory / "typst"
            wrapper.write_text(
                f"#!/bin/sh\nexec {shlex.quote(sys.executable)} "
                f"{shlex.quote(str(compiler))} \"$@\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            (root / "exit-codes.json").write_text(
                json.dumps(exit_codes), encoding="utf-8"
            )
            for source in DOCUMENTS:
                (root / source).write_text("= Synthetic document\n", encoding="utf-8")
            environment = {
                **os.environ,
                "PATH": f"{binary_directory}{os.pathsep}{os.environ.get('PATH', '')}",
            }
            # Nested make must not inherit the outer verification target's flags.
            for variable in ("MAKEFLAGS", "MFLAGS", "MAKEOVERRIDES"):
                environment.pop(variable, None)
            log_path = root / "build.log"
            with log_path.open("w", encoding="utf-8") as log:
                process = subprocess.Popen(
                    [
                        make, "--no-print-directory", "-f", str(ROOT / "Makefile"),
                        "compile-parallel", f"PROFILE={profile}", "SHELL=/bin/sh",
                    ],
                    cwd=root,
                    env=environment,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    # Both children must start before either is released.
                    self.wait_until(
                        lambda: all(
                            (root / f"started-{source}.json").is_file()
                            for source in DOCUMENTS
                        ),
                        "both compiler children to start",
                    )
                    invocations = {
                        source: json.loads((root / f"started-{source}.json").read_text())
                        for source in DOCUMENTS
                    }
                    (root / f"release-{first_finished}").touch()
                    self.wait_until(
                        lambda: (root / f"finished-{first_finished}").is_file()
                        and not self.process_exists(invocations[first_finished]["pid"]),
                        "the first compiler child to exit",
                    )
                    # A failed first child must not let make abandon its sibling.
                    with self.assertRaises(
                        subprocess.TimeoutExpired,
                        msg="make exited while the second compiler was still blocked",
                    ):
                        process.wait(timeout=0.1)
                    second_finished = next(
                        source for source in DOCUMENTS if source != first_finished
                    )
                    (root / f"release-{second_finished}").touch()
                    status = process.wait(timeout=TIMEOUT_SECONDS)
                    for source in DOCUMENTS:
                        self.assertEqual(
                            (root / f"finished-{source}").read_text(),
                            str(exit_codes[source]),
                        )
                finally:
                    # A failing assertion must not leave synthetic children running.
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    process.wait(timeout=TIMEOUT_SECONDS)
            return status, log_path.read_text(encoding="utf-8"), invocations

    def assert_outcomes(self, exit_codes):
        for profile in PROFILES:
            for first_finished in DOCUMENTS:
                with self.subTest(profile=profile, first_finished=first_finished):
                    status, output, invocations = self.run_build(
                        profile, exit_codes, first_finished
                    )
                    for source in DOCUMENTS:
                        expected = ["compile", "--root", "."]
                        if profile != "default":
                            expected.extend(["--input", f"profile={profile}"])
                        expected.extend([source, str(Path(source).with_suffix(".pdf"))])
                        self.assertEqual(invocations[source]["argv"], expected)
                    if any(exit_codes.values()):
                        self.assertNotEqual(status, 0, output)
                        self.assertNotIn("Parallel compilation complete", output)
                    else:
                        self.assertEqual(status, 0, output)
                        self.assertIn("Parallel compilation complete", output)
                    for source, label in (
                        ("thesis.typ", "Thesis"),
                        ("sample-chapter.typ", "Sample chapter"),
                    ):
                        message = f"{label} compiled: {Path(source).with_suffix('.pdf')}"
                        if exit_codes[source]:
                            self.assertNotIn(message, output)
                        else:
                            self.assertIn(message, output)

    def test_successful_children_succeed_in_both_completion_orders(self):
        self.assert_outcomes({"thesis.typ": 0, "sample-chapter.typ": 0})

    def test_failed_thesis_fails_after_waiting_for_both_children(self):
        self.assert_outcomes({"thesis.typ": 7, "sample-chapter.typ": 0})

    def test_failed_sample_fails_after_waiting_for_both_children(self):
        self.assert_outcomes({"thesis.typ": 0, "sample-chapter.typ": 13})

    def test_both_failed_children_fail_in_both_completion_orders(self):
        self.assert_outcomes({"thesis.typ": 7, "sample-chapter.typ": 13})


if __name__ == "__main__":
    unittest.main()
