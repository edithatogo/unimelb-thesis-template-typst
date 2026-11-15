"""Independent rendered outcomes for the bounded glossary/abbreviation/index corpus.

The verifier owns all commands. Native PDF parsing is supplied by the existing
COR-02 pure parser; none of these expectations come from template functions.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


EXPECTED_SPECIMEN_COUNT = 25
CREATION_TIMESTAMP = "1794700800"
SOURCE_FILES = (
    "lib.typ", "config/abbreviations.typ", "config/glossary.typ", "config/index.typ",
    "pages/glossary.typ", "endmatter/optional-glossary.typ", "endmatter/optional-index.typ",
    "config/metadata.typ", "utils/style.typ", "utils/locales.typ", "utils/fonts.typ",
)
ROWS = (
    ("Machine Learning", "ML", "A method of data analysis that automates analytical model building."),
    ("Deep Learning", "DL", "A subset of machine learning using neural networks with multiple layers."),
    ("Neural Network", "NN", "A computing system inspired by biological neural networks."),
    ("Algorithm", "Algo", "A procedure or formula for solving a problem."),
    ("Artificial Intelligence", "AI", "The simulation of human intelligence processes by machines."),
    ("Natural Language Processing", "NLP", "A subfield of AI focused on the interaction between computers and humans in natural language."),
    ("Computer Vision", "CV", "A field of AI that trains computers to interpret and understand visual information from the world."),
    ("Support Vector Machine", "SVM", "A supervised learning algorithm used for classification and regression tasks."),
    ("Random Forest", "RF", "An ensemble learning method that constructs multiple decision trees."),
    ("Gradient Boosting", "GB", "A machine learning technique for regression and classification problems."),
)
INDEX_TERMS = (
    "Abstract", "Appendix", "Bibliography", "Citation", "Hypothesis",
    "Literature Review", "Methodology", "Peer Review", "Plagiarism", "Thesis",
)
CASES = (
    ("abbreviations", "table"), ("abbreviations", "first-use"),
    ("glossary", "first-use"), ("glossary", "marked"),
    ("glossary", "automatic"), ("glossary", "extract"), ("glossary", "index"),
    ("index", "marked"), ("index", "columns"), ("index", "manual"),
    ("index", "subentries"), ("index", "alias"),
    ("pages", "abbreviations"), ("pages", "combined"),
    ("edge-cases", "roman"), ("edge-cases", "empty-index"),
    ("edge-cases", "category"), ("edge-cases", "hidden-pages"),
    ("edge-cases", "zero-page"), ("edge-cases", "reversed-range"),
    ("edge-cases", "invalid-page"), ("edge-cases", "empty-term"),
    ("edge-cases", "automatic-index"), ("edge-cases", "conflicting-definition"),
    ("thesis-index", "supplied"),
)
EXPECTED_ERRORS = {
    "glossary-automatic": "panicked with: Automatic glossary extraction is unsupported. Mark terms with glossary-term(term, definition), then call generate-glossary-page().",
    "glossary-extract": "panicked with: Automatic glossary extraction is unsupported. Use explicit glossary-term(term, definition) markers; extract-technical-terms(string) provides suggestions only.",
    "edge-cases-zero-page": "assertion failed: Manual index page numbers must be positive integers.",
    "edge-cases-reversed-range": "assertion failed: Manual index range must be ordered and contain at most 10001 pages.",
    "edge-cases-invalid-page": "assertion failed: Invalid manual index page reference: tomorrow",
    "edge-cases-empty-term": "assertion failed: Index term must be a nonempty string.",
    "edge-cases-automatic-index": "panicked with: Automatic index extraction is unsupported. Mark actual locations with index-term(term), or supply explicit page references to optional-index-page(). extract-index-terms(string) provides suggestions only.",
    "edge-cases-conflicting-definition": "assertion failed: Conflicting definitions for glossary term: Conflict Sentinel",
}
LINK_CASES = ("glossary-marked", "glossary-index", "edge-cases-roman")


def specimens():
    return [{
        "id": module + "-" + case,
        "fixture": "tests/rendered/terms/" + module + ".typ",
        "inputs": {"case": case},
        "expected_error": EXPECTED_ERRORS.get(module + "-" + case),
        "needs_boxes": module + "-" + case in LINK_CASES,
    } for module, case in CASES]


def normal(value):
    return " ".join(value.split())


def result(checks):
    errors = [check["name"] for check in checks if not check["passed"]]
    return {"passed": bool(checks) and not errors, "checks": checks, "errors": errors}


def check_rejection(specimen, diagnostics, *, exit_code, timed_out, pdf_exists):
    observed = re.findall(r"^error: (.+)$", diagnostics, re.MULTILINE)
    return result([
        {"name": "Intended rejection exits exactly 1", "passed": exit_code == 1, "observed": exit_code},
        {"name": "Intended rejection does not time out", "passed": timed_out is False},
        {"name": "Only the intended diagnostic is emitted", "passed": observed == [specimen["expected_error"]],
         "expected": specimen["expected_error"], "observed": observed},
        {"name": "Rejected input produces no document", "passed": not pdf_exists},
    ])


def word_boxes(source):
    if source is None:
        raise ValueError("Expected glossary links require retained bounding boxes")
    root = ET.fromstring(source)
    pages = []
    for page in root.findall(".//{*}page"):
        lines = []
        for line in page.findall(".//{*}line"):
            words = [{"text": "".join(word.itertext()),
                      **{key: float(word.attrib[key]) for key in ("xMin", "xMax", "yMin", "yMax")}}
                     for word in line.findall("{*}word")]
            if words:
                lines.append(words)
        pages.append({"height": float(page.attrib["height"]), "lines": lines})
    if not pages:
        raise ValueError("Bounding-box capture has no pages")
    return pages


def phrase_boxes(boxes, phrase, page_numbers):
    expected = phrase.split()
    found = []
    for number in page_numbers:
        for words in boxes[number - 1]["lines"]:
            for offset in range(len(words) - len(expected) + 1):
                selected = words[offset:offset + len(expected)]
                if [word["text"] for word in selected] == expected:
                    found.append({"page": number,
                                  "xMin": min(word["xMin"] for word in selected),
                                  "xMax": max(word["xMax"] for word in selected),
                                  "yMin": min(word["yMin"] for word in selected),
                                  "yMax": max(word["yMax"] for word in selected)})
    return found


def check_links(identifier, pdf, boxes, check):
    links = pdf.links()
    if identifier == "glossary-index":
        expected = [(term, (3,), (1, 2), 1) for term in INDEX_TERMS]
    elif identifier == "glossary-marked":
        expected = [("Sentinel Concept", (1, 2), (3,), 3)]
    else:
        expected = [("Roman Sentinel", (1, 2), (3,), 2)]
    expected_count = sum(count for _, _, _, count in expected)
    check("All expected glossary link annotations exist", len(links) == expected_count,
          expected=expected_count, observed=len(links))
    used = []
    for term, source_pages, target_pages, count in expected:
        sources = phrase_boxes(boxes, term, source_pages)
        targets = phrase_boxes(boxes, term + ":", target_pages)
        check("Visible glossary-link source count: " + term, len(sources) == count,
              expected=count, observed=len(sources))
        check("Unique visible glossary destination exists: " + term, len(targets) == 1,
              expected=1, observed=len(targets))
        for index, source in enumerate(sources):
            x = (source["xMin"] + source["xMax"]) / 2
            y = boxes[source["page"] - 1]["height"] - (source["yMin"] + source["yMax"]) / 2
            matching = [link for link in links if link["source_page"] == source["page"]
                        and link["rect"][0] <= x <= link["rect"][2]
                        and link["rect"][1] <= y <= link["rect"][3]]
            name = term + " occurrence " + str(index + 1)
            check("Visible source has exactly one glossary link: " + name, len(matching) == 1,
                  expected=1, observed=len(matching))
            if len(matching) != 1 or len(targets) != 1:
                continue
            link = matching[0]
            used.append(link["object"])
            target = link["target"]
            visible = targets[0]
            parameters = target["parameters"]
            valid = (target["view"] == "/XYZ" and len(parameters) == 3
                     and type(parameters[0]) in (int, float) and type(parameters[1]) in (int, float))
            check("Glossary link uses a native XYZ destination: " + name, valid)
            if not valid:
                continue
            top = boxes[target["page"] - 1]["height"] - parameters[1]
            # A block destination sits above its first glyph. Twelve points is
            # narrower than the gap to another entry in these controlled pages.
            aligned = (target["page"] == visible["page"]
                       and abs(parameters[0] - visible["xMin"]) <= 2
                       and 0 <= visible["yMin"] - top <= 12)
            check("Glossary link reaches its own visible definition: " + name, aligned,
                  target=target, visible=visible)
    check("Every expected link was associated with a visible source",
          len(used) == expected_count and len(set(used)) == expected_count,
          expected=expected_count, observed=len(set(used)))


def analyze(specimen, extracted, pdf_pages, native, bounding_boxes, pdf_helpers):
    identifier = specimen["id"]
    raw_pages = extracted.split("\f")
    if raw_pages and not raw_pages[-1].strip():
        raw_pages.pop()
    pages = [normal(page) for page in raw_pages]
    text = " ".join(pages)
    lines = [normal(line) for line in extracted.splitlines() if line.strip()]
    pdf = pdf_helpers["PDF"](native)
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})

    def count(value, expected=1, region=None):
        actual = (text if region is None else region).count(value)
        check("Literal value count: " + value, actual == expected, expected=expected, observed=actual)

    def line(value):
        actual = lines.count(value)
        check("Exact rendered reference line: " + value, actual == 1, expected=1, observed=actual)

    check("PDF and extracted/native page inventories agree",
          pdf_pages == len(pages) == len(pdf.pages) and pdf_pages > 0)
    expected_pages = {
        "abbreviations-table": 1, "abbreviations-first-use": 2,
        "glossary-first-use": 4, "glossary-marked": 3, "glossary-index": 3,
        "index-marked": 3, "index-columns": 3, "index-manual": 1,
        "index-subentries": 1, "index-alias": 2, "pages-abbreviations": 1,
        "pages-combined": 2, "edge-cases-roman": 4, "edge-cases-empty-index": 1,
        "edge-cases-category": 1, "edge-cases-hidden-pages": 1,
    }.get(identifier)
    if expected_pages is not None:
        check("Controlled specimen has the expected page count", pdf_pages == expected_pages,
              expected=expected_pages, observed=pdf_pages)
        if pdf_pages != expected_pages:
            return result(checks)

    if identifier in ("abbreviations-table", "pages-abbreviations", "pages-combined"):
        for term, short, definition in ROWS:
            if identifier == "abbreviations-table":
                count(term + " " + short + " " + definition)
            elif identifier == "pages-abbreviations":
                count(short + " " + term + " " + definition)
            else:
                count(term + " (" + short + "): " + definition)
                count(short + " " + term + ": " + definition)
        for token in ("entry.key", "entry.short", "entry.long", "sorted-abbrevs.map"):
            check("Controlled table contains no literal expression " + token, token not in text)
    if identifier == "abbreviations-table":
        count("Term Abbreviation Definition")
        count("TERM TABLE CONTROL")
    elif identifier == "pages-abbreviations":
        count("Abbreviation Term Definition")
        count("Statistics: 10 total abbreviations")
    elif identifier == "pages-combined":
        count("Glossary and Abbreviations")
        count("Glossary of Terms")
        count("List of Abbreviations")
    elif identifier == "abbreviations-first-use":
        count("TERM FIRST: Machine Learning (ML). TERM SECOND: ML.", region=pages[0])
        count("TERM UNEXPANDED: AI. TERM LATER FIRST: Artificial Intelligence (AI).", region=pages[0])
        count("TERM THIRD: ML.", region=pages[1])
        count("Machine Learning (ML)")
        count("Artificial Intelligence (AI)")
    elif identifier == "glossary-first-use":
        definition = "A reference to a source of information used in a scholarly work."
        count("GLOSS FIRST: Citation (" + definition + ").", region=pages[0])
        count("GLOSS SECOND: Citation.", region=pages[0])
        count("GLOSS THIRD: Citation.", region=pages[1])
        count(definition, region=" ".join(pages[:2]))
        count("Citation: " + definition + " (pp. 1, 2)", region=" ".join(pages[2:]))
    elif identifier == "glossary-marked":
        count("Marked Sentinel Concept on the first page.", region=pages[0])
        count("Repeated Sentinel Concept on the first page.", region=pages[0])
        count("Repeated Sentinel Concept on the second page.", region=pages[1])
        line("Sentinel Concept: SYNTHETIC DEFINITION ALPHA. (pp. 1, 2)")
        check("Repeated markers retain logical page labels", pdf.labels() == ["1", "2", "3"], observed=pdf.labels())
    elif identifier == "glossary-index":
        count("Glossary Index", region=pages[2])
        for term in INDEX_TERMS:
            observed = len(re.findall(r"(?<![A-Za-z])" + re.escape(term) + r"(?![A-Za-z])", pages[2]))
            check("Glossary index has one visible term: " + term, observed == 1, expected=1, observed=observed)
    elif identifier in ("index-marked", "index-columns"):
        count("INDEX FIRST PAGE", region=pages[0])
        count("INDEX SECOND PAGE", region=pages[1])
        count("Synthetic Alpha", 0, region=" ".join(pages[:2]))
        line("Synthetic Alpha — 1-2")
        line("Synthetic Beta")
        line("detail — 2")
    elif identifier == "index-manual":
        line("Synthetic Alpha — 2, 4-6")
        line("Synthetic Beta — 3")
        count("Index Statistics: 2 unique terms, 5 page references.")
    elif identifier == "index-subentries":
        line("Synthetic Alpha")
        line("Detail One — 2, 4-6")
        line("Detail Two — 3")
        count("Index Statistics: 1 unique terms, 5 page references.")
    elif identifier == "index-alias":
        count("INDEX ALIAS FIRST", region=pages[0])
        count("Synthetic Alias", 0, region=pages[0])
        line("Synthetic Alias — 1")
    elif identifier == "edge-cases-roman":
        count("ROMAN FIRST Roman Sentinel", region=pages[0])
        count("ARABIC FIRST Roman Sentinel", region=pages[1])
        line("Roman Sentinel: ROMAN SYNTHETIC DEFINITION. (pp. i, 1)")
        line("Roman Index — i, 1")
        check("Logical references agree with native Roman/Arabic page labels",
              pdf.labels() == ["i", "1", "2", "3"], observed=pdf.labels())
    elif identifier == "edge-cases-empty-index":
        count("No index terms defined. Mark actual locations with index-term(term), or supply explicit manual page references.")
    elif identifier == "edge-cases-category":
        count("CATEGORY ORDER: Zeta Term then Alpha Term")
    elif identifier == "edge-cases-hidden-pages":
        line("Hidden References")
        check("Hidden manual references are not rendered", not re.search(r"\b(?:22|44|45|46)\b", text))
        count("Index Statistics: 1 unique terms, 4 page references.")
    elif identifier == "thesis-index-supplied":
        count("THESIS INDEX BODY SENTINEL.")
        line("THESIS SUPPLIED ALPHA — 2, 4-6")
        count("Index Statistics: 1 unique terms, 4 page references.")
        body_pages = [i + 1 for i, page in enumerate(pages) if "THESIS INDEX BODY SENTINEL." in page]
        indexes = [item for item in pdf.outlines() if item["title"] == "Index"]
        check("Thesis index follows its actual body in the native outline",
              len(body_pages) == len(indexes) == 1 and indexes[0]["target"]["page"] > body_pages[0],
              body_pages=body_pages, index_targets=[item["target"] for item in indexes])
    else:
        raise ValueError("Unknown positive terms specimen: " + identifier)

    if specimen["needs_boxes"]:
        boxes = word_boxes(bounding_boxes)
        check("Glossary bounding boxes cover every PDF page", len(boxes) == pdf_pages)
        if len(boxes) == pdf_pages:
            check_links(identifier, pdf, boxes, check)
    return result(checks)
