"""Independent PDF order, labels, destinations and margin expectations."""

import xml.etree.ElementTree as ET

CREATION_TIMESTAMP = "1794700800"
EXPECTED_SPECIMEN_COUNT = 9
SOURCE_FILES = ("lib.typ", "layouts/document.typ", "pages/appendix.typ", "pages/front-matter.typ")
RESOURCE_FILES = ("tests/rendered/layout-order/references.bib",)


def specimens():
    values = [
        {"id": p, "profile": p, "case": "control", "fixture": "thesis.typ", "duplex": p == "print"}
        for p in ("default", "draft", "screen", "print")
    ] + [
        {"id": "default-double", "profile": "default", "case": "double-true", "fixture": "thesis.typ", "duplex": True},
        {"id": "print-single", "profile": "print", "case": "double-false", "fixture": "thesis.typ", "duplex": False},
        {"id": "no-bibliography", "profile": "default", "case": "no-bibliography", "fixture": "thesis.typ", "duplex": False},
        {"id": "custom-title", "profile": "default", "case": "control", "fixture": "custom-bibliography.typ", "duplex": False},
        {"id": "direct-appendix", "profile": "screen", "case": "control", "fixture": "direct-appendix.typ", "duplex": False},
    ]
    for value in values:
        value["fixture"] = "tests/rendered/layout-order/" + value["fixture"]
    return values


def check_native(case, extracted, page_count, pdf, bbox, roman):
    pages = extracted.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    pages = [" ".join(page.split()) for page in pages]
    text = " ".join(pages)
    boxes = [x for x in ET.fromstring(bbox).iter() if x.tag.rsplit("}", 1)[-1] == "page"]
    outlines = pdf.outlines()
    labels = pdf.labels()
    checks = []

    def check(name, passed, **details):
        checks.append({"name": name, "passed": bool(passed), **details})

    check("Text, native pages, labels and bounding boxes describe the same PDF",
          page_count > 0 and len(pages) == len(pdf.pages) == len(labels) == len(boxes) == page_count)
    check("Every page is A4", all(
        abs(float(p.get("width")) - 595.2756) < 0.1 and
        abs(float(p.get("height")) - 841.8898) < 0.1 for p in boxes))

    def marker_page(marker):
        found = [index + 1 for index, page in enumerate(pages) if marker in page]
        check("Unique visible body marker: " + marker, len(found) == 1 and text.count(marker) == 1,
              observed_pages=found)
        if len(found) != 1:
            raise ValueError("Missing or duplicated body marker: " + marker)
        return found[0]

    def outline(title, target):
        found = [x for x in outlines if x["title"] == title]
        check("One native bookmark reaches its actual body: " + title,
              len(found) == 1 and found[0]["target"]["page"] == target,
              expected_page=target, observed_pages=[x["target"]["page"] for x in found])

    def boundaries(prefix):
        for side in ("LEFT", "RIGHT"):
            found = []
            for index, page in enumerate(boxes):
                words = [x for x in page.iter() if x.tag.rsplit("}", 1)[-1] == "word"]
                for offset in range(len(words) - 2):
                    triple = words[offset:offset + 3]
                    if [w.text for w in triple] == [prefix, side, "BOUNDARY"]:
                        distance = float(triple[0].get("xMin")) if side == "LEFT" else (
                            float(page.get("width")) - float(triple[-1].get("xMax")))
                        found.append({"page": index + 1, "distance_pt": distance})
            check(prefix + " " + side + " controlled content boundary is 30 mm",
                  len(found) == 1 and abs(found[0]["distance_pt"] - 30 * 72 / 25.4) < 0.1,
                  observed=found)

    if case["id"] == "custom-title":
        reference = marker_page("LAYOUT BIBLIOGRAPHY RECORD")
        outline("LAYOUT CUSTOM REFERENCES", reference)
        check("Exactly one visible custom bibliography heading", text.count("LAYOUT CUSTOM REFERENCES") == 1)
        check("The default heading is absent from text and bookmarks",
              "Bibliography" not in text and all(x["title"] != "Bibliography" for x in outlines))
        check("The controlled citation resolves", "LAYOUT STANDALONE CITATION [1]" in text)
    elif case["id"] == "direct-appendix":
        target = marker_page("LAYOUT DIRECT APPENDIX BODY")
        outline("Appendix A: LAYOUT DIRECT APPENDIX", target)
        boundaries("APPENDIX")
    else:
        first = marker_page("LAYOUT FIRST CHAPTER BODY")
        second = marker_page("LAYOUT SECOND CHAPTER BODY")
        appendix = marker_page("LAYOUT APPENDIX BODY")
        check("Core chapters precede the appendix", first < second < appendix)
        check("The first chapter has logical page 1", labels[first - 1] == "1", observed=labels[first - 1])
        check("Arabic labels continue through the final appendix page",
              labels[first - 1:] == [str(i) for i in range(1, page_count - first + 2)], observed=labels[first - 1:])
        check("All preceding pages retain continuous Roman labels",
              labels[:first - 1] == [roman(i).lower() for i in range(1, first)], observed=labels[:first - 1])
        check("The explicit duplex choice sets the chapter gap", second - first == (2 if case["duplex"] else 1))
        check("Duplex core chapters start on odd physical pages",
              not case["duplex"] or first % 2 == second % 2 == 1)
        front = [x["target"]["page"] for x in outlines if x["title"] == "List of Algorithms"]
        expected_first = (front[0] + (2 if case["duplex"] and front[0] % 2 == 1 else 1)) if len(front) == 1 else None
        check("The first core page needs no surplus alignment pages", first == expected_first, observed=first, expected=expected_first)
        outline("1 LAYOUT CHAPTER ALPHA", first)
        outline("2 LAYOUT CHAPTER BETA", second)
        outline("Appendix A: LAYOUT APPENDIX", appendix)
        outline("A.1 LAYOUT APPENDIX SECTION", appendix)
        if case["id"] == "no-bibliography":
            check("Disabled bibliography has no record or heading",
                  "LAYOUT BIBLIOGRAPHY RECORD" not in text and all(x["title"] != "Bibliography" for x in outlines))
        else:
            bibliography = marker_page("LAYOUT BIBLIOGRAPHY RECORD")
            check("The bibliography is after core chapters and before appendices", second < bibliography < appendix)
            outline("Bibliography", bibliography)
            check("The bibliography body has exactly one heading", pages[bibliography - 1].count("Bibliography") == 1)
            check("The controlled citation resolves", "LAYOUT CITATION [1]" in text)
        boundaries("CORE")
        boundaries("APPENDIX")
    return {"checks": checks, "errors": [x["name"] for x in checks if not x["passed"]]}
