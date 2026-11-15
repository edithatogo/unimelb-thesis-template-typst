# COR-03 legacy configuration fixtures

The canonical verifier runs these 34 specimens after the shipped thesis/sample
PDFs, all 14 COR-01 specimens and all three COR-02 specimens. Run `make verify`
for the full repository gate. Every compiler, qpdf and Poppler command retains
the existing 60-second limit.

There are 23 successful-output cases and 11 deliberate rejection cases. A
rejection passes only when Typst exits with exactly 1, emits only the intended
configuration error, completes before the timeout, and produces no PDF.
Unexpected success, an unrelated syntax error, a missing tool and a timeout all
fail. Existing positive commands continue to require exit 0.

The public outcomes include:

- Typed `--input show_logo=false`, permitted caller-owned inputs, and explicit
  diagnostics for malformed reserved flags and unknown metadata override keys.
- Profile-selected PDF colour models and explicit duplex overrides. Unique
  chapter body sentences independently identify physical pages; the oracle
  checks their spacing and recto placement without reading template counters.
- Resolved bibliography enablement, path and style, including a native `path`
  created by the caller and a mixed native/string resource collection. Literal
  reference titles distinguish the selected resource from a deliberately wrong
  one. The disabled case supplies a nonexistent resource, which must not open.
- Preserved bibliography aliases, checked through their actual citation text.
- A supplied declaration body on its Declaration page, with the generated body
  absent. Omitted declarations retain the generated original-work statement.
- No default logo placeholder, and policy diagnostics for explicit or CLI
  `true`, including the direct title-page context. A specific optional soft
  hyphen in the old placeholder's spelling of Melbourne is recognised by the
  logo text count; there is no general Unicode stripping.

`oracles.py` contains literal expectations and pure parsers, without subprocess
or compilation logic. Only four colour cases need qpdf JSON and decoded PDF
content streams. The first chapter body marker selects their physical page;
the direct style control uses its sole page. The checks distinguish native
four-component CMYK operators from the RGB operators present before repair.

The verifier retains per-case commands, exit expectations, diagnostics,
timeouts, source/resource/fixture/oracle hashes, PDFs, extracted text, oracle
reports and selected native colour streams. It removes stale outputs first and
starts the top-level report failed, so interruption cannot preserve an earlier
success. Synthetic data and a fixed creation timestamp keep the scope bounded.

These fixtures exercise the legacy Typst entry point. They do not implement or
certify the five-layer shared JSON contract, blind projection, arbitrary author
prose, creative-work applicability, all-profile pagination, general PDF
accessibility or university acceptance. The fictional fixtures are distributed
under the repository's [Apache-2.0 licence](../../../LICENSE).
