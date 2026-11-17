#!/usr/bin/env python3
"""Project reviewed, discrete *literal-text* thesis material before rendering.

This is a bounded source boundary, not a general PDF redactor. In particular,
it cannot anonymize arbitrary prose, copy embedded publications, or certify
rights/accessible PDF output. Its manifest stays private. No network is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile


class ProjectionError(ValueError):
    """A stable, privacy-safe validation failure (no user text in errors)."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


TARGETS = frozenset({"examination", "deposit-public"})
VISIBILITIES = frozenset({"public", "restricted", "unresolved"})
FIELDS = frozenset({"id", "source", "visibility", "kind", "sha256"})
OMISSION = "Rights-restricted material omitted from this public version."
MAX_ITEM_BYTES = 2 * 1024 * 1024


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProjectionError("duplicate-manifest-key")
        result[key] = value
    return result


def _validated_items(manifest: Path):
    try:
        raw = manifest.read_bytes()
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs_unique)
    except ProjectionError:
        raise
    except (OSError, ValueError, UnicodeError) as exc:
        raise ProjectionError("invalid-manifest") from exc
    if not isinstance(value, dict) or set(value) != {"schema_version", "items"}:
        raise ProjectionError("invalid-manifest-shape")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1:
        raise ProjectionError("unsupported-manifest-version")
    items = value["items"]
    if not isinstance(items, list) or not items or len(items) > 5000:
        raise ProjectionError("invalid-item-count")
    ids = set()
    paths = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != FIELDS:
            raise ProjectionError("invalid-item-shape")
        identifier = item["id"]
        if type(identifier) is not str or re.fullmatch(r"[a-z][a-z0-9._-]{0,63}", identifier) is None:
            raise ProjectionError("invalid-item-id")
        if identifier in ids:
            raise ProjectionError("duplicate-item-id")
        ids.add(identifier)
        source = item["source"]
        _safe_name(source)
        if source in paths:
            raise ProjectionError("duplicate-source")
        paths.add(source)
        if item["visibility"] not in VISIBILITIES or type(item["visibility"]) is not str:
            raise ProjectionError("invalid-visibility")
        if item["kind"] != "literal-text" or type(item["kind"]) is not str:
            raise ProjectionError("unsupported-material")
        if type(item["sha256"]) is not str or re.fullmatch(r"[a-f0-9]{64}", item["sha256"]) is None:
            raise ProjectionError("invalid-source-digest")
    return items


def _safe_name(name: str) -> PurePosixPath:
    if (type(name) is not str or not name or "\\\\" in name or "\\x00" in name
            or any(ord(c) < 32 for c in name)
            or ":" in name or name.startswith("/")
            or any(x in ("", ".", "..") for x in name.split("/"))):
        raise ProjectionError("unsafe-source-path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".git" in path.parts:
        raise ProjectionError("unsafe-source-path")
    return path


def _read_material(root: Path, item: dict) -> str:
    parts = _safe_name(item["source"]).parts
    path = root
    for part in parts:
        path /= part
        if path.is_symlink():
            raise ProjectionError("symlink-source")
    if not path.is_file():
        raise ProjectionError("missing-source")
    if not path.resolve().is_relative_to(root):
        raise ProjectionError("source-outside-root")
    try:
        if path.stat().st_size > MAX_ITEM_BYTES:
            raise ProjectionError("oversized-source")
        data = path.read_bytes()
        if len(data) > MAX_ITEM_BYTES:
            raise ProjectionError("oversized-source")
    except OSError as exc:
        raise ProjectionError("source-read-failed") from exc
    if _hash(data) != item["sha256"]:
        raise ProjectionError("source-digest-mismatch")
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProjectionError("non-utf8-source") from exc
    if "\\x00" in decoded:
        raise ProjectionError("null-in-source")
    return decoded


def _quoted(value: str) -> str:
    """Encode authored prose as a single Typst string literal, not source code."""
    return json.dumps(value, ensure_ascii=False)


def _preflight(manifest, source_root, destination, target):
    if target not in TARGETS:
        raise ProjectionError("unsupported-target")
    source = Path(source_root)
    if source.is_symlink() or not source.is_dir():
        raise ProjectionError("invalid-source-root")
    root = source.resolve(strict=True)
    output = Path(destination).absolute()
    if output.exists() or output.is_symlink():
        raise ProjectionError("destination-already-exists")
    resolved = output.resolve()
    if resolved == root or resolved.is_relative_to(root) or root.is_relative_to(resolved):
        raise ProjectionError("source-destination-overlap")
    items = _validated_items(Path(manifest))
    # Reject undecided rights globally: no default-to-public or silent deletion.
    if any(item["visibility"] == "unresolved" for item in items):
        raise ProjectionError("unresolved-rights")
    return root, output, items


def project(manifest, source_root, destination, *, target: str):
    """Build a sealed, text-only Typst projection; return its public-safe receipt.

    Rights review is an external prerequisite, not something inferred here.
    Success means exactly these reviewed text bytes entered the staging source.
    It does not mean a PDF was compiled, examined, deposited or approved.
    """
    root, output, items = _preflight(manifest, source_root, destination, target)
    paragraphs = []
    included = withheld = 0
    # Validate ALL named material, including items withheld from public output.
    # Confidential source names and bytes are never included in the public receipt.
    for item in items:
        material = _read_material(root, item)
        if target == "deposit-public" and item["visibility"] == "restricted":
            paragraphs.append(OMISSION)
            withheld += 1
        else:
            paragraphs.append(material)
            included += 1
    # Every content fragment is a string literal; hostile Typst tokens cannot
    # become imports/functions, and no original source path is referenced.
    source = ("// UMTHESIS rights-projected literal text. Not a complete thesis.\\n"
              + "\\n".join("#par(" + _quoted(piece) + ")" for piece in paragraphs)
              + "\\n").encode("utf-8")
    report = {
        "schema_version": 1,
        "target": target,
        "content_kind": "literal-text-only",
        "included_count": included,
        "withheld_count": withheld,
        "main_sha256": _hash(source),
        "main_bytes": len(source),
        "status": "projected-not-validated-pdf",
    }
    # The destination is disjoint from the source and must not exist. Stage on
    # the same filesystem and rename only after all inputs have been checked.
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".rights-projection-", dir=output.parent))
    try:
        (stage / "main.typ").write_bytes(source)
        (stage / "projection.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\\n", encoding="utf-8"
        )
        if output.exists() or output.is_symlink():
            raise ProjectionError("destination-already-exists")
        os.rename(stage, output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args(argv)
    try:
        receipt = project(args.manifest, args.source_root, args.destination,
                          target=args.target)
    except ProjectionError as exc:
        print("rights-projection: " + exc.code, file=sys.stderr)
        return 2
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
