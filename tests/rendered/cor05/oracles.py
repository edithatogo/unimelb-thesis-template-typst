"""Independent optional-section values, applicability, order and privacy controls.

Commands belong to scripts/verify.py. A deliberately identifying blind specimen
must retain a failed public-surface scan; the regression result is not anonymity.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET

CREATION_TIMESTAMP = "1794700800"
SOURCE_FILES = (
    "lib.typ", "config/metadata.typ", "config/optional.typ", "config/review.typ",
    "pages/declaration.typ", "pages/preface.typ", "pages/preface-helpers.typ",
    "pages/funding.typ", "pages/acknowledgements.typ", "pages/title.typ",
    "config/publications.typ", "layouts/document.typ", "frontmatter/preface.typ",
)
SAMPLE_FILES = (
    "examples/samples/sample-ai-disclosure.typ",
    "examples/samples/sample-creative-outputs.typ",
)
PUBLIC_GROUPS = {
    "publications": ("COR05 PUBLICATION ALPHA",),
    "assistance": (
        "COR05 HUMAN ASSISTANCE DESCRIPTION", "COR05 DIGITAL ASSISTANCE DESCRIPTION",
        "COR05 AI ASSISTANCE DESCRIPTION",
    ),
    "prior_work": ("COR05 PRIOR WORK DESCRIPTION", "COR05 PRIOR DEGREE", "COR05 PRIOR INSTITUTION"),
    "funding": ("COR05 FUNDER ALPHA", "COR05 FUNDER BETA", "COR05 GRANT NUMBER", "COR05 FUNDING ACKNOWLEDGEMENT"),
    "creative_outputs": ("COR05 CREATIVE DESCRIPTION",),
}
PRIVATE_TOKENS = (
    "COR05_PRIVATE_ASSISTANCE", "COR05_PRIVATE_APPROVAL", "COR05_PRIVATE_PROMPT",
    "COR05_PRIVATE_OUTPUT", "COR05_CREATIVE_ID", "COR05_CREATIVE_RESOURCE",
)
IDENTITY_TOKENS = (
    "COR05_MANAGED_AUTHOR", "COR05_ASSISTANCE_IDENTITY", "COR05_PRIOR_IDENTITY",
    "COR05_FUNDING_IDENTITY", "COR05_AUTHORED_CREATIVE",
)
NEUTRAL_CREATIVE = "the thesis includes the creative outputs described in the Preface;"
MIGRATION = (
    "Private ai_assistance logs are not a public thesis field. Migrate to assistance "
    "records with kind and description; keep prompts and output logs outside the thesis."
)
PERCENTAGE = "Invalid percentage_dissertation: expected a finite number from 0 to 100."
PAIR = (
    "Invalid creative percentages: supply both percentage_dissertation and "
    "percentage_creative, or neither."
)
IDENTIFIER = "expected an identifier using letters, digits, dot, underscore, colon or hyphen."
REJECTIONS = (
    ("percentages-without-creative", "Invalid creative percentages: creative_outputs must contain at least one record."),
    ("private-argument", MIGRATION),
    ("private-override", MIGRATION),
    ("private-helper", MIGRATION),
    ("private-public-record", "Invalid assistance[0]: unknown field; use only the documented public record fields."),
    ("assistance-missing-kind", "Invalid assistance[0].kind: required public field is missing."),
    ("assistance-unknown-kind", "Invalid assistance[0].kind: expected human, digital or ai."),
    ("assistance-wrong-container", "Invalid assistance: expected an array of public records."),
    ("assistance-wrong-record", "Invalid assistance[0]: expected a public record dictionary."),
    ("funding-missing-funder", "Invalid funding[0].funder: required public field is missing."),
    ("funding-wrong-grant", "Invalid funding[0].grant: expected a nonempty string."),
    ("prior-work-empty-description", "Invalid prior_work[0].description: expected a nonempty string."),
    ("prior-work-invalid-reference", "Invalid prior_work[0].approval_ref: " + IDENTIFIER),
    ("creative-invalid-id", "Invalid creative_outputs[0].id: " + IDENTIFIER),
    ("creative-invalid-proportion", "Invalid creative_outputs[0].proportion: expected a finite number from 0 to 100."),
    ("creative-wrong-resources", "Invalid creative_outputs[0].resource_ids: expected an array of unique identifiers."),
    ("creative-duplicate-resources", "Invalid creative_outputs[0].resource_ids: expected an array of unique identifiers."),
    ("creative-missing-dissertation", PAIR),
    ("creative-missing-creative", PAIR),
    ("creative-boolean-percentage", PERCENTAGE),
    ("creative-negative-percentage", PERCENTAGE),
    ("creative-overflow-percentage", PERCENTAGE),
    ("creative-invalid-total", "Invalid creative percentages: percentage_dissertation and percentage_creative must total 100."),
    ("creative-infinite-percentage", PERCENTAGE),
    ("creative-nan-percentage", PERCENTAGE),
    ("invalid-overridden-layer", "Invalid funding: expected an array of public records."),
)
RENDERED_IDS = (
    "control", "publications-only", "publication-flag-only", "legacy-digital-only",
    "legacy-human-only", "assistance-only", "prior-work-only", "funding-only",
    "creative-only", "creative-proportion", "creative-percentages", "creative-boundaries",
    "creative-fractions", "combined-order", "metadata-overrides", "empty-record-overrides",
    "blind-authored-records", "blind-reviewed-records", "compat-preface",
    "sample-ai-disclosure", "sample-creative-outputs",
)
EXPECTED_SPECIMEN_COUNT = 47
EXPECTED_REJECTION_COUNT = 26


def specimens():
    cases = []
    for identifier in RENDERED_IDS:
        if identifier.startswith("sample-"):
            fixture = "examples/samples/" + identifier + ".typ"
        elif identifier == "compat-preface":
            fixture = "tests/rendered/cor05/compat-preface.typ"
        else:
            fixture = "tests/rendered/cor05/optional-sections.typ"
        cases.append({
            "id": identifier, "fixture": fixture,
            "inputs": {"cor05-case": identifier} if fixture.endswith("optional-sections.typ") else {},
            "expected_error": None,
        })
    cases.extend({
        "id": identifier, "fixture": "tests/rendered/cor05/optional-sections.typ",
        "inputs": {"cor05-case": identifier}, "expected_error": error,
    } for identifier, error in REJECTIONS)
    return cases


def compact(value):
    return "".join(value.replace("\u00ad", "").replace("\u2060", "").split())


def result(checks, **extra):
    errors = [check["name"] for check in checks if not check["passed"]]
    return {"passed": bool(checks) and not errors, "checks": checks, "errors": errors, **extra}


def check_rejection(case, diagnostics, *, exit_code, timed_out, pdf_exists):
    observed = re.findall(r"^error: (.+)$", diagnostics, re.MULTILINE)
    expected = ["panicked with: " + case["expected_error"]]
    return result([
        {"name": "Invalid input exits 1", "passed": exit_code == 1, "observed": exit_code},
        {"name": "Rejection finishes within budget", "passed": timed_out is False},
        {"name": "Only the intended typed or migration diagnostic occurs", "passed": observed == expected,
         "observed": observed, "expected": expected},
        {"name": "Invalid input produces no PDF", "passed": not pdf_exists},
        {"name": "Diagnostic does not interpolate private sentinel values",
         "passed": not any(value in diagnostics for value in PRIVATE_TOKENS)},
    ])


def analyze(case, native, extracted, xmp, diagnostics, pdf_pages):
    identifier = case["id"]
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    if not pages or not isinstance(native.get("pages"), list):
        raise ValueError("Missing PDF page inventory")
    if not isinstance(native.get("qpdf"), list) or len(native["qpdf"]) < 2:
        raise ValueError("Missing native PDF objects")
    if not ET.fromstring(xmp).tag.endswith("xmpmeta"):
        raise ValueError("Missing XMP metadata document")
    text = compact(extracted)
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})

    def count(value, expected=1, region=extracted):
        observed = compact(region).count(compact(value))
        check("Literal count: " + value, observed == expected, observed=observed, expected=expected)

    def heading_pages(title):
        return [index + 1 for index, page in enumerate(pages)
                if " ".join(page.split()).startswith(title + " ")]

    sections = {title: heading_pages(title) for title in ("Preface", "Funding", "Acknowledgements", "Declaration", "Table of Contents")}
    check("PDF and extracted page inventories agree", len(pages) == len(native["pages"]) == pdf_pages)
    public_surfaces = {"visible": extracted, "native": json.dumps(native, ensure_ascii=False), "xmp": xmp}
    private_hits = [{"surface": name, "token": value}
                    for name, value_text in public_surfaces.items() for value in PRIVATE_TOKENS
                    if compact(value) in compact(value_text)]
    check("Private bookkeeping references and prompt values are absent from PDF surfaces", not private_hits,
          observed=private_hits)
    count("as agreed by the advisory committee", 0)
    count("Publications (demo)", 0)
    count("This chapter refers to an associated publication.", 0)
    count("COR05 BASE REPLACED DESCRIPTION", 0)

    groups = set()
    if identifier == "publications-only":
        groups.add("publications")
    for suffix, group in (("assistance-only", "assistance"), ("prior-work-only", "prior_work"), ("funding-only", "funding")):
        if identifier == suffix:
            groups.add(group)
    if identifier.startswith("creative-"):
        groups.add("creative_outputs")
    if identifier == "combined-order":
        groups.update(PUBLIC_GROUPS)
    if identifier == "metadata-overrides":
        groups.update(set(PUBLIC_GROUPS) - {"publications"})
    for group, values in PUBLIC_GROUPS.items():
        for value in values:
            count(value, 1 if group in groups else 0)

    expected_preface = bool(groups - {"funding"}) or identifier.startswith("blind-") or identifier in (
        "compat-preface", "sample-ai-disclosure", "sample-creative-outputs",
    )
    expected_funding = "funding" in groups or identifier.startswith("blind-")
    check("Preface activates exactly for populated public preface inputs",
          len(sections["Preface"]) == int(expected_preface), observed=sections["Preface"])
    check("Funding uses its own optional page", len(sections["Funding"]) == int(expected_funding),
          observed=sections["Funding"])
    check("Acknowledgements remain an independent optional page",
          len(sections["Acknowledgements"]) == int(identifier == "combined-order"),
          observed=sections["Acknowledgements"])
    if expected_preface and expected_funding:
        check("Preface precedes funding", sections["Preface"] and sections["Funding"]
              and sections["Preface"][0] < sections["Funding"][0])
    if identifier == "combined-order":
        check("Funding precedes other acknowledgements", sections["Funding"] and sections["Acknowledgements"]
              and sections["Funding"][0] < sections["Acknowledgements"][0])
        count("COR05 PREFACE BODY CONTROL.")
        count("COR05 ACKNOWLEDGEMENTS BODY CONTROL.")
    for group in groups:
        section = "Funding" if group == "funding" else "Preface"
        start = sections[section][0] if sections[section] else 0
        later = [page for positions in sections.values() for page in positions if page > start]
        end = min(later) if later else len(pages) + 1
        region = "\n".join(pages[start - 1:end - 1]) if start else ""
        check("Values are rendered in their intended " + section + " region: " + group,
              all(compact(value) in compact(region) for value in PUBLIC_GROUPS[group]))

    # Read the native outline independently of the printed contents listing.
    bookmarks = []

    def walk(entries):
        for entry in entries:
            bookmarks.append((entry["title"], entry["destpageposfrom1"]))
            walk(entry["kids"])

    walk(native["outlines"])
    register_destinations = [page for name, page in bookmarks if name == "Publication Register"]
    check("Exactly one real publication register is emitted when records exist",
          len(register_destinations) == int("publications" in groups), observed=register_destinations)
    for title in ("Preface", "Funding", "Acknowledgements"):
        destinations = [page for name, page in bookmarks if name == title]
        check("Native bookmark targets the actual " + title + " page",
              destinations == sections[title], observed=destinations, expected=sections[title])

    creative = "creative_outputs" in groups or identifier.startswith("blind-") or identifier == "sample-creative-outputs"
    percentages = {
        "creative-percentages": ("70", "30"), "creative-boundaries": ("0", "100"),
        "creative-fractions": ("70.5", "29.5"), "sample-creative-outputs": ("70", "30"),
    }
    count(NEUTRAL_CREATIVE, int(creative and identifier not in percentages))
    ratio_phrase = "the thesis comprises "
    observed_ratios = re.findall(r"thethesiscomprises[0-9.]+%dissertationand[0-9.]+%creativeoutputs;", text)
    if identifier in percentages:
        dissertation, creative_share = percentages[identifier]
        expected_ratio = f"{ratio_phrase}{dissertation}% dissertation and {creative_share}% creative outputs;"
        count(expected_ratio)
        check("Only the explicitly supplied aggregate pair is rendered", observed_ratios == [compact(expected_ratio)])
    else:
        check("No aggregate creative percentage is inferred", observed_ratios == [], observed=observed_ratios)
    count("Declared record proportion: 30%.", int(identifier == "creative-proportion"))
    count("COR05 LEGACY DIGITAL SUMMARY", int(identifier == "legacy-digital-only"))
    count("COR05 LEGACY HUMAN SUMMARY", int(identifier == "legacy-human-only"))
    if identifier not in ("compat-preface", "sample-ai-disclosure", "sample-creative-outputs"):
        count("COR05 MAIN BODY CONTROL.")
        count("COR05 ABSTRACT CONTROL.")
        declaration = "\n".join(pages[page - 1] for page in sections["Declaration"])
        enumerated = re.findall(r"^\s*([0-9]+)\. ", declaration, re.MULTILINE)
        expected_count = 3 + int(creative) + int(identifier.startswith("legacy-"))
        check("Declaration has only applicable numbered clauses",
              enumerated == [str(index) for index in range(1, expected_count + 1)], observed=enumerated)
    if identifier == "compat-preface":
        count("COR05 COMPAT PREFACE BODY.")
        count("COR05 COMPAT ASSISTANCE")
    elif identifier == "sample-ai-disclosure":
        for value in (
            "Synthetic example: a colleague commented on the structure of a draft.",
            "Synthetic example: a spelling checker suggested corrections.",
            "Synthetic example: an AI tool suggested alternative wording for author review.",
        ):
            count(value)
    elif identifier == "sample-creative-outputs":
        count("Synthetic creative example: a short video exploring patterns of light.")

    scan = None
    if identifier.startswith("blind-"):
        hits = [{"surface": name, "token": value}
                for name, value_text in public_surfaces.items() for value in IDENTITY_TOKENS
                if compact(value) in compact(value_text)]
        expected_clean = identifier == "blind-reviewed-records"
        scan = {"result": "fail" if hits else "pass", "passed": not hits, "hits": hits,
                "scope": "Declared optional-record identity sentinels across visible/native/XMP surfaces",
                "reviewer_ready_certified": False}
        check("Blind known-identifier scan has its explicit expected outcome", scan["passed"] is expected_clean,
              expected=expected_clean, observed=scan["passed"])
        check("Managed author is removed without erasing authored records",
              not any(hit["token"] == "COR05_MANAGED_AUTHOR" for hit in hits))
        if not expected_clean:
            check("Each authored optional identity remains a detected residual",
                  {hit["token"] for hit in hits if hit["surface"] == "visible"} == set(IDENTITY_TOKENS[1:]))
        notices = diagnostics[0].get("diagnostics", []) if isinstance(diagnostics, list) and len(diagnostics) == 1 else []
        fields = notices[0].get("fields", []) if len(notices) == 1 else []
        check("Static blind diagnostic explicitly includes new author-reviewed fields",
              len(notices) == 1 and notices[0].get("code") == "author-review-required"
              and {"assistance.description", "prior_work", "funding", "creative_outputs.description"} <= set(fields))
        check("Blind diagnostic contains no original private or identity sentinels",
              not any(value in json.dumps(diagnostics) for value in PRIVATE_TOKENS + IDENTITY_TOKENS))
        count("Author review required:", region=pages[0])
    return result(checks, section_pages=sections, public_surface_scan=scan,
                  reviewer_ready_certified=False, policy_or_approval_certified=False)
