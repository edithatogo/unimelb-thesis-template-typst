# Native image inputs

`thesis-image(source, ..options)` forwards its input and options to Typst's native
`image` function in every build profile. It accepts file-name strings, native
`path` values and image bytes. Supply an `alt` description appropriate to the
figure, and use the native `width`, `height` and fitting options as needed.

```typst
#import "utils/style.typ": thesis-image
#thesis-image("assets/figure.jpg", width: 8cm, alt: "Description of this figure")
```

Typst's `format` option selects the **input decoder**. Setting `format: "png"`
does not convert a JPEG to PNG or compress it for screen viewing. The historical
helper did this for draft and screen builds, causing valid JPEG inputs to fail.
It also assumed that every source had a string method, rejecting native paths
and byte inputs in those profiles. The helper now preserves the supplied input.

Profile-specific image recompression is not implemented. Prepare transformed
assets separately if needed, check their visual quality, and keep their input
format consistent with any explicit decoder option. The underlying native
formats and options are documented in the
[Typst image reference](https://typst.app/docs/reference/visualize/image/).

## Bounded verification

`make verify` compiles twenty synthetic specimens: PNG, JPEG and SVG under each
of default, draft, screen and print, plus JPEG supplied as a native path and as
bytes under each profile. Every compiler and PDF inspection command has the
same sixty-second budget as the other rendered checks.

The independent oracle checks actual PDF output: exact decoded PNG pixels,
unchanged embedded JPEG bytes, dimensions and encoding, native SVG rectangles,
and retained alternative text. Fourteen original cases provide positive
controls; the six previously failing draft/screen cases must now compile and
satisfy the same assertions. Stale generated output is cleared before execution.

These fixtures qualify the bounded native-input behavior. They do not qualify
all possible assets, image recompression, colour management, or PDF/A and PDF/UA
conformance.
