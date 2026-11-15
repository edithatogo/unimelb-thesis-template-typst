#!/usr/bin/env python3
"""Exercise one real watch/edit/rebuild in the canonical runner's process group."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

CREATION_TIMESTAMP = "1794700800"
INITIAL_SENTINEL = "STARTER BODY SENTINEL"
UPDATED_SENTINEL = "WATCH REBUILD SENTINEL"
PHASE_SECONDS = 20


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def completed_count(log):
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    return len(re.findall(r"compiled (?:successfully|with warnings) in ", text))


def await_completion(process, pdf, log, *, count, sentinel, records):
    deadline = time.monotonic() + PHASE_SECONDS
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Watch terminated before the required completed build")
        if completed_count(log) >= count and pdf.is_file() and pdf.stat().st_size:
            command = ["pdftotext", "-layout", str(pdf), "-"]
            native = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
            records.append({
                "command": command, "exit_code": native.returncode, "timeout_seconds": 5,
                "stdout_sha256": hashlib.sha256(native.stdout.encode()).hexdigest(),
                "stderr": native.stderr,
            })
            if native.returncode != 0 or sentinel not in " ".join(native.stdout.split()):
                raise RuntimeError("Completed watch output failed its native text assertion")
            return {"pdf_sha256": sha256(pdf), "completed_builds": completed_count(log),
                    "text_sha256": hashlib.sha256(native.stdout.encode()).hexdigest(), "text": native.stdout}
        time.sleep(0.1)
    raise RuntimeError("Watch did not complete within the bounded phase budget")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("project", "cache", "pdf", "log", "report"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args(argv)
    command = [
        "typst", "watch", "--root", str(args.project), "--package-path", str(args.cache),
        "--ignore-system-fonts", "--creation-timestamp", CREATION_TIMESTAMP,
        str(args.project / "main.typ"), str(args.pdf),
    ]
    report = {"result": "fail", "command": command, "phase_seconds": PHASE_SECONDS,
              "inherits_canonical_process_group": os.name == "posix",
              "process_scope": "Canonical POSIX group cleanup; otherwise the runner direct-process limit",
              "commands": [], "errors": []}
    args.pdf.unlink(missing_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    process = None
    started = time.monotonic()
    try:
        with args.log.open("w", encoding="utf-8") as stream:
            # Do not create a new session: the outer canonical watchdog owns us
            # and this compiler together if its unchanged 60-second budget expires.
            process = subprocess.Popen(command, stdout=stream, stderr=stream, stdin=subprocess.DEVNULL)
            first = await_completion(process, args.pdf, args.log, count=1,
                                     sentinel=INITIAL_SENTINEL, records=report["commands"])
            first_pdf = args.pdf.with_name(args.pdf.stem + "-initial.pdf")
            first_pdf.write_bytes(args.pdf.read_bytes())
            first["retained_pdf"] = str(first_pdf)
            report["first"] = first
            chapter = args.project / "chapters/introduction.typ"
            report["chapter_sha256_before"] = sha256(chapter)
            chapter.write_text(chapter.read_text(encoding="utf-8") + "\n" + UPDATED_SENTINEL + ".\n", encoding="utf-8")
            second = await_completion(process, args.pdf, args.log, count=first["completed_builds"] + 1,
                                      sentinel=UPDATED_SENTINEL, records=report["commands"])
            report["second"] = second
            report["chapter_sha256_after"] = sha256(chapter)
            if first["pdf_sha256"] == second["pdf_sha256"]:
                raise RuntimeError("Watch did not replace the initial PDF")
            report["result"] = "pass"
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        report["errors"].append(f"{type(exc).__name__}: {exc}")
    finally:
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            report["watch_exit_after_controlled_stop"] = process.returncode
        report["duration_seconds"] = time.monotonic() - started
        if args.log.is_file():
            report["watch_log_sha256"] = sha256(args.log)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "report": str(args.report)}))
    return 0 if report["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
