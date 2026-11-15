# Native image inputs across profiles

These 20 synthetic cases exercise PNG, JPEG and SVG inputs under default, draft,
screen and print. JPEG is additionally supplied as a native `path` and as bytes.
The geometric assets are CC0; their licence is retained beside the fixtures.

The original helper forced the PNG decoder for non-SVG draft/screen images.
Six cases failed: two JPEG decode errors and four unsupported string-method
calls on path/bytes values. The fourteen successful cases provide controls.

The repaired helper forwards the original input and options to Typst's native
`image`. Its `format` argument selects the input decoder, not output conversion.
This helper does not implement profile-specific image recompression. Authors
who need transformed assets must prepare and verify those assets separately.

The independent oracle inspects qpdf JSON with inline native streams. It checks
one raster, two-by-two dimensions, exact decoded PNG pixels and unchanged
embedded JPEG bytes. The SVG has two expected native vector rectangles and no
raster image. The supplied alternative text must appear in native content.
Every compiler/qpdf/Poppler command keeps the canonical 60-second budget.

These are bounded resource and output checks. They do not qualify arbitrary
images, a compression pipeline, general colour management, PDF/UA or PDF/A.
