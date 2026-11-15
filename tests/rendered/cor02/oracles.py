#!/usr/bin/env python3
"""Independent bounded COR-02 PDF navigation and appendix-content oracles.

The canonical verifier supplies PDF-native JSON, text and bounding boxes.
This helper does not launch commands or derive expectations from template code.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


EXPECTED_SPECIMENS = ("navigation", "appendix-pages", "appendix-layout")
CREATION_TIMESTAMP = "1794700800"
SOURCE_FILES = ("lib.typ", "pages/front-matter.typ", "layouts/document.typ",
                "pages/appendix.typ", "config/appendix.typ")


HEADINGS = (
    ("1 NAV CHAPTER ALPHA", "NAV CHAPTER ALPHA BODY", 1),
    ("1.1 NAV SECTION ALPHA", "Section alpha content.", 2),
    ("1.1.1 NAV DETAIL ALPHA", "Detail alpha content.", 3),
    ("2 NAV CHAPTER BETA", "NAV CHAPTER BETA BODY", 1),
    ("2.1 NAV SECTION BETA", "Section beta content.", 2),
    ("Appendix A: NAV APPENDIX ALPHA", "NAV APPENDIX ALPHA BODY", 1),
    ("A.1 NAV APPENDIX ALPHA SECTION", "Appendix alpha subsection content.", 2),
    ("Appendix B: NAV APPENDIX BETA", "NAV APPENDIX BETA BODY", 1),
    ("B.1 NAV APPENDIX BETA SECTION", "Appendix beta subsection content.", 2),
)
CREATIVE_ROWS = (
    ("Medium", "NAV SYNTHETIC VIDEO"),
    ("Dimensions", "1920 by 1080 pixels"),
    ("Duration", "00:02:30"),
    ("Description", "NAV CREATIVE DESCRIPTION SENTINEL"),
)


def normal(text):
    return " ".join(text.split())


def roman(number):
    result = []
    for value, letters in ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                           (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                           (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")):
        count, number = divmod(number, value)
        result.append(letters * count)
    return "".join(result)


def pdf_string(value):
    if not isinstance(value, str) or not value.startswith("u:"):
        raise ValueError("Expected qpdf's Unicode string encoding in this fixture")
    return value[2:]


class PDF:
    def __init__(self, payload):
        if payload.get("version") != 2:
            raise ValueError("This prototype requires qpdf JSON version 2")
        self.data = payload
        self.objects = {}
        for chunk in payload["qpdf"][1:]:
            self.objects.update(chunk)
        self.pages = payload["pages"]
        self.page_numbers = {page["object"]: index + 1
                             for index, page in enumerate(self.pages)}
        if len(self.page_numbers) != len(self.pages):
            raise ValueError("Duplicate PDF page object")
        if [page["pageposfrom1"] for page in self.pages] != list(range(1, len(self.pages) + 1)):
            raise ValueError("Nonsequential qpdf physical page positions")
        catalog = self.resolve(self.objects["trailer"]["value"]["/Root"])
        self.named_destinations = {}

        def names(node, depth=0):
            if depth > 16:
                raise ValueError("Excessive destination name-tree nesting")
            node = self.resolve(node)
            pairs = self.resolve(node.get("/Names", []))
            if len(pairs) % 2:
                raise ValueError("Malformed PDF destination name tree")
            for index in range(0, len(pairs), 2):
                if pairs[index] in self.named_destinations:
                    raise ValueError("Duplicate PDF named destination")
                self.named_destinations[pairs[index]] = pairs[index + 1]
            for child in self.resolve(node.get("/Kids", [])):
                names(child, depth + 1)

        names(self.resolve(catalog.get("/Names", {})).get("/Dests", {}))
        self.named_destinations.update(self.resolve(catalog.get("/Dests", {})))

    def resolve(self, value):
        seen = set()
        while isinstance(value, str) and re.fullmatch(r"\d+ \d+ R", value):
            if value in seen or len(seen) >= 32:
                raise ValueError("Cyclic or excessive indirect PDF references")
            seen.add(value)
            value = self.objects["obj:" + value]["value"]
        return value

    def destination(self, value):
        value = self.resolve(value)
        seen = set()
        while isinstance(value, str) and value in self.named_destinations:
            if value in seen or len(seen) >= 16:
                raise ValueError("Cyclic PDF named destination")
            seen.add(value)
            value = self.resolve(self.named_destinations[value])
        if isinstance(value, dict) and "/D" in value:
            value = self.resolve(value["/D"])
        if not isinstance(value, list) or len(value) < 2:
            raise ValueError("Unsupported or absent PDF destination; no target inferred")
        if value[0] not in self.page_numbers:
            raise ValueError("Destination is not a page in this PDF")
        return {"page": self.page_numbers[value[0]], "page_object": value[0],
                "view": value[1], "parameters": value[2:]}

    def outlines(self):
        result = []

        def walk(entries, depth):
            if depth > 16:
                raise ValueError("Excessive outline nesting")
            for entry in entries:
                target = self.destination(entry["dest"])
                if target["page"] != entry["destpageposfrom1"]:
                    raise ValueError("Outline target disagrees with resolved page object")
                result.append({"title": normal(entry["title"]), "depth": depth,
                               "object": entry["object"], "target": target})
                walk(entry["kids"], depth + 1)

        walk(self.data["outlines"], 1)
        return result

    def labels(self):
        ranges = self.data["pagelabels"]
        if not ranges:
            return [str(index + 1) for index in range(len(self.pages))]
        indexes = [entry["index"] for entry in ranges]
        if (any(type(index) is not int for index in indexes)
                or indexes != sorted(set(indexes)) or indexes[0] != 0
                or indexes[-1] >= len(self.pages)):
            raise ValueError("Invalid PDF page-label ranges")
        result = []
        active = 0
        for index in range(len(self.pages)):
            if active + 1 < len(ranges) and ranges[active + 1]["index"] <= index:
                active += 1
            entry = ranges[active]
            label = self.resolve(entry["label"])
            start = label.get("/St", 1)
            if type(start) is not int or start < 1:
                raise ValueError("Invalid PDF page-label start")
            value = start + index - entry["index"]
            style = label.get("/S")
            if style == "/D":
                suffix = str(value)
            elif style in ("/r", "/R"):
                suffix = roman(value)
                if style == "/r":
                    suffix = suffix.lower()
            elif style in ("/a", "/A"):
                suffix = chr(65 + (value - 1) % 26) * ((value - 1) // 26 + 1)
                if style == "/a":
                    suffix = suffix.lower()
            elif style is None:
                suffix = ""
            else:
                raise ValueError("Unsupported PDF page-label style")
            result.append((pdf_string(label["/P"]) if "/P" in label else "") + suffix)
        return result

    def links(self):
        result = []
        for page in self.pages:
            value = self.resolve(page["object"])
            for item in self.resolve(value.get("/Annots", [])):
                annotation = self.resolve(item)
                if annotation.get("/Subtype") != "/Link":
                    continue
                destination = annotation.get("/Dest")
                if destination is None:
                    action = self.resolve(annotation.get("/A", {}))
                    if action.get("/S") != "/GoTo":
                        continue
                    destination = action.get("/D")
                result.append({"source_page": page["pageposfrom1"], "object": item,
                               "rect": self.resolve(annotation["/Rect"]),
                               "target": self.destination(destination)})
        return result


def bbox_pages(source):
    if source is None:
        return None
    root = ET.fromstring(source)
    result = []
    for page in root.findall(".//{*}page"):
        result.append({"height": float(page.attrib["height"]), "lines": [
            {"text": normal(" ".join("".join(word.itertext()) for word in line.findall("{*}word"))),
             **{key: float(line.attrib[key]) for key in ("xMin", "xMax", "yMin", "yMax")}}
            for line in page.findall(".//{*}line")]})
    return result


def analyze(payload, extracted_text, specimen, bounding_boxes=None):
    report = {"scope": "COR-02 bounded synthetic PDF navigation prototype",
              "specimen": specimen, "passed": False, "checks": [], "errors": []}

    def check(name, observed, expected):
        passed = observed == expected
        report["checks"].append({"name": name, "passed": passed,
                                 "observed": observed, "expected": expected})
        if not passed:
            report["errors"].append(name)

    try:
        pdf = PDF(payload)
        pages = extracted_text.split("\f")
        if pages and not pages[-1].strip():
            pages.pop()
        text = [normal(page) for page in pages]
        boxes = bbox_pages(bounding_boxes)
        check("PDF and extracted text page counts", len(pages), len(pdf.pages))
        if boxes is not None:
            check("PDF and bounding-box page counts", len(boxes), len(pdf.pages))
        labels, outlines, links = pdf.labels(), pdf.outlines(), pdf.links()
        report["observed"] = {"logical_labels": labels, "outlines": outlines, "links": links}

        def marker_page(marker):
            found = [index + 1 for index, page in enumerate(text) if marker in page]
            check("Unique body sentinel: " + marker, len(found), 1)
            return found[0] if len(found) == 1 else None

        def source_pages(title):
            return [index + 1 for index, page in enumerate(pages)
                    if any(normal(line) == title for line in page.splitlines())]

        def target_near_title(target, title, target_page, name):
            if boxes is None or target_page is None:
                return
            matches = [line for line in boxes[target_page - 1]["lines"] if line["text"] == title]
            check(name + " unique target heading line", len(matches), 1)
            if len(matches) != 1:
                return
            params = target["parameters"]
            usable = target["view"] == "/XYZ" and len(params) >= 2 and isinstance(params[1], (int, float))
            check(name + " explicit XYZ destination", usable, True)
            if usable:
                destination_top = boxes[target_page - 1]["height"] - params[1]
                # Controlled fixture headings place their native anchor just above
                # the glyph box. A 24-point window detects same-page mis-targets.
                delta = matches[0]["yMin"] - destination_top
                check(name + " destination at heading", -1 <= delta <= 24, True)

        def links_for_line(page_number, line):
            height = boxes[page_number - 1]["height"]
            selected = []
            for link in links:
                if link["source_page"] != page_number:
                    continue
                left, bottom, right, top = link["rect"]
                overlap_y = min(line["yMax"], height - bottom) - max(line["yMin"], height - top)
                overlap_x = min(line["xMax"], right) - max(line["xMin"], left)
                if overlap_y > 0 and overlap_x > 0:
                    selected.append(link)
            return selected

        if specimen == "navigation":
            target_pages = {title: marker_page(marker) for title, marker, _ in HEADINGS}
            actual = [entry for entry in outlines if "NAV " in entry["title"]]
            check("Navigation bookmark titles and hierarchy in order",
                  [(entry["title"], entry["depth"]) for entry in actual],
                  [(title, depth) for title, _, depth in HEADINGS])
            for title, _, _ in HEADINGS:
                entries = [entry for entry in outlines if entry["title"] == title]
                check("Unique bookmark: " + title, len(entries), 1)
                if len(entries) == 1 and target_pages[title] is not None:
                    check("Bookmark physical page: " + title, entries[0]["target"]["page"], target_pages[title])
                    target_near_title(entries[0]["target"], title, target_pages[title], "Bookmark " + title)
            first_main = target_pages[HEADINGS[0][0]]
            if first_main is not None:
                expected_labels = [roman(index + 1).lower() if index + 1 < first_main
                                   else str(index + 2 - first_main) for index in range(len(pages))]
                check("Roman front matter then continuous Arabic main/appendix labels", labels, expected_labels)
                known = [target_pages[title] for title, _, _ in HEADINGS if target_pages[title] is not None]
                check("Body heading physical order", known, sorted(known))
            toc = source_pages("Table of Contents")
            check("Exactly one controlled contents page", len(toc), 1)
            check("Bounding boxes retained for per-entry link validation", boxes is not None, True)
            if len(toc) == 1:
                toc_page = toc[0]
                for title, _, _ in HEADINGS:
                    # Native Typst outlines retain a zero-width WORD JOINER
                    # immediately before page labels in Poppler extraction.
                    pattern = re.compile(re.escape(title) + r"\s+(?:[.·]\s*)*\u2060?([ivxlcdmIVXLCDM0-9]+)$")
                    lines = [normal(line) for line in pages[toc_page - 1].splitlines()]
                    matches = [pattern.fullmatch(line) for line in lines]
                    matches = [match for match in matches if match is not None]
                    check("Unique visible contents entry: " + title, len(matches), 1)
                    target_page = target_pages[title]
                    if len(matches) == 1 and target_page is not None and first_main is not None:
                        check("Contents logical page: " + title, matches[0].group(1), str(target_page - first_main + 1))
                    if boxes is not None:
                        rows = [line for line in boxes[toc_page - 1]["lines"] if pattern.fullmatch(line["text"])]
                        check("Contents bounding-box row: " + title, len(rows), 1)
                        if len(rows) == 1:
                            row_links = links_for_line(toc_page, rows[0])
                            check("Contents entry has internal link: " + title, bool(row_links), True)
                            for link in row_links:
                                if target_page is not None:
                                    check("Contents link physical page: " + title, link["target"]["page"], target_page)
                                    target_near_title(link["target"], title, target_page, "Contents " + title)
            if boxes is not None:
                for label, destination in (("NAV FORWARD LINK BETA", "2 NAV CHAPTER BETA"),
                                           ("NAV BACK LINK ALPHA", "1 NAV CHAPTER ALPHA")):
                    rows = [(index + 1, line) for index, page in enumerate(boxes)
                            for line in page["lines"] if line["text"] == label]
                    check("Unique explicit link text: " + label, len(rows), 1)
                    if len(rows) == 1:
                        source_page, line = rows[0]
                        matching = links_for_line(source_page, line)
                        check("Explicit text has internal link: " + label, bool(matching), True)
                        for link in matching:
                            target_page = target_pages[destination]
                            if target_page is not None:
                                check("Explicit link physical page: " + label, link["target"]["page"], target_page)
                                target_near_title(link["target"], destination, target_page, label)
            for list_title, caption in (("List of Figures", "NAV FIGURE ALPHA"),
                                        ("List of Tables", "NAV TABLE ALPHA"),
                                        ("List of Algorithms", "NAV ALGORITHM ALPHA")):
                listing = source_pages(list_title)
                check("Exactly one " + list_title, len(listing), 1)
                if len(listing) == 1:
                    check("Caption occurs once in " + list_title, text[listing[0] - 1].count(caption), 1)
                    destinations = [index + 1 for index, page in enumerate(text)
                                    if first_main is not None and index + 1 >= first_main and caption in page]
                    check("Unique body caption: " + caption, len(destinations), 1)
                    if boxes is not None and len(destinations) == 1:
                        rows = [line for line in boxes[listing[0] - 1]["lines"] if caption in line["text"]]
                        check("Unique list row: " + caption, len(rows), 1)
                        if len(rows) == 1:
                            matching = links_for_line(listing[0], rows[0])
                            check("List row has internal link: " + caption, bool(matching), True)
                            for link in matching:
                                check("List link physical page: " + caption, link["target"]["page"], destinations[0])
            alpha_page = target_pages["Appendix A: NAV APPENDIX ALPHA"]
            if alpha_page is not None:
                # The supplied descriptor must render its literal table values.
                # This checks appendix content, not creative-work applicability.
                rows = [normal(line) for line in pages[alpha_page - 1].splitlines()]
                page_text = text[alpha_page - 1]
                check("Descriptor has two header cells", rows.count("Attribute Details"), 1)
                for field, value in CREATIVE_ROWS:
                    check("Descriptor row: " + field, rows.count(field + " " + value), 1)
                    check("Descriptor field cardinality: " + field,
                          len(re.findall(r"(?<![A-Za-z])" + re.escape(field) + r"(?![A-Za-z])", page_text)), 1)
                    check("Descriptor value cardinality: " + field, page_text.count(value), 1)
                check("No descriptor source fragments on appendix Alpha",
                      [token for token in ("f.at(", "fields.map(") if token in page_text], [])
        elif specimen == "appendix-pages":
            check("Three controlled pages", len(pages), 3)
            for marker, expected in (("NAV ARABIC PAGE CONTROL", 1), ("NAV APPENDIX ALPHA BODY", 2),
                                     ("NAV APPENDIX BETA BODY", 3)):
                check("Physical placement: " + marker, marker_page(marker), expected)
            check("Caller Arabic labels continue through appendices", labels, ["7", "8", "9"])
            expected = [("Appendix A: NAV APPENDIX ALPHA", 1, 2), ("Appendix B: NAV APPENDIX BETA", 1, 3)]
            check("Appendix A/B bookmarks and destinations",
                  [(entry["title"], entry["depth"], entry["target"]["page"]) for entry in outlines], expected)
        elif specimen == "appendix-layout":
            for suffix, marker, depth in (("NAV DIRECT APPENDIX", "NAV DIRECT APPENDIX BODY", 1),
                                           ("NAV DIRECT APPENDIX SECTION", "NAV DIRECT SECTION BODY", 2)):
                page = marker_page(marker)
                entries = [entry for entry in outlines if entry["title"].endswith(suffix)]
                check("Direct appendix bookmark: " + suffix, len(entries), 1)
                if len(entries) == 1:
                    check("Direct appendix heading level: " + suffix, entries[0]["depth"], depth)
                    if page is not None:
                        check("Direct appendix destination: " + suffix, entries[0]["target"]["page"], page)
        else:
            raise ValueError("Unknown controlled specimen")
    except (KeyError, TypeError, ValueError, IndexError, ET.ParseError) as error:
        report["errors"].append(type(error).__name__ + ": " + str(error))
    report["passed"] = not report["errors"]
    return report
