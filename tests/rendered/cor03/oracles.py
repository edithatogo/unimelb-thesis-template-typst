"""Independent public-outcome checks for the bounded legacy configuration corpus.

Compilation, PDF extraction and timeout enforcement belong to scripts/verify.py.
These checks do not certify the shared JSON contract adapter or thesis policy.
"""

from __future__ import annotations

import re


EXPECTED_SPECIMEN_COUNT = 34
CREATION_TIMESTAMP = "1794700800"
SOURCE_FILES = (
    "lib.typ", "config/options.typ", "config/metadata.typ", "layouts/document.typ",
    "pages/title.typ", "utils/style.typ", "utils/fonts.typ", "utils/locales.typ",
    "utils/locales/en.typ", "utils/locales/zh.typ",
)
RESOURCE_FILES = tuple("tests/rendered/cor03/" + name for name in
                       ("raw.bib", "resolved.bib", "second.bib"))

LOGO_ERROR = (
    "show_logo=true is not permitted: University of Melbourne thesis preparation "
    "clause 3.6 prohibits the University logo in a thesis. Use show_logo=false."
)
EXPECTED_ERRORS = {
    "cli-logo-true": LOGO_ERROR,
    "cli-logo-malformed": "Invalid CLI show_logo: expected exactly true or false.",
    "cli-profile-unknown": "Invalid profile: expected one of default, draft, screen, print.",
    "cli-font-unknown": "Invalid font_theme: expected one of unimelb, classic, modern.",
    "cli-locale-unknown": "Invalid locale: expected one of en, zh.",
    "explicit-logo-over-cli": LOGO_ERROR,
    "malformed-double": "Invalid double_sided: expected a boolean or auto for the profile default.",
    "unknown-override": "Unknown metadata_overrides field 'include_bibliogaphy'.",
    "thesis-logo-explicit-true": LOGO_ERROR,
    "title-logo-true": LOGO_ERROR,
    "title-logo-malformed": "Invalid show_logo: expected a boolean; use false for this thesis template.",
}

CASES = (
    ("control", "thesis-config", {"cor03-case": "control"}),
    ("cli-logo-false", "thesis-config", {"cor03-case": "cli-logo", "show_logo": "false"}),
    ("cli-logo-true", "thesis-config", {"cor03-case": "cli-logo", "show_logo": "true"}),
    ("cli-logo-malformed", "thesis-config", {"cor03-case": "cli-logo", "show_logo": "flase"}),
    ("cli-profile-unknown", "thesis-config", {"profile": "unexpected-profile"}),
    ("cli-font-unknown", "thesis-config", {"cor03-case": "cli-font", "font_theme": "unexpected-font"}),
    ("cli-locale-unknown", "thesis-config", {"locale": "unexpected-locale"}),
    ("explicit-logo-over-cli", "thesis-config", {"show_logo": "true"}),
    ("default-explicit-double-true", "thesis-config", {"cor03-case": "double-true"}),
    ("print-omitted-double", "thesis-config", {"profile": "print"}),
    ("print-explicit-double-false", "thesis-config", {"cor03-case": "double-false", "profile": "print"}),
    ("malformed-double", "thesis-config", {"cor03-case": "double-string"}),
    ("bib-disable", "thesis-config", {"cor03-case": "bib-disable"}),
    ("bib-enable", "thesis-config", {"cor03-case": "bib-enable"}),
    ("bib-path", "thesis-config", {"cor03-case": "bib-path"}),
    ("bib-style", "thesis-config", {"cor03-case": "bib-style"}),
    ("custom-declaration", "thesis-config", {"cor03-case": "custom-declaration"}),
    ("unknown-override", "thesis-config", {"cor03-case": "unknown-override"}),
    ("direct-print-style", "style-control", {}),
    ("style-chicago", "bibliography-style", {"cor03-style": "chicago"}),
    ("style-numeric", "bibliography-style", {"cor03-style": "numeric"}),
    ("style-author-year", "bibliography-style", {"cor03-style": "author-year"}),
    ("style-author-underscore-year", "bibliography-style", {"cor03-style": "author_year"}),
    ("native-path", "native-paths", {"cor03-path": "native"}),
    ("native-collection", "native-paths", {"cor03-path": "collection"}),
    ("native-path-override", "native-paths", {"cor03-path": "override"}),
    ("thesis-logo-default", "thesis-config", {"cor03-case": "cli-logo"}),
    ("thesis-logo-explicit-true", "thesis-logo", {}),
    ("title-logo-default", "title-config", {}),
    ("title-logo-false", "title-config", {"cor03-logo": "false"}),
    ("title-logo-true", "title-config", {"cor03-logo": "true"}),
    ("title-logo-malformed", "title-config", {"cor03-logo": "FALSE"}),
    ("direct-layout", "direct-layout", {}),
    ("caller-input", "thesis-config", {"user-note": "permitted-value"}),
)
COLOR_EXPECTATIONS = {
    "control": "rgb",
    "print-omitted-double": "cmyk",
    "print-explicit-double-false": "cmyk",
    "direct-print-style": "cmyk",
}


def specimens():
    return [{
        "id": name,
        "fixture": "tests/rendered/cor03/" + fixture + ".typ",
        "inputs": inputs.copy(),
        "expected_error": EXPECTED_ERRORS.get(name),
        "expected_color": COLOR_EXPECTATIONS.get(name),
    } for name, fixture, inputs in CASES]


def _result(checks):
    errors = [check["name"] for check in checks if not check["passed"]]
    return {"passed": bool(checks) and not errors, "checks": checks, "errors": errors}


def check_rejection(specimen, diagnostics, *, exit_code, timed_out, pdf_exists):
    """An unrelated syntax error, timeout or successful compile cannot pass."""
    errors = re.findall(r"^error: (.+)$", diagnostics, re.MULTILINE)
    expected = "panicked with: " + specimen["expected_error"]
    return _result([
        {"name": "Typst rejects with exit 1", "passed": exit_code == 1,
         "observed": exit_code},
        {"name": "Rejection finishes within the command time budget", "passed": timed_out is False},
        {"name": "Only the intended configuration diagnostic is emitted",
         "passed": errors == [expected], "expected": expected, "observed": errors},
        {"name": "Rejected configuration produces no PDF", "passed": not pdf_exists},
    ])


def pages_from_text(extracted):
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return [" ".join(page.split()) for page in pages]


def color_page(specimen, extracted):
    """Find the controlled colour page from a body marker, not template counters."""
    if specimen["expected_color"] is None:
        return None
    if specimen["id"] == "direct-print-style":
        return 1
    pages = pages_from_text(extracted)
    found = [index + 1 for index, page in enumerate(pages)
             if "COR03 FIRST CHAPTER BODY" in page]
    if len(found) != 1:
        raise ValueError("The colour control requires exactly one first chapter body marker")
    return found[0]


def check_text(specimen, extracted, pdf_pages, *, color_streams=()):
    identifier = specimen["id"]
    pages = pages_from_text(extracted)
    text = " ".join(pages)
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})

    def count(value, expected=1):
        actual = text.count(value)
        check("Literal text count: " + value, actual == expected,
              expected=expected, observed=actual)

    check("Extracted page inventory agrees with the PDF", len(pages) == pdf_pages and pdf_pages > 0,
          expected=pdf_pages, observed=len(pages))
    if specimen["fixture"].endswith("thesis-config.typ"):
        count("COR03 FIRST CHAPTER BODY")
        count("COR03 SECOND CHAPTER BODY")
        positions = [[i + 1 for i, page in enumerate(pages) if marker in page]
                     for marker in ("COR03 FIRST CHAPTER BODY", "COR03 SECOND CHAPTER BODY")]
        duplex = identifier in ("default-explicit-double-true", "print-omitted-double")
        expected_gap = 2 if duplex else 1
        actual_gap = positions[1][0] - positions[0][0] if all(len(p) == 1 for p in positions) else None
        check("Explicit duplex setting determines the chapter-page gap", actual_gap == expected_gap,
              expected=expected_gap, observed=actual_gap)
        if duplex:
            check("Duplex chapters open on odd physical pages",
                  all(len(p) == 1 and p[0] % 2 == 1 for p in positions), observed=positions)
    if specimen["fixture"].endswith(("thesis-config.typ", "native-paths.typ", "title-config.typ")):
        # The old narrow placeholder line-breaks Melbourne after a soft hyphen.
        # Accept only that specific optional break when counting this label.
        university_count = len(re.findall(r"University of Mel(?:\u00ad\s*)?bourne", pages[0])) if pages else 0
        check("Title has one university heading and no duplicate logo placeholder",
              university_count == 1, expected=1, observed=university_count)
    if identifier == "custom-declaration":
        count("COR03 CUSTOM DECLARATION SENTINEL")
        count("the thesis comprises only my original work", 0)
        declaration_pages = [page for page in pages if "COR03 CUSTOM DECLARATION SENTINEL" in page]
        check("Custom declaration is inside the Declaration page",
              len(declaration_pages) == 1 and declaration_pages[0].startswith("Declaration "))
    elif specimen["fixture"].endswith(("thesis-config.typ", "native-paths.typ")):
        count("the thesis comprises only my original work towards the Doctor of Philosophy")
    if identifier in ("bib-enable", "bib-path", "bib-style", "native-path", "native-path-override", "native-collection"):
        count("COR03 RESOLVED BIBLIOGRAPHY TITLE")
        count("COR03 RAW BIBLIOGRAPHY TITLE", 0)
    if identifier in ("bib-enable", "bib-style", "style-numeric"):
        count("COR03 CITATION [1]")
    if identifier == "bib-disable":
        count("COR03 RAW BIBLIOGRAPHY TITLE", 0)
        count("COR03 RESOLVED BIBLIOGRAPHY TITLE", 0)
    if identifier == "native-collection":
        count("COR03 SECOND COLLECTION TITLE")
        count("COR03 SECOND RESOURCE (Researcher, 2025)")
    if identifier in ("style-author-year", "style-author-underscore-year"):
        count("COR03 CITATION (Candidate, 2026)")
    if identifier == "style-chicago":
        count("COR03 CITATION (Candidate 2026)")
    if identifier.startswith("style-"):
        # Chicago applies sentence case to the synthetic title; preserve its
        # native formatting while still requiring the unique reference body.
        count("RESOLVED BIBLIOGRAPHY TITLE")
    if identifier.startswith("native-"):
        count("COR03 NATIVE RESOURCE BODY")
    if identifier.startswith("title-logo-"):
        count("COR03 DIRECT TITLE SENTINEL")
    if identifier == "direct-layout":
        count("COR03 DIRECT LAYOUT FIRST BODY")
        count("COR03 DIRECT LAYOUT SECOND BODY")
        check("Direct print layout respects explicit one-sided rendering",
              len(pages) == 2 and "COR03 DIRECT LAYOUT FIRST BODY" in pages[0]
              and "COR03 DIRECT LAYOUT SECOND BODY" in pages[1])
    if identifier == "direct-print-style":
        count("COR03 DIRECT PRINT COLOR")
        count("cmyk")
    if specimen["expected_color"] is not None:
        streams = "\n".join(color_streams)
        number = r"(?:\d+(?:\.\d*)?|\.\d+)"
        cmyk = re.findall(r"(?<![\w.])(?:" + number + r"\s+){4}k(?=\s|$)", streams)
        rgb = re.findall(r"(?<![\w.])(?:" + number + r"\s+){3}scn(?=\s|$)", streams)
        expected = specimen["expected_color"]
        check("Controlled PDF page uses the expected colour model",
              bool(cmyk) if expected == "cmyk" else bool(rgb) and not cmyk,
              expected=expected, cmyk_operators=cmyk, rgb_operators=rgb)
    return _result(checks)
