"""Independent metadata, order and rejection assertions for the Typst adapter.

Canonical fixtures specify configuration semantics only. The visible metadata
and section-order expectations in expectations.json are additional local
controls; they are not an assertion of cross-engine or institutional acceptance.
"""
from __future__ import annotations

import hashlib
import json
import re

EXPECTED_IDS = (
    "bad-month", "bad-orcid", "blind-draft", "blind-examination", "cli-false",
    "doctoral-monograph", "draft-minimal", "incompatible-pdf", "joint-resubmission",
    "masters-publication", "missing-final-title", "missing-language-approval",
    "non-english-creative", "placeholder-final-title", "print-explicit-false",
    "public-deposit-input", "string-boolean", "unknown-field",
    "precedence-layers", "print-profile-default", "literal-markup",
)
CONTRACT_PIN = "338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c"
FIXTURE_MANIFEST_PIN = "af82359a786b2be565e49de594e32a5d2edb3354221dfd5371d5d954b33c5757"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def normal(value):
    return " ".join(value.split())


def analyze(case, fixture, report, output_files, pdf_helper, text=None, native=None, bbox=None):
    result = {"id": case["id"], "scope": "bounded-adapter-native-semantics", "passed": False,
              "checks": [], "errors": [], "observed": {}}

    def check(name, observed, expected):
        passed = canonical(observed) == canonical(expected)
        result["checks"].append({"name": name, "passed": passed, "observed": observed, "expected": expected})
        if not passed:
            result["errors"].append(name)

    try:
        check("Exact canonical contract digest", report["contract_sha256"], CONTRACT_PIN)
        check("Exact shared fixture-manifest digest", report["fixture_manifest_sha256"], FIXTURE_MANIFEST_PIN)
        check("Native slice does not assert an uncollected source revision", report["source_revision"], None)
        check("Source identity is explicitly content-bound and revision uncollected",
              [report["source_kind"], report["source_revision_status"]],
              ["content-hash-bound-native-slice", "uncollected"])
        check("Contract acceptance remains blocked", report["contract_acceptance"],
              "blocked-pending-adapter-registration-and-qualified-source")
        check("LaTeX execution remains unexecuted", report["latex_execution"], "unexecuted")
        check("Institutional approval remains unverified", report["institutional_approval"], "unverified")
        check("Adapter sources unchanged", report["sources_unchanged"], True)
        if fixture is not None:
            check("Exact canonical fixture binding", report["fixture"],
                  {"id": case["id"], "sha256": case["fixture_sha256"]})
        if case["outcome"] == "invalid":
            check("Invalid fixture rejected", report["result"], "rejected")
            check("Native invalid-input exit", report["exit_code"], 1)
            check("Intended validation diagnostic", report.get("error_code"), case["error_code"])
            check("No normalized invalid configuration", report["normalized_configuration"], None)
            check("Invalid configuration has no digest", report["configuration_sha256"], None)
            check("No compiler or PDF tools run for invalid input", report["commands"], [])
            check("Rejected input has no PDF", "document.pdf" in output_files, False)
            check("Rejected input has no old prepared configuration", "input.json" in output_files, False)
        else:
            config = report["normalized_configuration"]
            check("Typed normalization succeeded", report["normalization"], "valid")
            check("Normalized configuration hash is actual", report["configuration_sha256"],
                  hashlib.sha256(canonical(config).encode()).hexdigest())
            if fixture is not None:
                for path, expected in fixture["expected"]["values"].items():
                    value = config
                    for part in path.split("."):
                        value = value[part]
                    check("Shared fixture semantic value: " + path, value, expected)
                check("Shared fixture diagnostic codes", sorted({d["code"] for d in report["diagnostics"]}),
                      sorted(fixture["expected"]["diagnostic_codes"]))
            if case["outcome"] == "unsupported":
                check("Valid unsupported input is distinct from rejection", report["result"], "unsupported")
                check("Unsupported native exit", report["exit_code"], 2)
                check("Exact unsupported fields are disclosed", report["unsupported_paths"], case["unsupported_paths"])
                check("Unsupported fields are not silently rendered", report["rendering"], "unsupported")
                check("No compiler or PDF tools run for unsupported input", report["commands"], [])
                check("Unsupported input has no PDF", "document.pdf" in output_files, False)
                check("Unsupported input has no old prepared configuration", "input.json" in output_files, False)
            else:
                check("Supported input actually rendered", report["result"], "rendered")
                check("Native supported exit", report["exit_code"], 0)
                check("Actual document is retained", "document.pdf" in output_files, True)
                check("No unsupported field is hidden", report["unsupported_paths"], [])
                check("Actual compiler matches the qualified native fixture version",
                      report["tool_versions"]["typst"].split()[:2], ["typst", "0.15.1"])
                check("Compiler manifest is bound to the source snapshot",
                      report["typst_manifest_sha256"], report["source_sha256_before"]["typst.toml"])
                expected = case["render"]
                check("Selected profile reaches prepared configuration", config["layout"], expected["profile"])
                check("Typed duplex reaches prepared configuration", config["double_sided"], expected["double_sided"])
                pdf = pdf_helper["PDF"](native)
                pages = text.split("\f")
                if pages and not pages[-1].strip():
                    pages.pop()
                lines = [[normal(line) for line in page.splitlines() if line.strip()] for page in pages]
                boxes = pdf_helper["bbox_pages"](bbox)
                check("Native PDF and text page counts agree", len(pdf.pages), len(pages))
                check("Native PDF and bounding-box counts agree", len(pdf.pages), len(boxes))
                info = pdf.resolve(pdf.objects["trailer"]["value"]["/Info"])
                native_title = pdf_helper["pdf_string"](info["/Title"])
                native_author = pdf_helper["pdf_string"](info["/Author"])
                check("Native PDF title metadata", native_title, expected["title"])
                check("Native PDF author metadata", native_author, expected["author"])
                title_fields = [expected["title"], expected["author"]]
                if expected["orcid"] is not None:
                    title_fields.append("ORCID: " + expected["orcid"])
                else:
                    check("Absent ORCID is not fabricated", any(line.startswith("ORCID:") for line in lines[0]), False)
                title_fields.extend([expected["course"], *expected["academic_units"], "Submission month: " + expected["month"]])
                indexes = []
                for field in title_fields:
                    check("Title page contains exact field: " + field, lines[0].count(field), 1)
                    indexes.append(lines[0].index(field) if field in lines[0] else -1)
                check("Title metadata occurs in the declared local order", all(a < b for a, b in zip(indexes, indexes[1:])), True)

                def unique_line_page(line):
                    found = [index + 1 for index, values in enumerate(lines) if values.count(line) == 1]
                    check("Unique visible line: " + line, len(found), 1)
                    return found[0] if len(found) == 1 else None

                declaration_page = unique_line_page("Declaration")
                contents_page = unique_line_page("Table of Contents")
                alpha_page = unique_line_page("ADAPTER ALPHA BODY")
                beta_page = unique_line_page("ADAPTER BETA BODY")
                sections = [("title", 1)]
                headings = []
                if expected["abstract"] is not None:
                    abstract_page = unique_line_page(expected["abstract"])
                    check("Abstract heading belongs to its body page", "Abstract" in lines[abstract_page - 1], True)
                    sections.append(("abstract", abstract_page))
                    headings.append(("Abstract", 1, abstract_page))
                else:
                    check("Absent abstract is not fabricated", any("Abstract" == line for values in lines for line in values), False)
                sections.extend([("declaration", declaration_page), ("contents", contents_page), ("body", alpha_page)])
                check("Local matter sequence is physically ordered", all(a[1] < b[1] for a, b in zip(sections, sections[1:])), True)
                word_line = "Word count not supplied." if expected["word_count"] is None else f"Word count: {expected['word_count']}."
                check("Declaration preserves supplied or missing word count", word_line in lines[declaration_page - 1], True)
                original_line = ("Original work declaration not supplied." if expected["word_count"] is None
                                 else "The author declares that the thesis contains their original work.")
                check("Declaration preserves supplied or missing attestation", original_line in lines[declaration_page - 1], True)
                check("Duplex setting changes actual chapter-page placement", beta_page - alpha_page,
                      2 if expected["double_sided"] else 1)
                if expected["double_sided"]:
                    check("Duplex chapters occupy physical recto pages", [alpha_page % 2, beta_page % 2], [1, 1])
                headings.extend([("Declaration", 1, declaration_page), ("Table of Contents", 1, contents_page),
                                 ("1 ADAPTER CHAPTER ALPHA", 1, alpha_page),
                                 ("1.1 ADAPTER ALPHA SECTION", 2, alpha_page),
                                 ("2 ADAPTER CHAPTER BETA", 1, beta_page)])
                outlines = pdf.outlines()
                check("Exact native heading order, nesting and page destinations",
                      [[row["title"], row["depth"], row["target"]["page"]] for row in outlines],
                      [list(row) for row in headings])
                for row in outlines:
                    target = row["target"]
                    box = boxes[target["page"] - 1]
                    matches = [line for line in box["lines"] if line["text"] == row["title"]]
                    check("Unique visible native bookmark heading: " + row["title"], len(matches), 1)
                    good = False
                    if len(matches) == 1 and target["view"] == "/XYZ" and len(target["parameters"]) == 3:
                        x, y = target["parameters"][:2]
                        line = matches[0]
                        good = abs(x - line["xMin"]) <= 2 and -2 <= line["yMin"] - (box["height"] - y) <= 12
                    check("Native bookmark targets its own visible heading: " + row["title"], good, True)
                toc_links = [link for link in pdf.links() if link["source_page"] == contents_page]
                expected_toc = [row for row in outlines if row["title"] != "Table of Contents"]
                check("All expected contents links exist", len(toc_links), len(expected_toc))
                for row in expected_toc:
                    candidates = [line for line in boxes[contents_page - 1]["lines"] if line["text"].startswith(row["title"] + " ")]
                    check("Unique visible contents row: " + row["title"], len(candidates), 1)
                    matches = []
                    if len(candidates) == 1:
                        line = candidates[0]
                        for link in toc_links:
                            rect = link["rect"]
                            center_y = boxes[contents_page - 1]["height"] - (rect[1] + rect[3]) / 2
                            if line["yMin"] - 2 <= center_y <= line["yMax"] + 2:
                                matches.append(link)
                    check("Contents row owns one native link: " + row["title"], len(matches), 1)
                    check("Contents link reaches its own heading: " + row["title"],
                          matches[0]["target"] if len(matches) == 1 else None, row["target"])
                labels = pdf.labels()
                check("Every front page, including duplex alignment, keeps Roman labels", labels[:alpha_page - 1],
                      [pdf_helper["roman"](n).lower() for n in range(1, alpha_page)])
                check("Core labels start at one and continue through all pages", labels[alpha_page - 1:],
                      [str(n) for n in range(1, len(pdf.pages) - alpha_page + 2)])
                for row in expected_toc:
                    source = [line["text"] for line in boxes[contents_page - 1]["lines"] if line["text"].startswith(row["title"] + " ")]
                    expected_label = labels[row["target"]["page"] - 1]
                    check("Contents row displays the target logical page: " + row["title"],
                          len(source) == 1 and re.search(r"(?:\s|\u2060)" + re.escape(expected_label) + r"$", source[0]) is not None, True)
                result["observed"] = {"title": native_title, "author": native_author,
                                      "matter_sequence": [name for name, _ in sections],
                                      "section_pages": dict(sections), "page_labels": labels,
                                      "headings": outlines, "chapter_page_gap": beta_page - alpha_page}
        result["passed"] = not result["errors"]
    except Exception as exc:
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    return result
