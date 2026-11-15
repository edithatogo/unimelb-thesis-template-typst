# Native contract-adapter specimens

This corpus accounts for the exact 18 fixtures in the retained UMTHESIS bundle,
then adds three local controls. The canonical fixtures define configuration
semantics. `expectations.json` supplies separate literal output expectations for
the bounded Typst renderer; it is not a shared cross-engine matter-order oracle.

The expected outcomes are seven real PDFs, nine intended validation rejections
and five valid configurations explicitly reported as unsupported. None of the
negative cases is described as a clean document. `oracles.py` requires all 21
case identities and the exact bundle/fixture-manifest pins.

`body.typ` supplies two chapters and a same-page section with unique visible
markers. Native page objects, page-label ranges, bookmarks, annotations and
bounding boxes are parsed with the existing COR-02 PDF helper. Literal expected
metadata and the physical body markers determine output assertions independently
of the producer's rendering functions.

The three local controls are:

- `precedence-layers`: defaults, selected profile, metadata, parsed CLI and
  explicit arguments contribute to one normalized configuration and actual PDF.
- `print-profile-default`: the profile supplies typed duplex true, including
  Roman alignment pages and a core restart at Arabic 1.
- `literal-markup`: a title containing `#panic(123)` remains literal visible and
  native PDF metadata, rather than becoming executable source.

Run `python3 scripts/verify_typst_contract_adapter.py` from the repository root.
It preserves per-command 60-second limits, removes seeded stale generated
artifacts and writes actual native reports plus independent oracle reports.
It invokes the adapter's argument parser directly and retains invocation
receipts; compiler/PDF commands alone cross the process-supervision boundary.
The actual Typst version must match `typst.toml` before rendering.
The adapter identifies source inputs by their content hashes and explicitly
leaves its source revision uncollected. The outer canonical report carries
checkout-revision evidence when available. Contract acceptance remains blocked.
Full integration and exact-head hosted
qualification are separate from this focused corpus.

All authored specimens and local input records here are synthetic and CC0. The
canonical fixture files retain their existing attribution and are not copied or
modified by this corpus. See [the adapter guide](../../docs/typst-contract-adapter.md)
for supported fields, commands and limits.
