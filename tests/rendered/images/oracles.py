"""Independent expectations for native image handling across four profiles."""

import base64
import hashlib

CREATION_TIMESTAMP = "1794700800"
PROFILES = ("default", "draft", "screen", "print")
RESOURCES = ("png", "jpg", "svg", "native", "bytes")
EXPECTED_SPECIMEN_COUNT = 20
SOURCE_FILES = ("utils/style.typ", "utils/fonts.typ", "assets/colors/unimelb-colors.typ")
FIXTURE = "tests/rendered/images/image.typ"
ASSETS = (
    "tests/rendered/images/assets/control.png",
    "tests/rendered/images/assets/control.jpg",
    "tests/rendered/images/assets/control.svg",
)
JPEG_SHA256 = "a0f35b69dc9074097f9f68bdda0aea2a55990617abb06420f565898f8ee22723"
PNG_PIXELS = bytes((255, 0, 0, 0, 255, 0, 0, 0, 255, 255, 255, 0))


def specimens():
    return [
        {"id": f"{profile}-{resource}", "profile": profile, "resource": resource}
        for profile in PROFILES for resource in RESOURCES
    ]


def check_native(case, text, page_count, native):
    checks = []

    def check(description, condition):
        checks.append({"description": description, "passed": bool(condition)})

    check("One controlled page", page_count == 1)
    check("Visible fixture sentinel occurs exactly once", text.count("IMAGE INPUT CONTROL") == 1)
    pages = native["pages"]
    check("One native PDF page", len(pages) == 1)
    objects = {}
    for group in native["qpdf"]:
        for key, value in group.items():
            if key.startswith("obj:"):
                if key in objects:
                    raise ValueError("Duplicate native PDF object")
                objects[key] = value
    page = pages[0]
    images = page["images"]
    contents = b"".join(
        base64.b64decode(objects["obj:" + ref]["stream"]["data"], validate=True)
        for ref in page["contents"]
    )
    check("Declared image alternative text survives in native content",
          b"/Alt(Synthetic geometric colour squares)" in contents)
    if case["resource"] == "svg":
        check("The SVG remains vector content", images == [])
        check("First red vector rectangle is present", b"1 0 0 scn 0 0 m 10 0 l 10 20 l 0 20 l" in contents)
        check("Second blue vector rectangle is present", b"0 0 1 scn 10 0 m 20 0 l 20 20 l 10 20 l" in contents)
        check("Exactly two vector rectangles are filled", contents.count(b"\nf\n") == 2)
    else:
        check("Exactly one raster image", len(images) == 1)
        if len(images) != 1:
            raise ValueError("Expected exactly one raster image")
        item = images[0]
        check("The supplied two-by-two raster dimensions survive", item["width"] == 2 and item["height"] == 2)
        check("Eight-bit raster components survive", item["bitspercomponent"] == 8)
        stream = objects["obj:" + item["object"]]["stream"]
        data = base64.b64decode(stream["data"], validate=True)
        if case["resource"] == "png":
            check("PNG uses native lossless image embedding", item["filter"] == ["/FlateDecode"])
            check("All four supplied RGB pixels survive exactly", data == PNG_PIXELS)
        else:
            check("JPEG uses its native DCT encoding", item["filter"] == ["/DCTDecode"])
            check("Embedded JPEG bytes match the synthetic source",
                  hashlib.sha256(data).hexdigest() == JPEG_SHA256)
    return {
        "scope": "Bounded two-by-two PNG/JPEG and two-rectangle SVG fixtures, four profiles",
        "checks": checks,
        "errors": [x["description"] for x in checks if not x["passed"]],
    }
