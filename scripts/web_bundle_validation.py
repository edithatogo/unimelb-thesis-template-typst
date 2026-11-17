#!/usr/bin/env python3
"""Offline structural and privacy-boundary verifier for experimental HTML bundles.

A successful check is not a rights decision or a browser accessibility claim.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


class WebBundleError(ValueError):
    """Stable public error code; never echo private input or sentinel text."""

    def __init__(self, code):
        self.code = code
        super().__init__(code)


ALLOWED = {".html", ".css", ".svg", ".png", ".jpg", ".jpeg", ".gif",
           ".webp", ".txt", ".json", ".ico", ".woff", ".woff2"}
ACTIVE = {"script", "iframe", "object", "embed", "form", "base", "style", "applet"}


class HtmlOracle(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.html_count = 0
        self.headings = []
        self.ids = set()
        self.links = []
        self.math_count = 0
        self.tables = []

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs)

    def _start(self, tag, attrs):
        if tag in ACTIVE:
            raise WebBundleError("active-html-content")
        if len(attrs) != len({k for k, _ in attrs}):
            raise WebBundleError("duplicate-html-attribute")
        a = dict(attrs)
        if tag == "html":
            self.html_count += 1
            self.lang = a.get("lang")
        if "id" in a:
            identifier = a["id"]
            if not identifier or identifier in self.ids:
                raise WebBundleError("duplicate-or-empty-id")
            self.ids.add(identifier)
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "math":
            self.math_count += 1
        if tag == "img":
            alt = a.get("alt")
            if alt is None or (not alt.strip() and a.get("role") != "presentation"):
                raise WebBundleError("missing-image-alternative")
            if not a.get("src"):
                raise WebBundleError("missing-image-source")
        if tag == "table":
            self.tables.append({"caption": False, "th": False})
        if tag == "caption" and self.tables:
            self.tables[-1]["caption"] = True
        if tag == "th" and self.tables:
            self.tables[-1]["th"] = True
        if tag == "meta" and a.get("http-equiv", "").lower() == "refresh":
            raise WebBundleError("html-refresh")
        if any(k in a for k in ("srcset", "style", "onload", "onclick")):
            raise WebBundleError("unreviewed-html-attribute")
        for key in ("href", "src", "poster", "data", "action"):
            if key in a:
                self.links.append((tag, key, a[key]))

    def handle_endtag(self, tag):
        if tag == "table":
            if not self.tables:
                raise WebBundleError("invalid-table")
            item = self.tables.pop()
            if not all(item.values()):
                raise WebBundleError("missing-table-semantics")

    def finish(self):
        if self.html_count != 1 or not isinstance(self.lang, str) or not self.lang.strip():
            raise WebBundleError("missing-document-language")
        if not self.headings or self.headings[0] != 1 or self.headings.count(1) != 1:
            raise WebBundleError("invalid-heading-root")
        if any(b > a + 1 for a, b in zip(self.headings, self.headings[1:])):
            raise WebBundleError("heading-level-skip")
        if self.tables:
            raise WebBundleError("unclosed-table")


def _resolve_link(origin, raw):
    if not isinstance(raw, str) or not raw or any(ord(c) < 32 for c in raw):
        raise WebBundleError("invalid-link")
    if raw.startswith("//"):
        raise WebBundleError("remote-unpinned-resource")
    try:
        uri = urlsplit(raw)
        name = unquote(uri.path, errors="strict")
        fragment = unquote(uri.fragment, errors="strict")
    except (ValueError, UnicodeError) as exc:
        raise WebBundleError("invalid-link-encoding") from exc
    if uri.scheme:
        if uri.scheme.lower() not in {"https", "mailto"}:
            raise WebBundleError("unsupported-link-scheme")
        return None
    if uri.netloc or uri.query or name.startswith("/") or "\\" in name:
        raise WebBundleError("unsafe-local-link")
    if any(ord(c) < 32 for c in name + fragment):
        raise WebBundleError("invalid-link")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(origin), name)) if name else origin
    if target in ("..", ".") or target.startswith("../") or target.startswith("/"):
        raise WebBundleError("link-escapes-bundle")
    return target, fragment


def _svg_oracle(data):
    lower = data.lower()
    if any(x in lower for x in (b"<!doctype", b"<!entity", b"<script", b"foreignobject", b"url(")):
        raise WebBundleError("unreviewed-svg-content")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise WebBundleError("invalid-svg") from exc
    if not root.tag.endswith("svg"):
        raise WebBundleError("invalid-svg-root")
    for node in root.iter():
        for key, value in node.attrib.items():
            if key.lower().endswith("href") and not value.startswith("#"):
                raise WebBundleError("unreviewed-svg-reference")
            if key.lower().startswith("on"):
                raise WebBundleError("active-svg-attribute")


def _inventory(root, forbidden):
    files = {}
    aliases = set()
    total = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise WebBundleError("symlink-bundle-entry")
        if path.is_dir():
            continue
        if not path.is_file():
            raise WebBundleError("invalid-bundle-entry")
        name = path.relative_to(root).as_posix()
        if (any(part.startswith(".") or "\\" in part for part in name.split("/"))
                or name.casefold() in aliases):
            raise WebBundleError("unsafe-or-colliding-path")
        aliases.add(name.casefold())
        if path.suffix.lower() not in ALLOWED:
            raise WebBundleError("unsupported-asset-type")
        if path.stat().st_size > 12 * 1024 * 1024:
            raise WebBundleError("oversized-asset")
        data = path.read_bytes()
        if any(secret.encode("utf-8") in data for secret in forbidden):
            raise WebBundleError("restricted-content-present")
        total += len(data)
        if len(data) > 12 * 1024 * 1024 or total > 96 * 1024 * 1024 or len(files) >= 2000:
            raise WebBundleError("bundle-limit-exceeded")
        if name.endswith(".svg"):
            _svg_oracle(data)
        if name.endswith(".css") and (b"url(" in data.lower() or b"@import" in data.lower()):
            raise WebBundleError("unreviewed-css-resource")
        files[name] = data
    return files


def inspect_bundle(root, *, required_pages=("index.html",), forbidden=()):
    """Inspect a local directory and return only structural counts and hashes."""
    directory = Path(root)
    if directory.is_symlink() or not directory.is_dir():
        raise WebBundleError("missing-bundle")
    directory = directory.resolve(strict=True)
    if (not isinstance(forbidden, (tuple, list))
            or any(type(s) is not str or not s for s in forbidden)):
        raise WebBundleError("invalid-forbidden-set")
    if (not isinstance(required_pages, (tuple, list)) or not required_pages
            or any(type(s) is not str or not s.endswith(".html") for s in required_pages)):
        raise WebBundleError("invalid-required-pages")
    files = _inventory(directory, forbidden)
    if not files:
        raise WebBundleError("empty-bundle")
    if any(name not in files for name in required_pages):
        raise WebBundleError("missing-required-page")
    documents = {}
    for name, data in files.items():
        if not name.endswith(".html"):
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise WebBundleError("invalid-html-encoding") from exc
        parser = HtmlOracle()
        parser.feed(text)
        parser.close()
        parser.finish()
        documents[name] = parser
    if not documents:
        raise WebBundleError("no-html-pages")
    external = 0
    for name, page in documents.items():
        for tag, attr, raw in page.links:
            link = _resolve_link(name, raw)
            if link is None:
                if attr != "href" or tag not in {"a", "link"}:
                    raise WebBundleError("external-asset-reference")
                external += 1
                continue
            dest, fragment = link
            if dest not in files:
                raise WebBundleError("missing-local-resource")
            if fragment and (dest not in documents or fragment not in documents[dest].ids):
                raise WebBundleError("unresolved-local-fragment")
    return {
        "schema_version": 1, "status": "structural-validation-only",
        "html_pages": len(documents),
        "mathml_elements": sum(x.math_count for x in documents.values()),
        "external_links_not_fetched": external,
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--expect", action="append", required=True)
    parser.add_argument("--sentinel-file", type=Path)
    args = parser.parse_args(argv)
    try:
        denied = ()
        if args.sentinel_file is not None:
            denied = tuple(args.sentinel_file.read_text(encoding="utf-8").splitlines())
        result = inspect_bundle(args.root, required_pages=args.expect, forbidden=denied)
    except (WebBundleError, OSError, UnicodeError) as exc:
        code = exc.code if isinstance(exc, WebBundleError) else "invalid-private-sentinel-input"
        print("web-bundle: " + code, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
