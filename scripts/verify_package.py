#!/usr/bin/env python3
"""Packaging native checks through the existing canonical command runner.

The --recover-thumbnail command generates an unqualified recovery artifact.
Default verification requires an already committed thumbnail and never writes it.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parent.parent
CREATION_TIMESTAMP = "1794700800"
PPI = "150"
MAX_THUMBNAIL_BYTES = 3 * 1024 * 1024
MAX_RECOVERY_BASE64_BYTES = 512 * 1024
CASE_IDS = (
    "archive-init-first-build", "package-library-import", "relocated-project",
    "nested-asset-edit", "bibliography-override", "chapter-and-draft-profile",
    "missing-resources", "watch-edit-rebuild", "readme-example", "thumbnail",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_output(root, output):
    """Remove only this gate's package directory under the repository build tree."""
    root, output = Path(root).resolve(), Path(output).absolute()
    build = root / "build"
    if (output.name != "package" or output.is_symlink()
            or output.resolve() != output
            or not output.parent.resolve().is_relative_to(build)
            or output == build):
        raise ValueError("Package cleanup is confined to its own package directory under build/")
    if output.exists():
        if not output.is_dir():
            raise ValueError("Package output must be a directory")
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def _run(ctx, entry, command, name, **options):
    return ctx["run"](command, "package/" + name, entry["commands"], **options)


def _check(name, passed):
    return {"name": name, "passed": passed is True}


def _require(entry, checks):
    entry["checks"] = checks
    if not checks or not all(item["passed"] is True for item in checks):
        raise ValueError("Missing or failed package assertions")
    entry["result"] = "pass"


def _record(path, root):
    return {"path": str(path.relative_to(root)), "sha256": digest(path), "bytes": path.stat().st_size}


def _inspect_pdf(ctx, entry, pdf, prefix):
    root = ctx["ROOT"]
    if not pdf.is_file() or pdf.stat().st_size == 0:
        raise ValueError("Native compiler did not produce a nonempty PDF")
    _run(ctx, entry, ["qpdf", "--check", str(pdf)], prefix + "-qpdf.log")
    info = _run(ctx, entry, ["pdfinfo", str(pdf)], prefix + "-pdfinfo.log")
    match = re.search(r"^Pages:\s+([0-9]+)\s*$", info, re.MULTILINE)
    if match is None or int(match[1]) < 1:
        raise ValueError("PDF has no readable page count")
    text = _run(ctx, entry, ["pdftotext", "-layout", str(pdf), "-"], prefix + "-text.log")
    if not text.strip():
        raise ValueError("PDF has no extractable text")
    target = pdf.with_suffix(".txt")
    target.write_text(text, encoding="utf-8")
    return {"pdf": _record(pdf, root), "text": _record(target, root), "pages": int(match[1])}, text


def _compile(ctx, entry, source, project, cache, output, prefix, extra=()):
    output.unlink(missing_ok=True)
    output.with_suffix(".txt").unlink(missing_ok=True)
    _run(ctx, entry, [
        "typst", "compile", "--root", str(project), "--package-path", str(cache),
        "--ignore-system-fonts", "--creation-timestamp", CREATION_TIMESTAMP,
        *extra, str(source), str(output),
    ], prefix + "-compile.log")
    details, text = _inspect_pdf(ctx, entry, output, prefix)
    details["source"] = _record(source, ctx["ROOT"])
    return details, text


def _fonts(ctx, entry, pdf, prefix):
    value = _run(ctx, entry, ["pdffonts", str(pdf)], prefix + "-fonts.log")
    fonts = []
    for line in value.splitlines():
        match = re.fullmatch(r"(\S+)\s+.*?\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*", line)
        if match:
            fonts.append(dict(zip(("name", "embedded", "subset", "unicode_map"), match.groups())))
    return fonts


def _prepare(ctx, output, entry):
    root = ctx["ROOT"]
    helper = runpy.run_path(str(root / "scripts/package_template.py"), run_name="scripts.package_template")
    archive = output / "template.tar.gz"
    receipt = helper["build"](root, archive)
    second = output / "template-repeat.tar.gz"
    repeated = helper["build"](root, second)
    if receipt != repeated or archive.read_bytes() != second.read_bytes():
        raise ValueError("Local archive construction is not deterministic")
    receipt_path = output / "archive-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    cache = output / "packages"
    installed = helper["install"](archive, receipt, cache)
    entry["python_operations"] = [
        {"callable": "scripts.package_template.build", "archive": _record(archive, root)},
        {"callable": "scripts.package_template.build", "archive": _record(second, root)},
        {"callable": "scripts.package_template.install", "installed_path": str(installed.relative_to(root))},
    ]
    entry["archive_receipt"] = _record(receipt_path, root)
    entry["payload_files"] = len(receipt["files"])
    entry["payload_bytes"] = receipt["payload_bytes"]
    entry["archive_bytes"] = receipt["archive_bytes"]
    entry["ordinary_preview_dependencies"] = "Ambient online/provisioned package cache; no cold-start or offline guarantee"
    native = _run(ctx, entry, ["typst", "--version"], "typst-version.log").strip()
    if native.split()[:2] != ["typst", receipt["compiler"]]:
        raise ValueError("Packaging requires the compiler pinned by typst.toml")
    entry["compiler_version"] = native
    entry["compiler_executable_sha256"] = digest(Path(shutil.which("typst")))
    entry["implementation_sha256"] = {name: digest(root / name) for name in (
        "scripts/package_template.py", "scripts/verify_package.py", "scripts/verify.py",
    )}
    spec = "@local/" + receipt["name"] + ":" + receipt["version"]
    project = output / "author"
    _run(ctx, entry, ["typst", "init", "--package-path", str(cache), spec, str(project)], "init.log")
    paths = tuple(sorted(path.relative_to(project).as_posix() for path in project.rglob("*") if path.is_file()))
    if paths != tuple(sorted(helper["STARTER_PATHS"])) or any(path.is_symlink() for path in project.rglob("*")):
        raise ValueError("Initializer did not produce exactly the six declared author files")
    if any(digest(project / name) != receipt["files"]["template/" + name]["sha256"] for name in paths):
        raise ValueError("Initializer changed an authored file from the verified package")
    entry["starter_files"] = {name: _record(project / name, root) for name in paths}
    return project, cache, spec, receipt


def _copy(project, output, name):
    target = output / name
    shutil.copytree(project, target)
    return target


def _ppm_counts(path):
    data = path.read_bytes()
    position, tokens = 0, []
    while len(tokens) < 4:
        while position < len(data) and data[position] in b" \t\r\n":
            position += 1
        if position < len(data) and data[position] == ord("#"):
            position = data.index(b"\n", position) + 1
            continue
        start = position
        while position < len(data) and data[position] not in b" \t\r\n":
            position += 1
        tokens.append(data[start:position])
    if tokens[0] != b"P6" or tokens[3] != b"255":
        raise ValueError("Expected native eight-bit PPM raster")
    if data[position:position + 2] == b"\r\n":
        position += 2
    elif data[position:position + 1] in (b"\n", b" ", b"\r", b"\t"):
        position += 1
    else:
        raise ValueError("PPM raster separator is missing")
    width, height = int(tokens[1]), int(tokens[2])
    raster = data[position:]
    if width <= 0 or height <= 0 or len(raster) != width * height * 3:
        raise ValueError("PPM dimensions do not match native bytes")
    blue = red = 0
    for index in range(0, len(raster), 3):
        r, g, b = raster[index:index + 3]
        blue += b > 160 and r < 80 and g < 120
        red += r > 160 and g < 120 and b < 80
    return {"width": width, "height": height, "blue_pixels": blue, "red_pixels": red}


def _raster(ctx, entry, pdf, text, output, prefix):
    pages = [i + 1 for i, page in enumerate(text.split("\f")) if "SYNTHETIC NESTED RESOURCE" in " ".join(page.split()) and "STARTER BODY SENTINEL" in " ".join(page.split())]
    if len(pages) != 1:
        raise ValueError("Expected one controlled image-caption page")
    target = output / prefix
    _run(ctx, entry, ["pdftoppm", "-f", str(pages[0]), "-l", str(pages[0]), "-singlefile",
                     "-scale-to", "1000", str(pdf), str(target)], prefix + "-raster.log")
    ppm = target.with_suffix(".ppm")
    return {**_record(ppm, ctx["ROOT"]), "page": pages[0], **_ppm_counts(ppm)}


def _thumbnail(ctx, entry, project, cache, output):
    target = output / "rendered-thumbnail.png"
    target.unlink(missing_ok=True)
    _run(ctx, entry, [
        "typst", "compile", "--root", str(project), "--package-path", str(cache),
        "--ignore-system-fonts", "--creation-timestamp", CREATION_TIMESTAMP,
        "--format", "png", "--pages", "1", "--ppi", PPI,
        str(project / "main.typ"), str(target),
    ], "thumbnail-render.log")
    data = target.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("Thumbnail is not an actual native PNG")
    width, height = struct.unpack(">II", data[16:24])
    if min(width, height) <= 0 or max(width, height) < 1080 or len(data) > MAX_THUMBNAIL_BYTES:
        raise ValueError("Thumbnail dimensions or byte size violate the declared package rules")
    entry["native_thumbnail"] = {**_record(target, ctx["ROOT"]), "width": width, "height": height,
                                 "ppi": int(PPI), "creation_timestamp": CREATION_TIMESTAMP}
    return target


def verify(report, ctx):
    root = ctx["ROOT"]
    corpus = report.setdefault("packaging_corpus", {})
    corpus.update({
        "requirements": ["PKG-01", "PKG-02", "PKG-03"], "result": "fail",
        "scope": "Bounded local archive/install/starter and executable documentation checks",
        "expected_specimen_count": len(CASE_IDS), "specimens": [],
        "registry_submission_qualified": False, "offline_replay_qualified": False,
        "cold_start_qualified": False, "reviewer_safe_package_qualified": False,
    })
    ctx["write_report"](report)
    output = clean_output(root, ctx["OUTPUT"] / "package")
    helper = runpy.run_path(str(root / "scripts/package_template.py"), run_name="scripts.package_template")
    source_paths = (*helper["PAYLOAD_PATHS"], "scripts/package_template.py", "scripts/verify_package.py",
                    "scripts/verify.py", "tests/packaging/watch_probe.py", "thumbnail.png")
    before = {name: digest(root / name) if (root / name).is_file() else None for name in source_paths}
    corpus["source_sha256_before"] = before
    corpus["font_scope"] = {
        "system_fonts_disabled": True,
        "explicit_font_paths_environment_present": bool(os.environ.get("TYPST_FONT_PATHS")),
        "embedded_fonts_disabled_environment_present": bool(__import__("os").environ.get("TYPST_IGNORE_EMBEDDED_FONTS")),
        "source_font_bytes_qualified": False, "supported_scripts_qualified": False,
    }
    project = cache = spec = first_pdf = first_text = None
    for identifier in CASE_IDS:
        entry = {"id": identifier, "result": "fail", "commands": [], "errors": []}
        corpus["specimens"].append(entry)
        try:
            if identifier == "archive-init-first-build":
                project, cache, spec, receipt = _prepare(ctx, output, entry)
                first_pdf = output / "first.pdf"
                details, first_text = _compile(ctx, entry, project / "main.typ", project, cache, first_pdf, "first")
                entry["output"] = details
                fonts = _fonts(ctx, entry, first_pdf, "first")
                entry["observed_pdf_fonts"] = fonts
                entry["tool_versions"] = {}
                for name, flag in (("qpdf", "--version"), ("pdfinfo", "-v"), ("pdftotext", "-v"), ("pdffonts", "-v"), ("pdftoppm", "-v")):
                    version = _run(ctx, entry, [name, flag], name + "-version.log", combined=True).strip()
                    if not version:
                        raise ValueError("Native package tool did not report its version")
                    entry["tool_versions"][name] = {"version": version.splitlines()[0], "executable_sha256": digest(Path(shutil.which(name)))}
                checks = [
                    _check("Synthetic author document has its body and bibliography", "STARTER BODY SENTINEL" in first_text and "SYNTHETIC REFERENCE ORIGINAL" in first_text.upper()),
                    _check("All declared PDF fonts are embedded", bool(fonts) and all(item["embedded"] == "yes" for item in fonts)),
                    _check("Observed starter font family", bool(fonts) and all("LibertinusSerif" in item["name"] for item in fonts)),
                    _check("No font files in the audited package", not any(name.lower().endswith((".otf", ".ttf", ".woff", ".woff2", ".zip")) for name in receipt["files"])),
                ]
            elif identifier == "package-library-import":
                consumer = output / "library-consumer"
                consumer.mkdir()
                (consumer / "icon.svg").write_bytes((project / "assets/figures/example.svg").read_bytes())
                source = consumer / "main.typ"
                source.write_text('#import "' + spec + '": thesis-image\n#set page(width: 100mm, height: 100mm)\n#set text(font: "Libertinus Serif")\nPACKAGE IMPORT SUCCESS.\n#thesis-image(path("icon.svg"), width: 20mm, alt: "Synthetic square.")\n', encoding="utf-8")
                details, text = _compile(ctx, entry, source, consumer, cache, output / "library.pdf", "library")
                entry["output"] = details
                checks = [_check("Actual installed library import", "PACKAGE IMPORT SUCCESS" in text)]
            elif identifier == "relocated-project":
                consumer = _copy(project, output, "relocated-author")
                details, text = _compile(ctx, entry, consumer / "main.typ", consumer, cache, output / "relocated.pdf", "relocated")
                entry["output"] = details
                checks = [_check("Relocated author project preserves text", text == first_text)]
            elif identifier == "nested-asset-edit":
                before_pixels = _raster(ctx, entry, first_pdf, first_text, output, "asset-before")
                consumer = _copy(project, output, "asset-author")
                image = consumer / "assets/figures/example.svg"
                data = image.read_text(encoding="utf-8")
                if data.count("#0055cc") != 1:
                    raise ValueError("Controlled blue SVG token is missing or duplicated")
                image.write_text(data.replace("#0055cc", "#cc3300"), encoding="utf-8")
                details, text = _compile(ctx, entry, consumer / "main.typ", consumer, cache, output / "asset-edited.pdf", "asset-edited")
                after_pixels = _raster(ctx, entry, output / "asset-edited.pdf", text, output, "asset-after")
                entry.update({"output": details, "before": before_pixels, "after": after_pixels})
                checks = [
                    _check("Initial caller-owned image is blue", before_pixels["blue_pixels"] > 100 and before_pixels["red_pixels"] == 0),
                    _check("Edited nested image reaches actual pixels", after_pixels["red_pixels"] > 100 and after_pixels["blue_pixels"] == 0),
                ]
            elif identifier == "bibliography-override":
                consumer = _copy(project, output, "bibliography-author")
                main = consumer / "main.typ"
                main.write_text(main.read_text(encoding="utf-8").replace('path("references.bib")', 'path("replacement.bib")'), encoding="utf-8")
                replacement = (consumer / "references.bib").read_text(encoding="utf-8").replace("SYNTHETIC REFERENCE ORIGINAL", "SYNTHETIC REFERENCE REPLACED")
                (consumer / "replacement.bib").write_text(replacement, encoding="utf-8")
                details, text = _compile(ctx, entry, main, consumer, cache, output / "bibliography.pdf", "bibliography")
                entry["output"] = details
                checks = [_check("Caller-native bibliography override", "SYNTHETIC REFERENCE REPLACED" in text.upper() and "SYNTHETIC REFERENCE ORIGINAL" not in text.upper())]
            elif identifier == "chapter-and-draft-profile":
                consumer = _copy(project, output, "chapter-author")
                main = consumer / "main.typ"
                main.write_text(main.read_text(encoding="utf-8") + '\n#include "chapters/second.typ"\n', encoding="utf-8")
                (consumer / "chapters/second.typ").write_text("= An added chapter\n\nADDED CHAPTER SENTINEL.\n", encoding="utf-8")
                details, text = _compile(ctx, entry, main, consumer, cache, output / "draft.pdf", "draft", ["--input", "profile=draft"])
                entry["output"] = details
                checks = [_check("New author chapter with selected native draft input", "ADDED CHAPTER SENTINEL" in text)]
            elif identifier == "missing-resources":
                checks = []
                for name, missing in (("image", "assets/figures/example.svg"), ("bibliography", "references.bib")):
                    consumer = _copy(project, output, "missing-" + name)
                    (consumer / missing).unlink()
                    pdf = output / ("missing-" + name + ".pdf")
                    pdf.unlink(missing_ok=True)
                    diagnostics = _run(ctx, entry, [
                        "typst", "compile", "--root", str(consumer), "--package-path", str(cache),
                        "--ignore-system-fonts", "--creation-timestamp", CREATION_TIMESTAMP,
                        str(consumer / "main.typ"), str(pdf),
                    ], "missing-" + name + ".log", combined=True, expected_exit=1)
                    errors = re.findall(r"^error:.*$", diagnostics, re.MULTILINE)
                    checks.append(_check("Intended missing " + name + " rejects without stale PDF",
                                         len(errors) == 1 and "file not found" in errors[0].lower()
                                         and Path(missing).name in diagnostics and not pdf.exists()))
            elif identifier == "watch-edit-rebuild":
                consumer = _copy(project, output, "watch-author")
                pdf, native_log, native_report = (output / name for name in ("watch.pdf", "watch-native.log", "watch.json"))
                _run(ctx, entry, [
                    sys.executable, str(root / "tests/packaging/watch_probe.py"),
                    "--project", str(consumer), "--cache", str(cache), "--pdf", str(pdf),
                    "--log", str(native_log), "--report", str(native_report),
                ], "watch-probe.log")
                observed = json.loads(native_report.read_text(encoding="utf-8"))
                details, text = _inspect_pdf(ctx, entry, pdf, "watch-final")
                initial_pdf = pdf.with_name(pdf.stem + "-initial.pdf")
                initial_details, initial_text = _inspect_pdf(ctx, entry, initial_pdf, "watch-initial")
                entry["initial_output"] = initial_details
                entry.update({"output": details, "watch_receipt": _record(native_report, root), "watch_log": _record(native_log, root)})
                checks = [
                    _check("Native watch/edit/rebuild evidence", observed.get("result") == "pass" and not observed.get("errors") and observed.get("first", {}).get("pdf_sha256") != observed.get("second", {}).get("pdf_sha256")),
                    _check("Actual initial PDF precedes the edit", "STARTER BODY SENTINEL" in initial_text and "WATCH REBUILD SENTINEL" not in initial_text and observed.get("first", {}).get("pdf_sha256") == digest(initial_pdf)),
                    _check("Actual rebuilt PDF contains authored edit", "WATCH REBUILD SENTINEL" in text),
                    _check("Final watch PDF matches the native receipt", observed.get("second", {}).get("pdf_sha256") == digest(pdf)),
                ]
            elif identifier == "readme-example":
                details, text = _compile(ctx, entry, root / "README.typ", root, cache, output / "readme.pdf", "readme")
                entry["output"] = details
                checks = [_check("Executable repository README example", "README EXAMPLE SUCCESS" in text)]
            else:
                native = _thumbnail(ctx, entry, project, cache, output)
                committed = root / "thumbnail.png"
                checks = [_check("Committed thumbnail matches the actual initialized starter",
                                 committed.is_file() and committed.read_bytes() == native.read_bytes())]
                entry["committed_thumbnail_sha256"] = digest(committed) if committed.is_file() else None
            _require(entry, checks)
        except Exception as exc:
            entry["errors"].append(f"{type(exc).__name__}: {exc}")
        ctx["write_report"](report)
    corpus["source_sha256_after"] = {name: digest(root / name) if (root / name).is_file() else None for name in source_paths}
    corpus["source_unchanged"] = before == corpus["source_sha256_after"]
    corpus["passed_count"] = sum(entry["result"] == "pass" for entry in corpus["specimens"])
    corpus["assertion_count"] = sum(len(entry.get("checks", [])) for entry in corpus["specimens"])
    corpus["output_inventory"] = [_record(path, root) for path in sorted(output.iterdir()) if path.is_file()]
    if corpus["passed_count"] != len(CASE_IDS) or corpus["source_unchanged"] is not True:
        raise ctx["VerificationError"]("Packaging corpus failed or repository source changed")
    corpus["result"] = "pass"
    ctx["write_report"](report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover-thumbnail", action="store_true")
    args = parser.parse_args(argv)
    spec = importlib.util.spec_from_file_location("package_canonical_verifier", ROOT / "scripts/verify.py")
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.OUTPUT = ROOT / "build" / ("package-thumbnail-recovery" if args.recover_thumbnail else "package-focused")
    runner.OUTPUT.mkdir(parents=True, exist_ok=True)
    report = {"passed": False, "canonical_gate_pass": False,
              "started_at_utc": datetime.now(timezone.utc).isoformat(),
              "artifact_kind": "thumbnail-recovery" if args.recover_thumbnail else "focused-package-verification"}
    runner.write_report(report)
    try:
        if args.recover_thumbnail:
            entry = {"result": "unqualified", "commands": [], "errors": []}
            report["recovery"] = entry
            output = clean_output(ROOT, runner.OUTPUT / "package")
            project, cache, _identity, _receipt = _prepare(vars(runner), output, entry)
            target = _thumbnail(vars(runner), entry, project, cache, output)
            data = target.read_bytes()
            encoded = base64.b64encode(data).decode("ascii")
            if len(encoded) > MAX_RECOVERY_BASE64_BYTES:
                raise ValueError("Recovery image exceeds the bounded log payload")
            report["result"] = "generated-unqualified"
            report["canonical_gate_pass"] = False
            print("PACKAGE_THUMBNAIL_SHA256 " + digest(target))
            print("PACKAGE_THUMBNAIL_BYTES " + str(len(data)))
            print("BEGIN_TYPST_PACKAGE_THUMBNAIL_BASE64")
            for index in range(0, len(encoded), 76):
                print(encoded[index:index + 76])
            print("END_TYPST_PACKAGE_THUMBNAIL_BASE64")
        else:
            verify(report, vars(runner))
            report["passed"] = True
        return 0
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(report["error"], file=sys.stderr)
        return 1
    finally:
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        runner.write_report(report)


if __name__ == "__main__":
    raise SystemExit(main())
