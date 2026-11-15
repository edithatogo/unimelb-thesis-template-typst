# COR-03: legacy configuration resolution

This repair makes the existing Typst entry point use typed options and resolved
metadata consistently. It is a bounded COR-03 increment for the rendering
correctness workstream in [issue 15](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/15).
The shared JSON contract adapter remains a separate integration milestone.

## Configuration and compatibility

`lib.typ` reserves four command-line input names: `profile`, `font_theme`,
`locale` and `show_logo`. Typst supplies command-line values as
[strings in `sys.inputs`](https://typst.app/docs/reference/foundations/sys/). The
resolver accepts the existing documented profile, font-theme and locale values,
parses `show_logo=false` into the boolean `false`, and diagnoses malformed or
unknown reserved values. Other `sys.inputs` belong to caller documents and are
left untouched. This does not introduce CLI support for every metadata field.

Valid explicit named options continue to override the corresponding CLI-derived
defaults. Every supplied reserved CLI value is validated even if an explicit
argument would otherwise hide it. The existing metadata layer is retained:
non-`none` values in `metadata_overrides` override named metadata arguments;
`none` in that override dictionary means absent. Unknown override field names
and malformed supplied boolean fields are now rejected instead of silently
ignored. This legacy precedence is not represented as implementation of the
candidate contract's complete five-layer precedence.

`double_sided` now defaults to `auto`. Omitting it retains the profile default:
`print` selects double-sided rendering; the other profiles select one-sided
rendering. Explicit `true` or `false` takes effect in both the thesis entry point
and direct `main-matter-layout` calls. A string such as `"false"` is rejected.
The resolved profile also reaches `make-thesis-style`, so the print profile's
existing CMYK palette actually reaches rendered text.

Bibliography enablement, resource path and style are taken from the same resolved
metadata dictionary. Disabling a bibliography no longer opens its resource,
and a resolved override no longer leaves a raw path in use. Native paths and
supported resource collections are passed through without string conversion;
callers can construct [`path("references.bib")`](https://typst.app/docs/reference/foundations/path/)
in their own source directory.
The existing `numeric` alias resolves to `ieee`; `author-year` and `author_year`
resolve to `harvard-cite-them-right`; `chicago` resolves to
`chicago-author-date`. Native style names and supported CSL resources continue
through to [Typst's bibliography API](https://typst.app/docs/reference/model/bibliography/).

A supplied `declaration` is now the body of the Declaration page. It accepts
content or a string; `none` retains the generated declaration. The template adds
the existing heading, spacing and page break around supplied content. Rendering
that content does not certify its wording, completeness or policy suitability.

## University logo restriction

The thesis entry point and direct title-page helper default `show_logo` to
`false`. An explicit boolean `true` or CLI `show_logo=true` produces a diagnostic
referring to clause 3.6 of the University's
[preparation guidance](https://gradresearch.unimelb.edu.au/processes/preparation-of-graduate-research-theses),
which prohibits the University logo in a thesis. Use `show_logo: false` in a
Typst call or `--input show_logo=false` on the command line. This is an intentional
migration from the former `true` default. The generic logo utility remains
available outside this thesis entry point; this repair does not make a wider
branding or institutional-conformance claim.

## Regression scope

The canonical verifier adds 34 synthetic COR-03 cases after the existing shipped
PDF, COR-01 and COR-02 checks. Twenty-three cases require validated rendered PDFs;
eleven require the intended configuration rejection. The fixture guide explains
the independent text, physical-page and native PDF-colour oracles in
[tests/rendered/cor03](../tests/rendered/cor03/README.md).

The bounded controls retain native bibliography resource behavior and the
existing metadata precedence. They do not establish a completed shared adapter,
blind output, creative applicability, accessibility or university acceptance.
The follow-up [layout and order corpus](layout-order.md) qualifies logical page 1
at the first core chapter, Roman-numbered duplex alignment, continuous Arabic
back matter, one bibliography heading and bibliography before appendices.
Publication-specific bibliography policy and broader resource handling remain
separate work. The [native image corpus](native-images.md) qualifies input
forwarding across profiles; automatic image conversion is not implemented.
