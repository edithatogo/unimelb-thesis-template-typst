#!/usr/bin/env python3
"""Build and install the explicitly audited local template payload.

This is a bounded local distribution helper, not a Typst Universe submission
validator, network downloader, font installer or privacy projection.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tarfile
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parent.parent
PACKAGE_NAME = "unimelb-thesis-template"
RUNTIME_PATHS = (
    "assets/colors/unimelb-colors.typ",
    "config/abbreviations.typ",
    "config/appendix.typ",
    "config/contributions.typ",
    "config/glossary.typ",
    "config/index.typ",
    "config/metadata.typ",
    "config/optional.typ",
    "config/options.typ",
    "config/publications.typ",
    "config/review.typ",
    "endmatter/appendix-a.typ",
    "endmatter/appendix-b.typ",
    "endmatter/bibliography.typ",
    "endmatter/glossary.typ",
    "endmatter/index.typ",
    "endmatter/optional-glossary.typ",
    "endmatter/optional-index.typ",
    "frontmatter/authorship.typ",
    "frontmatter/dedication.typ",
    "frontmatter/preface.typ",
    "layouts/document.typ",
    "lib.typ",
    "pages/abstract.typ",
    "pages/acknowledgements.typ",
    "pages/appendix.typ",
    "pages/declaration.typ",
    "pages/front-matter.typ",
    "pages/funding.typ",
    "pages/glossary.typ",
    "pages/landscape-sample.typ",
    "pages/preface-helpers.typ",
    "pages/preface.typ",
    "pages/title.typ",
    "utils/fonts.typ",
    "utils/locales.typ",
    "utils/locales/en.typ",
    "utils/locales/zh.typ",
    "utils/style.typ",
)
STARTER_PATHS = (
    "LICENSE", "README.md", "assets/figures/example.svg",
    "chapters/introduction.typ", "main.typ", "references.bib",
)
PAYLOAD_PATHS = tuple(sorted((
    "CITATION.cff", "LICENSE", "README.md", "README.typ", "typst.toml", *RUNTIME_PATHS,
    *("template/" + name for name in STARTER_PATHS),
)))
GENERATED_OUTPUT_DIRECTORIES = frozenset(("build", "dist", "target"))
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_PAYLOAD_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_BYTES = 4 * 1024 * 1024
MAX_TAR_BYTES = 8 * 1024 * 1024
HEX_DIGEST = re.compile(r"[0-9a-f]{64}")
VERSION = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")


class PackageError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(value):
    if (type(value) is not str or not value or "\\" in value or "\x00" in value
            or any(part in ("", ".", "..") for part in value.split("/"))
            or PurePosixPath(value).is_absolute()):
        raise PackageError("unsafe-path", "Expected a normalized relative package path")
    return value


def source_bytes(root, name):
    safe_name(name)
    path = root
    for part in PurePosixPath(name).parts:
        path = path / part
        if path.is_symlink():
            raise PackageError("symlink-source", "Package inputs cannot use symlinks")
    if not path.is_file():
        raise PackageError("missing-source", "Required package input is missing: " + name)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise PackageError("oversize-source", "Package input exceeds its byte limit")
    return path.read_bytes()


def validate_manifest(value):
    if not isinstance(value, dict):
        raise PackageError("invalid-manifest", "The manifest must be a TOML table")
    package, template, tool = (value.get(key, {}) for key in ("package", "template", "tool"))
    if not all(isinstance(item, dict) for item in (package, template, tool)):
        raise PackageError("invalid-manifest", "Required manifest tables are malformed")
    version, compiler = package.get("version"), package.get("compiler")
    pin = tool.get("typst", {})
    if (package.get("name") != PACKAGE_NAME or type(version) is not str
            or not VERSION.fullmatch(version) or package.get("entrypoint") != "lib.typ"
            or package.get("license") != "Apache-2.0"
            or type(compiler) is not str or not VERSION.fullmatch(compiler)
            or not isinstance(pin, dict) or pin.get("version") != compiler
            or package.get("categories") != ["thesis"]
            or package.get("disciplines", []) != []
            or template != {"path": "template", "entrypoint": "main.typ", "thumbnail": "thumbnail.png"}):
        raise PackageError("invalid-manifest", "Manifest does not match the audited local package profile")
    for key in ("authors", "exclude"):
        values = package.get(key)
        if not isinstance(values, list) or not values or any(type(item) is not str or not item.strip() for item in values):
            raise PackageError("invalid-manifest", "Manifest arrays must contain nonempty strings")
    if type(package.get("description")) is not str or not package["description"].strip():
        raise PackageError("invalid-manifest", "A package description is required")
    return {"name": package["name"], "version": version, "compiler": compiler}


def collect_payload(root):
    root = Path(root).resolve()
    payload = {name: source_bytes(root, name) for name in PAYLOAD_PATHS}
    if sum(map(len, payload.values())) > MAX_PAYLOAD_BYTES:
        raise PackageError("oversize-payload", "The audited payload exceeds its byte limit")
    identity = validate_manifest(tomllib.loads(payload["typst.toml"].decode("utf-8")))
    if payload["template/LICENSE"] != payload["LICENSE"]:
        raise PackageError("license-mismatch", "The starter must retain the repository Apache licence bytes")
    return identity, payload



def protected_source_paths(root):
    """Protect existing source without following directory symlinks.

    Only the top-level build, dist and target directories are generated output
    areas. Payload names remain protected even when an input is missing.
    Directory inspection errors propagate before any build output is written.
    """
    protected = {root / name for name in PAYLOAD_PATHS}
    pending = [root]
    while pending:
        for path in pending.pop().iterdir():
            if path.is_symlink():
                protected.add(path)
            elif path.is_dir():
                if path.parent != root or path.name not in GENERATED_OUTPUT_DIRECTORIES:
                    pending.append(path)
            else:
                protected.add(path)
    return protected


def validate_outputs(root, archive, receipt=None):
    """Check all destinations before writing an archive or its receipt."""
    root = Path(root).resolve()
    destinations = [Path(archive)] + ([] if receipt is None else [Path(receipt)])
    protected = protected_source_paths(root)

    def aliases(first, second):
        return first.resolve() == second.resolve() or (
            first.exists() and second.exists() and first.samefile(second)
        )

    for destination in destinations:
        if destination.is_symlink() or any(aliases(destination, source) for source in protected):
            raise PackageError("unsafe-output", "Output cannot replace repository source or follow a symlink")
    if len(destinations) == 2 and aliases(*destinations):
        raise PackageError("unsafe-output", "Archive and receipt must be separate files")

def build(root, archive):
    root, archive = Path(root).resolve(), Path(archive)
    validate_outputs(root, archive)
    identity, payload = collect_payload(root)
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as bundle:
        for name, data in sorted(payload.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode, member.mtime = len(data), 0o644, 0
            member.uid = member.gid = 0
            member.uname = member.gname = ""
            bundle.addfile(member, io.BytesIO(data))
    compressed = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb", filename="", mtime=0, compresslevel=9) as stream:
        stream.write(raw.getvalue())
    data = compressed.getvalue()
    if len(data) > MAX_ARCHIVE_BYTES:
        raise PackageError("oversize-archive", "Compressed archive exceeds its byte limit")
    archive.parent.mkdir(parents=True, exist_ok=True)
    archive.write_bytes(data)
    return {
        "schema_version": 1, "artifact_kind": "local-template-package",
        **identity, "archive_sha256": sha256(data), "archive_bytes": len(data),
        "payload_bytes": sum(map(len, payload.values())),
        "files": {name: {"bytes": len(value), "sha256": sha256(value)}
                  for name, value in sorted(payload.items())},
        "fonts_included": False, "registry_submission_qualified": False,
        "offline_replay_qualified": False,
    }


def inspect_archive(archive, receipt):
    archive = Path(archive)
    if (not isinstance(receipt, dict) or type(receipt.get("schema_version")) is not int
            or receipt["schema_version"] != 1 or receipt.get("artifact_kind") != "local-template-package"
            or type(receipt.get("archive_sha256")) is not str
            or not HEX_DIGEST.fullmatch(receipt["archive_sha256"])
            or type(receipt.get("archive_bytes")) is not int
            or not isinstance(receipt.get("files"), dict)
            or set(receipt["files"]) != set(PAYLOAD_PATHS)):
        raise PackageError("invalid-receipt", "Expected the complete audited archive receipt")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise PackageError("oversize-archive", "Compressed archive exceeds its byte limit")
    data = archive.read_bytes()
    if len(data) != receipt["archive_bytes"] or sha256(data) != receipt["archive_sha256"]:
        raise PackageError("archive-hash-mismatch", "Archive bytes differ from the retained receipt")
    with gzip.GzipFile(fileobj=io.BytesIO(data), mode="rb") as stream:
        raw = stream.read(MAX_TAR_BYTES + 1)
    if len(raw) > MAX_TAR_BYTES:
        raise PackageError("oversize-archive", "Expanded archive exceeds its byte limit")
    payload = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:") as bundle:
        for member in bundle:
            name = safe_name(member.name)
            if name in payload:
                raise PackageError("duplicate-member", "Archive repeats a member path")
            if name not in PAYLOAD_PATHS or not member.isfile() or member.mode != 0o644:
                raise PackageError("unexpected-member", "Archive contains an unapproved member or type")
            if not 0 <= member.size <= MAX_FILE_BYTES:
                raise PackageError("oversize-source", "Archive member exceeds its byte limit")
            expected = receipt["files"][name]
            if (not isinstance(expected, dict) or type(expected.get("bytes")) is not int
                    or type(expected.get("sha256")) is not str
                    or not HEX_DIGEST.fullmatch(expected["sha256"])):
                raise PackageError("invalid-receipt", "Member receipt is malformed")
            stream = bundle.extractfile(member)
            value = stream.read(MAX_FILE_BYTES + 1)
            if (len(value) != member.size or len(value) != expected["bytes"]
                    or sha256(value) != expected["sha256"]):
                raise PackageError("member-hash-mismatch", "Archive member differs from its receipt")
            payload[name] = value
    if set(payload) != set(PAYLOAD_PATHS):
        raise PackageError("missing-member", "Archive omits an audited file")
    total = sum(map(len, payload.values()))
    if total > MAX_PAYLOAD_BYTES or type(receipt.get("payload_bytes")) is not int or total != receipt["payload_bytes"]:
        raise PackageError("invalid-receipt", "Payload byte inventory does not match")
    identity = validate_manifest(tomllib.loads(payload["typst.toml"].decode("utf-8")))
    if any(receipt.get(key) != value for key, value in identity.items()):
        raise PackageError("identity-mismatch", "Archive manifest and receipt identities differ")
    if payload["template/LICENSE"] != payload["LICENSE"]:
        raise PackageError("license-mismatch", "Starter licence differs from the retained repository licence")
    return identity, payload


def install(archive, receipt, cache_root):
    identity, payload = inspect_archive(archive, receipt)
    cache_root = Path(cache_root).absolute()
    if cache_root.is_symlink():
        raise PackageError("unsafe-cache", "Package cache cannot be a symlink")
    cache_root.mkdir(parents=True, exist_ok=True)
    cache_root = cache_root.resolve()
    namespace = cache_root
    for part in ("local", identity["name"]):
        namespace = namespace / part
        if namespace.is_symlink() or (namespace.exists() and not namespace.is_dir()):
            raise PackageError("unsafe-cache", "Package namespace cannot follow a symlink or replace a file")
        namespace.mkdir(exist_ok=True)
    destination = namespace / identity["version"]
    if destination.exists() or destination.is_symlink():
        raise PackageError("already-installed", "Package version already exists; choose a fresh cache")
    temporary = Path(tempfile.mkdtemp(prefix=".package-install-", dir=namespace))
    try:
        for name, data in payload.items():
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                output.write(data)
            target.chmod(0o644)
        temporary.rename(destination)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return destination


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    build_command = commands.add_parser("build")
    build_command.add_argument("--root", type=Path, default=ROOT)
    build_command.add_argument("--archive", type=Path, required=True)
    build_command.add_argument("--receipt", type=Path, required=True)
    install_command = commands.add_parser("install")
    install_command.add_argument("--archive", type=Path, required=True)
    install_command.add_argument("--receipt", type=Path, required=True)
    install_command.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            validate_outputs(args.root, args.archive, args.receipt)
            receipt = build(args.root, args.archive)
            args.receipt.parent.mkdir(parents=True, exist_ok=True)
            args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps({"archive": str(args.archive), "receipt": str(args.receipt), "sha256": receipt["archive_sha256"]}))
        else:
            receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
            destination = install(args.archive, receipt, args.cache)
            print(json.dumps({"installed": str(destination), "registry_submission_qualified": False}))
        return 0
    except (PackageError, OSError, ValueError, tarfile.TarError, EOFError) as exc:
        print(f"Package operation failed ({getattr(exc, 'code', type(exc).__name__)}): {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
