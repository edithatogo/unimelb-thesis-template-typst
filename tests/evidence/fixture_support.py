"""Small committed source/evidence specimens; no simulated PDF is compiler proof."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess

from scripts import requirement_evidence as evidence

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 11, 15, 4, 0, tzinfo=timezone.utc)
NATIVE = "build/verification/report.json"
PROPERTIES = "build/property-tests.json"


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def git(root, *arguments):
    result = subprocess.run(["git", "--no-optional-locks", "-C", str(root), *arguments],
                            capture_output=True, text=True, check=True, timeout=60)
    return result.stdout.strip()


def make_fixture(root):
    """Create an isolated local Git repository and explicitly synthetic reports."""
    root = Path(root)
    root.mkdir(parents=True)
    shutil.copytree(ROOT / "contracts", root / "contracts")
    source_files = {".gitignore": "build/\n", "thesis.typ": "Synthetic thesis source\n",
                    "sample-chapter.typ": "Synthetic chapter source\n",
                    "typst.toml": '[tool.typst]\nversion = "0.15.1"\n',
                    "scripts/verify.py": "# Synthetic native producer identity\n",
                    "scripts/manage_terms.py": "# Synthetic measured term source\n",
                    "scripts/validate_template.py": "# Synthetic measured validation source\n",
                    "tests/test_properties.py": "# Synthetic measured property source\n"}
    for name, content in source_files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(root, "init", "-q")
    git(root, "add", "--all")
    git(root, "-c", "user.name=Synthetic Evidence Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "Synthetic unit source")
    revision, tree = git(root, "rev-parse", "HEAD"), git(root, "rev-parse", "HEAD^{tree}")
    build = root / "build/verification"
    build.mkdir(parents=True)
    log = build / "synthetic.log"
    log.write_text("SYNTHETIC COMMAND RECORD; no compiler was invoked.\n")
    command = {"command": ["synthetic-typst", "compile", "thesis.typ", "build/verification/thesis.pdf"],
               "exit_code": 0, "expected_exit_code": 0, "timed_out": False, "duration_seconds": 0.1,
               "timeout_seconds": 60, "log": "build/verification/synthetic.log", "log_sha256": evidence.digest(log),
               "environment_overrides": {"SOURCE_DATE_EPOCH": "0"}}
    documents = []
    for source in ("thesis.typ", "sample-chapter.typ"):
        stem = Path(source).stem
        pdf, text = build / (stem + ".pdf"), build / (stem + ".txt")
        pdf.write_bytes(b"SYNTHETIC NON-PDF ARTIFACT FOR HASH TESTS ONLY\n" + source.encode())
        text.write_text("Synthetic extracted-text specimen for " + source + "\n")
        documents.append({"source": source, "source_sha256": evidence.digest(root / source), "result": "pass",
                          "pages": 1, "bytes": pdf.stat().st_size,
                          "pdf": pdf.relative_to(root).as_posix(), "pdf_sha256": evidence.digest(pdf),
                          "text": text.relative_to(root).as_posix(), "text_sha256": evidence.digest(text)})
    native = {"schema_version": 1, "source_revision": revision, "source_dirty": False,
              "verifier_sha256": evidence.digest(root / "scripts/verify.py"),
              "typst_manifest_sha256": evidence.digest(root / "typst.toml"),
              "started_at_utc": "2026-11-15T03:00:00Z", "finished_at_utc": "2026-11-15T03:01:00Z",
              "passed": True, "compiler": "typst 0.15.1 (synthetic-unit-record)", "python_version": "3.15.1",
              "tool_versions": {name: "synthetic unit identity" for name in ("typst", "qpdf", "pdfinfo", "pdftotext")},
              "executables": {name: {"sha256": "0" * 64} for name in ("typst", "qpdf", "pdfinfo", "pdftotext")},
              "command_timeout_seconds": 60, "commands": [command], "documents": documents}
    adapters = json.loads((ROOT / "evidence/v1/adapters.json").read_text())
    native.update({name: {"result": "pass", "scope": "Synthetic unit observation; no native execution claim"}
                   for name in adapters["native_requirement_map"]})
    properties = {"schema_version": 1, "passed": True, "seed": 20261115, "cases_per_property": 64,
                  "tests_run": 10, "elapsed_seconds": 0.1, "generated_cases": {"test_synthetic_" + str(i): 64 for i in range(10)},
                  "source_sha256": {name: evidence.digest(root / name) for name in
                                    ("scripts/manage_terms.py", "scripts/validate_template.py", "tests/test_properties.py")},
                  "failure_threshold": 0, "failures": [], "errors": [], "skipped": []}
    write_json(root / NATIVE, native)
    write_json(root / PROPERTIES, properties)
    request = {"schema_version": 1, "repository": evidence.REPOSITORY, "revision": revision, "tree": tree,
               "run": {"not_before": "2026-11-15T02:59:00Z", "review_by": "2026-11-16T04:00:00Z"},
               "native": {"path": NATIVE, "sha256": evidence.digest(root / NATIVE), "schema_version": 1},
               "properties": {"path": PROPERTIES, "sha256": evidence.digest(root / PROPERTIES), "schema_version": 1},
               "sidecars": []}
    return deepcopy(request), native, properties
