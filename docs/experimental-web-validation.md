# Experimental web bundle structural assurance

Scope: This is a **separate, opt-in** source-to-web validation track under
[WEB-01/02](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/24).
The included synthetic Typst 0.15.1+ fixture exercises the experimental multi-document
HTML/MathML exporter. It is not a submission-ready thesis.

A locally provisioned compatible Typst CLI can attempt an experimental build:

    typst compile --features bundle,html --format bundle --root . experiments/web/synthetic-bundle.typ build/experimental-web
    python -m scripts.web_bundle_validation --root build/experimental-web --expect index.html --expect chapters/methods.html

The exporter invocation itself requires current compiler qualification; it has
**not** been established by the structural tests. The Python verifier accepts
an existing directory and makes **no network requests or deployments**.

## Structural acceptance

The validator checks normalized local paths, symlink rejection, asset allowlisting,
limits and SHA-256 inventory, required HTML pages and local links/anchors,
document language, heading hierarchy, duplicate IDs, image alternative text,
table captions/header cells, and MathML element counts. Script/iframe/embed,
active attributes, remotely loaded assets, unreviewed CSS/SVG imports and
user-supplied restricted-data sentinels are rejected.

The required tests use synthetic two-page HTML/MathML. Run:

    python -m unittest tests.maintenance.test_web_bundle_validation -v
    make verify-python

A successful report is explicitly labelled **structural-validation-only**.
It does not establish responsive presentation, native web export success,
browser accessibility, meaningful equations, assistive-technology usability,
institutional policy compliance, rights clearance, scientific accuracy,
research reproducibility or safe distribution of a complete thesis. External
HTTPS links are not fetched, and this verifier is not a full HTML conformance
validator.

## Remaining pre-publication gates

Before any public web bundle is delivered, the author must use the reviewed
source-level content projection from [#23](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/23),
confirm its rights ledger independently, verify its final output inventory,
and conduct browser/keyboard/assistive-technology testing. The versioned
rights projection API is an explicit prerequisite for public publication,
not a property inferred by this static validator. Preserve the ordinary
qualified PDF path independently under #19. Never include private source,
unfiltered logs, identifying review receipts or private rights decisions in
a public/reviewer-safe bundle.
