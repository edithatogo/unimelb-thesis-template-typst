"""Independent literal-text oracles for the bounded COR-01 fixture corpus.

There are no subprocesses or standalone runner here. scripts/verify.py owns
compilation, PDF checks, time budgets and evidence. Page 1 is the controlled
component region; page 2 deliberately contains valid raw source text.
"""

from __future__ import annotations

import re


EXPECTED_SPECIMEN_COUNT = 14
CREATION_TIMESTAMP = "1794700800"
RAW_CONTROL = 'v.at("citation", default: "")'
SOURCE_FILES = (
    "pages/declaration.typ",
    "pages/preface-helpers.typ",
    "config/publications.typ",
)
FORBIDDEN = {
    "declaration": ("if word_count", "if includes_publications", "if percentage",
                    "if ai_usage", "if third_party_assistance"),
    "contributions": ("r.at(",),
    "publications": ("citation-cell", "status-cell", "consent-cell", "appendix-cell",
                     "set text(", "set par(", "v.at("),
    "footnotes": ("v.at(", "if appendix", "(missing entry)"),
    "appendix-links": ("citation-cell", "status-cell", "consent-cell", "appendix-cell",
                       "publication-appendix-link", "atext", "href:"),
}


def expected_counts(component, variant):
    """Literal fixture requirements; counts include absent-value controls."""
    present = int(variant != "empty")
    multiple = int(variant == "multiple")
    if component == "declaration":
        return {
            "the thesis comprises only my original work towards the Doctor of Philosophy": 1,
            "due acknowledgement has been made in the text to all other material used": 1,
            "Synthetic Candidate": 1,
            "the thesis is 12345 words in length": present,
            "Generative or digital assistance used: Synthetic AI disclosure alpha.": multiple,
            "Third-party human assistance received: Synthetic human disclosure beta.": multiple,
            "creative outputs": 0,
        }
    if component == "contributions":
        return {
            "Name Role Contribution (%)": present,
            "ContribAlpha": present,
            "ContribAlpha Analysis 60": present,
            "ContribBeta": multiple,
            "ContribBeta Validation 40": multiple,
        }
    if component == "publications":
        return {
            "Citation Status Consent": present,
            "CitationAlpha (2026)": present,
            "CitationAlpha (2026) published Yes": present,
            "CitationBeta (2025)": multiple,
            "CitationBeta (2025) accepted No": multiple,
        }
    if component == "footnotes":
        return {
            "Direct note": present + multiple,
            "Chapter note by numeric key.": present,
            "Chapter note by citation key.": present,
            "CitationAlpha (2026)": 3 * present,
            "CitationAlpha (2026) (status: published, consent: yes, appendix: Appendix A)": 3 * present,
            "CitationBeta (2025)": multiple,
            "CitationBeta (2025) (status: accepted, consent: no)": multiple,
        }
    if component == "appendix-links":
        plain = int(variant == "plain")
        return {
            "Citation Status Consent Appendix Ref": 1,
            "CitationGamma (2024)": 1,
            "CitationGamma (2024) published Yes": 1,
            "Appendix A": 1,
            "See Appendix A": plain,
            "#cor01-appendix": 1 - plain,
            "Direct native reference:": 1 - plain,
            "Synthetic appendix destination.": 1,
        }
    raise ValueError(f"Unknown COR-01 component: {component}")


def specimens():
    result = []
    for component in FORBIDDEN:
        variants = ("plain", "label") if component == "appendix-links" else ("empty", "one", "multiple")
        for variant in variants:
            result.append({
                "id": component + "-" + variant,
                "component": component,
                "variant": variant,
                "fixture": "tests/rendered/cor01/" + component + ".typ",
                "inputs": {"case": variant},
                "marker": "COR01 " + component + " " + variant,
                "expected_pages": 2,
                "expected_counts": expected_counts(component, variant),
                "forbidden_tokens": FORBIDDEN[component],
                "enum_items": ({"empty": 2, "one": 3, "multiple": 5}[variant]
                               if component == "declaration" else None),
            })
    return result


def _count(text, value):
    # Footnote numbers can touch the first letter in pdftotext output. Letter
    # boundaries still reject partial words without losing those note values.
    return len(re.findall(r"(?<![A-Za-z])" + re.escape(value) + r"(?![A-Za-z])", text))


def check_text(specimen, extracted, pdf_pages):
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    errors = []
    expected_pages = specimen["expected_pages"]
    if pdf_pages != expected_pages or len(pages) != expected_pages:
        errors.append(f"expected {expected_pages} controlled pages; PDF={pdf_pages}, extracted={len(pages)}")
    region = " ".join(pages[0].split()) if pages else ""
    control = " ".join(pages[1].split()) if len(pages) > 1 else ""
    if _count(region, specimen["marker"]) != 1:
        errors.append("component-region fixture marker is missing or duplicated")
    observations = []
    for value, expected in specimen["expected_counts"].items():
        observed = _count(region, value)
        observations.append({"text": value, "expected_count": expected, "observed_count": observed})
        if observed != expected:
            errors.append(f"text cardinality {observed} != {expected}: {value}")
    for token in specimen["forbidden_tokens"]:
        if token in region:
            errors.append("literal source in component region: " + token)
    enum_numbers = None
    if specimen["enum_items"] is not None:
        enum_numbers = [int(value) for value in re.findall(r"(?m)^\s*([0-9]+)\.\s", pages[0] if pages else "")]
        expected_numbers = list(range(1, specimen["enum_items"] + 1))
        if enum_numbers != expected_numbers:
            errors.append(f"declaration enum items {enum_numbers} != {expected_numbers}")
    if specimen["component"] == "footnotes" and specimen["variant"] != "empty":
        body_end = region.find("Chapter note by citation key.")
        first_note = region.find("CitationAlpha (2026)")
        if body_end < 0 or first_note <= body_end:
            errors.append("publication notes must follow the controlled body text")
    raw_preserved = _count(control, "Raw code control") == 1 and _count(control, RAW_CONTROL) == 1
    if not raw_preserved:
        errors.append("legitimate raw source control on page 2 was lost or duplicated")
    return {
        "scope": "COR-01 controlled component text on page 1",
        "text_counts": observations,
        "enum_numbers": enum_numbers,
        "raw_code_control_preserved": raw_preserved,
        "errors": errors,
    }
