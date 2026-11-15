"""Declared-identifier scans and independent outcomes for COR-04 specimens.

Compilation and command budgets belong to scripts/verify.py. A negative case
may pass its regression assertion while its PDF scan remains explicitly failed.
This is no general anonymity detector, accessibility audit or package manifest.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET


EXPECTED_SPECIMEN_COUNT = 10
CREATION_TIMESTAMP = "1794700800"
SOURCE_FILES = (
    "lib.typ", "config/review.typ", "config/metadata.typ", "config/options.typ",
    "pages/title.typ", "pages/declaration.typ", "pages/preface.typ",
    "pages/preface-helpers.typ", "config/publications.typ", "layouts/document.typ",
    "utils/locales.typ", "utils/locales/en.typ", "utils/locales/zh.typ",
    "config/index.typ", "endmatter/optional-index.typ",
)
RESOURCE_FILES = tuple("tests/rendered/cor04/" + name for name in
                       ("identified.bib", "reviewed.bib", "neutral.svg"))
NOTICE = "Author review required: inspect authored text, references, images and links before sharing."
INVALID_BLIND_ERROR = "Invalid blind: expected a boolean."
TOKENS = {
    "base-author": "COR04BASEAUTHOR",
    "resolved-author": "COR04RESOLVEDAUTHOR",
    "department": "COR04DEPARTMENT",
    "school": "COR04SCHOOL",
    "university": "COR04UNIVERSITY",
    "supervisor": "COR04SUPERVISOR",
    "co-supervisor": "COR04COSUPERVISOR",
    "keyword-name": "COR04KEYWORDNAME",
    "keyword-email": "cor04author@example.invalid",
    "orcid": "0000-0000-0000-0001",
    "acknowledgement": "COR04ACKNAME",
    "contributor-alpha": "COR04CONTRIBUTORALPHA",
    "contributor-beta": "COR04CONTRIBUTORBETA",
    "publication-alpha": "COR04PUBLICATIONALPHA",
    "publication-beta": "COR04PUBLICATIONBETA",
    "publication-appendix": "COR04PUBLICATIONAPPENDIX",
    "authored-case-author": "COR04AUTOFIELDNAME",
    "preface-prose": "COR04AUTHOREDPREFACE",
    "preface-heading": "COR04PREFACEHEADING",
    "preface-section": "COR04PREFACESECTIONBODY",
    "ai-disclosure": "COR04AIDISCLOSURENAME",
    "human-disclosure": "COR04HUMANDISCLOSURENAME",
    "custom-declaration": "COR04CUSTOMDECLARATION",
    "body-heading": "COR04BOOKMARKNAME",
    "body-prose": "COR04PROSENAME",
    "body-email": "cor04prose@example.invalid",
    "image-alt-name": "COR04ALTNAME",
    "image-alt-email": "cor04alt@example.invalid",
    "caption": "COR04CAPTIONNAME",
    "mailto": "cor04contact@example.invalid",
    "repository-owner": "COR04REPOOWNER",
    "citation-author": "COR04BIBAUTHOR",
    "citation-title": "COR04BIBTITLE",
    "raw-contributor": "COR04RAWCONTRIBUTOR",
    "raw-publication": "COR04RAWPUBLICATION",
    "index-term": "COR04INDEXAUTHOR",
}


def specimens():
    cases = []
    for family in ("structured", "authored", "custom"):
        for identity in ("identified", "blind"):
            inputs = {"cor04-identity": identity}
            if family == "custom":
                inputs["cor04-custom-declaration"] = "true"
            cases.append({
                "id": family + "-" + identity,
                "fixture": "tests/rendered/cor04/" + (
                    "structured-fields.typ" if family == "structured" else "authored-surfaces.typ"
                ),
                "inputs": inputs, "family": family, "identity": identity,
                "reviewed": False, "expected_error": None,
                "expected_scan_pass": family == "structured" and identity == "blind",
            })
    cases.extend([
        {
            "id": "authored-reviewed-blind", "fixture": "tests/rendered/cor04/authored-surfaces.typ",
            "inputs": {"cor04-identity": "blind", "cor04-reviewed": "true"},
            "family": "authored", "identity": "blind", "reviewed": True,
            "expected_error": None, "expected_scan_pass": True,
        },
        {
            "id": "index-identified", "fixture": "tests/rendered/cor04/index-surfaces.typ",
            "inputs": {"cor04-identity": "identified"}, "family": "index", "identity": "identified",
            "reviewed": False, "expected_error": None, "expected_scan_pass": False,
        },
        {
            "id": "index-blind", "fixture": "tests/rendered/cor04/index-surfaces.typ",
            "inputs": {"cor04-identity": "blind"}, "family": "index", "identity": "blind",
            "reviewed": False, "expected_error": None, "expected_scan_pass": False,
        },
        {
            "id": "blind-string-rejected", "fixture": "tests/rendered/cor04/structured-fields.typ",
            "inputs": {"cor04-identity": "invalid"}, "family": "structured", "identity": "invalid",
            "reviewed": False, "expected_error": INVALID_BLIND_ERROR, "expected_scan_pass": None,
        },
    ])
    return cases


def compact(value):
    """Normalize extraction whitespace and soft hyphens, not arbitrary text."""
    return "".join(value.casefold().replace("\u00ad", "").split())


def token_hits(value):
    text = compact(value)
    return {name: text.count(compact(token)) for name, token in TOKENS.items()
            if compact(token) in text}


def scan_public_surfaces(native, extracted, xmp):
    """Inspect all retained text/native-string surfaces, recording real failures."""
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if not pages or any(not isinstance(page, str) for page in pages):
        raise ValueError("Missing extracted PDF pages")
    if not isinstance(native.get("pages"), list) or len(native["pages"]) != len(pages):
        raise ValueError("Native and extracted page inventories differ")
    if not isinstance(native.get("qpdf"), list) or len(native["qpdf"]) < 2:
        raise ValueError("Missing native PDF object inventory")
    objects = {}
    for chunk in native["qpdf"][1:]:
        if not isinstance(chunk, dict):
            raise ValueError("Invalid native PDF object chunk")
        objects.update(chunk)
    trailer = objects["trailer"]["value"]
    catalog = objects["obj:" + trailer["/Root"]]["value"]
    info = objects["obj:" + trailer["/Info"]]["value"]
    if not isinstance(info, dict):
        raise ValueError("Missing PDF Info dictionary")
    if not xmp.strip():
        raise ValueError("Missing XMP metadata capture")
    xmp_root = ET.fromstring(xmp)
    if not xmp_root.tag.endswith("xmpmeta"):
        raise ValueError("Unexpected XMP document root")
    if not isinstance(native.get("outlines"), list) or not isinstance(native.get("attachments"), dict):
        raise ValueError("Missing bookmark or attachment inventory")
    hits = []

    def record(surface, value, path):
        found = token_hits(value)
        if found:
            hits.append({"surface": surface, "path": path, "tokens": found})

    for index, page in enumerate(pages):
        record("visible", page, ["physical_page", index + 1])
    record("info", json.dumps(info, ensure_ascii=False), ["Info"])
    record("xmp", xmp, ["XMP"])

    def walk(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, path + [key])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, path + [index])
        elif isinstance(value, str):
            record("native", value[2:] if value.startswith("u:") else value, path)

    walk(objects, [])

    def outlines(entries):
        for entry in entries:
            record("bookmark", entry["title"], ["physical_page", entry["destpageposfrom1"]])
            outlines(entry["kids"])

    outlines(native["outlines"])
    return {
        "passed": not hits,
        "result": "fail" if hits else "pass",
        "scope": "Declared synthetic identifiers in captured visible text, Info, XMP, bookmarks and native object strings",
        "hits": hits, "pages": len(pages), "document_info": info,
        "tagged": catalog.get("/MarkInfo", {}).get("/Marked") is True,
        "has_structure_tree": "/StructTreeRoot" in catalog,
        "attachments": list(native["attachments"]),
        "reviewer_ready_certified": False,
    }


def _result(checks, **extra):
    errors = [check["name"] for check in checks if not check["passed"]]
    return {"passed": bool(checks) and not errors, "checks": checks, "errors": errors, **extra}


def check_rejection(case, diagnostics, *, exit_code, timed_out, pdf_exists):
    errors = re.findall(r"^error: (.+)$", diagnostics, re.MULTILINE)
    expected = "panicked with: " + case["expected_error"]
    return _result([
        {"name": "Wrong blind type exits 1", "passed": exit_code == 1, "observed": exit_code},
        {"name": "Wrong blind type is rejected within budget", "passed": timed_out is False},
        {"name": "Only the intended blind-type diagnostic occurs", "passed": errors == [expected],
         "expected": expected, "observed": errors},
        {"name": "Wrong blind type produces no PDF", "passed": not pdf_exists},
    ])


def analyze(case, native, extracted, xmp, diagnostics, pdf_pages):
    scan = scan_public_surfaces(native, extracted, xmp)
    checks = []
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    text = " ".join(" ".join(page.split()) for page in pages)
    first = " ".join(pages[0].split())
    blind = case["identity"] == "blind"

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})

    def count(value, expected=1, region=text):
        observed = compact(region).count(compact(value))
        check("Literal count: " + value, observed == expected, expected=expected, observed=observed)

    def observed(surface):
        return {token for hit in scan["hits"] if hit["surface"] == surface for token in hit["tokens"]}

    def contains(surface, required):
        found = observed(surface)
        check("Positive identity controls on " + surface, set(required) <= found,
              expected=sorted(required), observed=sorted(found))

    check("All PDF page inventories agree", scan["pages"] == pdf_pages and pdf_pages > 0)
    check("Native tag inventory is available", scan["tagged"] and scan["has_structure_tree"])
    check("No attachments are emitted by these specimens", scan["attachments"] == [])
    check("Raw public-surface scan has the declared expected outcome",
          scan["passed"] is case["expected_scan_pass"], expected=case["expected_scan_pass"],
          observed=scan["passed"])
    check("Base metadata never overrides the resolved author", "base-author" not in observed("visible"))
    if blind:
        count("Blind review copy", region=first)
        count("Author review required:", region=first)
        count("The University of Melbourne", 0)
        author = scan["document_info"].get("/Author")
        check("Blind Info author is neutral", author == "u:Author", observed=author)
        check("Blind Info keywords contain no values", scan["document_info"].get("/Keywords", "") in ("", "u:"))
        check("No managed author is present on any captured blind surface",
              not any({"base-author", "resolved-author", "authored-case-author"} & set(hit["tokens"])
                      for hit in scan["hits"]))
        count("Department withheld for review", region=first)
        count("School withheld for review", region=first)
        count("Institution withheld for review", region=first)
        check("One static queryable blind boundary diagnostic is emitted",
              isinstance(diagnostics, list) and len(diagnostics) == 1
              and diagnostics[0].get("code") == "blind-review-boundary")
        notices = diagnostics[0].get("diagnostics", []) if isinstance(diagnostics, list) and len(diagnostics) == 1 else []
        check("Author review diagnostic is explicit and contains no identity values",
              len(notices) == 1 and notices[0].get("code") == "author-review-required"
              and notices[0].get("message") == NOTICE and not token_hits(json.dumps(diagnostics)))
        fields = notices[0].get("fields", []) if len(notices) == 1 else []
        check("Diagnostic names uncontrolled prose, embedded content and raw helpers",
              {"body", "declaration", "preface", "bibliography", "alternative_text",
               "link_targets", "index_entries", "raw_helper_calls"} <= set(fields))
    else:
        count("The University of Melbourne", region=first)
        count("Blind review copy", 0)
        count("Author review required:", 0)
        check("Identified output has no blind diagnostic", diagnostics == [])

    if case["family"] == "structured":
        count("COR04 SAFE ABSTRACT BODY.")
        count("COR04 SAFE PREFACE BODY.")
        count("COR04 SAFE CHAPTER BODY.")
        count("COR04 SAFE DIGITAL ASSISTANCE")
        count("COR04 SAFE HUMAN ASSISTANCE")
        for value in ("Analysis", "Validation"):
            count(value)
        for value in ("60", "40"):
            check("Contribution percentage remains " + value,
                  re.search(r"\b" + value + r"\b", text) is not None)
        for value in ("published", "accepted", "Yes", "No"):
            check("Publication status/consent remains " + value,
                  re.search(r"\b" + value + r"\b", text) is not None)
        if blind:
            count("Contributor 1")
            count("Contributor 2")
            count("Publication 1 (details withheld for review)", 3)
            count("Publication 2 (details withheld for review)", 2)
        else:
            contains("visible", {
                "resolved-author", "department", "school", "university", "supervisor", "co-supervisor",
                "keyword-name", "keyword-email", "orcid", "acknowledgement", "contributor-alpha",
                "contributor-beta", "publication-alpha", "publication-beta", "publication-appendix",
            })
            for surface in ("info", "xmp"):
                contains(surface, {"resolved-author", "keyword-name", "keyword-email", "orcid"})
            count("COR04CONTRIBUTORALPHA")
            count("COR04CONTRIBUTORBETA")
            count("COR04PUBLICATIONALPHA", 3)
            count("COR04PUBLICATIONBETA", 2)
    elif case["family"] == "index":
        count("COR04 SAFE INDEX BODY.")
        count(TOKENS["index-term"])
        index_pages = [" ".join(page.split()) for page in pages if TOKENS["index-term"] in page]
        check("Authored index term is rendered on the actual Index page",
              len(index_pages) == 1 and index_pages[0].startswith("Index "))
        contains("visible", {"index-term"})
        if not blind:
            contains("info", {"authored-case-author"})
            contains("xmp", {"authored-case-author"})
        check("Identifying index remains a failed identity scan",
              scan["passed"] is False and scan["result"] == "fail")
    elif case["reviewed"]:
        count("COR04 SAFE CHAPTER BODY.")
        count("COR04 SAFE REFERENCE TITLE")
        count("Reviewed contributor")
        count("Reviewed publication")
        count("Contact details withheld for review.")
        check("Reviewed alternative text remains meaningful",
              "Neutral synthetic line diagram" in json.dumps(native, ensure_ascii=False))
        check("Reviewed resource link still exists",
              "https://example.invalid/resources" in json.dumps(native))
    else:
        visible = {
            "preface-prose", "preface-heading", "preface-section", "body-heading", "body-prose",
            "body-email", "orcid", "caption", "citation-author", "citation-title",
            "raw-contributor", "raw-publication",
        }
        if case["family"] == "custom":
            visible.add("custom-declaration")
        else:
            visible.update({"ai-disclosure", "human-disclosure"})
        if not blind:
            visible.add("authored-case-author")
            contains("info", {"authored-case-author"})
            contains("xmp", {"authored-case-author"})
        contains("visible", visible)
        contains("bookmark", {"preface-heading", "body-heading"})
        contains("native", {"image-alt-name", "image-alt-email", "mailto", "repository-owner"})
        for key, tokens in (
            ("/T", {"preface-heading", "body-heading"}),
            ("/Alt", {"image-alt-name", "image-alt-email"}),
            ("/URI", {"mailto", "repository-owner"}),
        ):
            found = {token for hit in scan["hits"] if hit["surface"] == "native"
                     and hit["path"][-1] == key for token in hit["tokens"]}
            check("Residual identifiers detected in native " + key, tokens <= found,
                  expected=sorted(tokens), observed=sorted(found))
        check("Residual PDF remains a failed identity scan despite any warning",
              scan["passed"] is False and scan["result"] == "fail")

    return _result(checks, public_surface_scan=scan, author_review_required=blind,
                   reviewer_ready_certified=False)
