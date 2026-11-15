# Native Typst evidence

The canonical verifier includes a bounded native evidence corpus for UMTHESIS
TYP-04 and TST-03. It uses the compiler version pinned in `typst.toml`, the existing
60-second command limit and the reviewed process cleanup. It adds no workflow or
check name. Its results qualify the declared synthetic extraction and inventory
cases; they do not certify a complete thesis, both rendering engines or a
reproducible release.

## Semantic results need a contract

An exit-zero `typst eval` command may legitimately return `false`, `null`, `""`,
`[]` or `{}`. The verifier therefore runs a closed list of fixed expressions and
validates each result against a declared JSON Schema 2020-12 definition. Required
assertions must be true; required metadata must have exactly one correctly shaped
record; required heading and reference collections must be nonempty and valid.
Missing, duplicate and malformed metadata are separate negative cases. Nonfinite
numeric results, including exponent overflow during JSON decoding, are rejected
before they can qualify as semantic evidence.

The optional-value control preserves false, zero, null and empty string, array
and object values with their original types. It also renders the literal string
`#panic(123)` from JSON. Metadata is data: none of its values become an eval
expression or executable Typst source. The fixed heading expression is scoped to
the plain synthetic heading in this fixture, not advertised as a general extractor
for arbitrary rich heading content.

| Bounded case group | Count | Required outcome |
| --- | ---: | --- |
| Checked PDF and its native dependency inventory | 1 | Valid output, three expected source inputs, actual PDF text and font observations |
| Assertion, metadata, heading, reference and optional values | 5 | Native exit zero and exact typed, schema-valid result |
| Required false/null/empty values and malformed metadata | 8 | Native exit zero, but explicit semantic rejection |
| Native assertion failure | 1 | Native exit one with the intended assertion diagnostic |
| Native compilation failure | 1 | Native exit one, no PDF, native `outputs: null`, no successful inventory |

All 16 regression cases must meet their declared outcome. A passing rejection
case keeps `evidence_status: rejected`; it is never counted as accepted evidence
or as a clean document. The corpus reports six accepted evidence results and ten
expected rejections separately.

## Dependency paths require a successful build

For the native fixture and successful COR-04/COR-05 specimens, compilation requests
`--deps PATH --deps-format json`. A dependency object is accepted only when it is
bound to one successful, non-timed-out compile record and its retained command
log. The source, actual PDF, expected output path, native report bytes and required
source input must agree. Missing files, malformed JSON, duplicate keys or paths,
non-path entries, unknown fields, missing inputs, null/empty outputs, changed
source/output hashes and a different output destination all fail.

Old PDF, text, log and native sidecar outputs are removed before the new bounded
run. Each successful inventory hashes the paths that Typst actually reported.
These are **observed post-compile content hashes**. Typst itself emits paths,
not hashes; the added hashes are not proof that every dependency was immutable
throughout compilation.

## Published inventory format and privacy boundary

`build/verification/native/document.dependencies.json` and the corresponding
COR-04/COR-05 `.dependencies.json` artifacts contain a
`validated-dependency-inventory`, rather than an unmodified copy of Typst's JSON.
Validation first binds the exact native bytes to the compile's requested file.
The retained artifact then replaces machine paths with `project:`, `package-cache:`
and `package-local:` identifiers and records the original native SHA-256 and byte
count. It explicitly states that the original bytes are not retained verbatim.
If validation fails, the artifact is replaced with a rejected-inventory receipt
containing the original byte digest and a failure code, without retaining the
unapproved raw paths.

Approved package locations are the explicit `TYPST_PACKAGE_CACHE_PATH` and
`TYPST_PACKAGE_PATH` overrides, or the standard Linux XDG cache/data package
directories. Relative explicit overrides resolve from the compiler's working
directory. Other external roots fail closed. Other operating systems can declare
their package locations through those overrides; this slice's native proof uses
Linux. Package names, versions and observed file hashes remain visible in the
neutral path records. This does not turn the entire diagnostic report or an
identified thesis into reviewer-safe material.

## Separate tooling and font observations

The native supplement records the manifest, compiler and actual executable
digests and versions for Typst, qpdf, pdfinfo, pdftotext and pdffonts. It also records
the Python executable and JSON Schema validator version. The synthetic fixture
uses Libertinus Serif with system-font discovery disabled. Actual PDF font names
and embedding/subset/Unicode-map observations come from `pdffonts`; explicit font
environment settings are reported as present or absent.

Native dependency JSON does not inventory fonts. The supplement does not pretend
to provide per-face font source hashes: it records that inventory as uncollected.
It also does not lock shared libraries, all environment settings or complete
package archives. The fixture uses no external package imports, while the real
COR-04/COR-05 captures retain their observed package input paths and file hashes.
`replay_qualified` remains false. Font source qualification, installed-package
testing and a complete release replay manifest remain separate work.

## Evidence and failure controls

The canonical report is `build/verification/report.json`; native raw semantic
JSON, command logs, the real PDF/text, the normalized inventory and the supplement
are under `build/verification/native/`. The failed compile's dependency object is
retained as an explicitly failed capture; its controlled fixture reports only a
project-relative input and a null output.

`tests/maintenance/test_native_evidence.py` adds focused validation and capture
controls, including missing tools/evidence, stale artifacts, exact byte binding,
wrong source/output, failed/timeout command records and external-path handling.
The reusable validation code in `scripts/native_evidence.py` is included in the
declared Python line/branch coverage scope, with the existing 80% floors unchanged.
The fixed expressions and literal expectations in `tests/rendered/native/oracles.py`
and command orchestration in `scripts/verify.py` are outside that denominator;
their native execution is evidenced separately.
The shared process runner's real timeout tests remain responsible for process
cleanup. These controls do not replace the other canonical corpora or the final
integrated `make verify` gate.

## Primary references

- [Typst 0.15.1 changelog](https://typst.app/docs/changelog/0.15.1/) records the
  corrected unsuccessful exit for failed native evaluation.
- [Pinned dependency writer](https://github.com/typst/typst/blob/v0.15.1/crates/typst-cli/src/deps.rs)
  defines input paths and optional output paths, including null outputs.
- [Pinned world implementation](https://github.com/typst/typst/blob/v0.15.1/crates/typst-cli/src/world.rs)
  distinguishes file dependencies from font discovery and loading.
- [Python JSON decoding](https://docs.python.org/3/library/json.html) documents
  the separate floating-point parser hook used to reject exponent overflow.
