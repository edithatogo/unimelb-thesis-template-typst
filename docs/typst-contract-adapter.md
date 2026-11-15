# Bounded Typst contract adapter

The adapter renders a defined subset of the shared UMTHESIS configuration through
a new Typst entry point. It reuses the canonical schema and five-layer resolver.
It does not replace `thesis.typ`, change the legacy `thesis(...)` interface or
register either engine as a completed contract implementation.

The current bundle still marks both engine adapters as `planned`. Its 18 fixtures
specify configuration outcomes; they do not contain a shared rendered matter-order
oracle. Accordingly, this adapter writes a separate native execution report whose
contract acceptance remains blocked. A successful native report is evidence about
the bounded output described here, not full CON-02/CON-03, cross-engine acceptance,
PDF standards conformance, institutional approval or execution of LaTeX.

## Input and precedence

Use `scripts/typst_contract_adapter.py` as the validation boundary. It passes raw
metadata, CLI overrides and explicit arguments to the unchanged
`scripts/thesis_contract.py` resolver. The precedence is:

1. Shared defaults.
2. Defaults for the highest-precedence selected layout profile.
3. The metadata configuration object.
4. Parsed CLI overrides.
5. Explicit API arguments supplied as a JSON configuration object.

Each supplied layer is validated before merging. An invalid lower layer cannot be
hidden by a later valid value. Objects merge recursively; arrays and scalars
replace. A typed `false` remains false, including an explicit override of the
print profile's duplex default. CLI string parsing follows the shared schema.

All invocations require the exact bundle and fixture-manifest digests. Fixture
mode additionally requires the individual fixture digest. A stale pin or adapter
API version fails before compilation. The normalized configuration and its actual
SHA-256 digest are retained in the native report and in the renderer input.
The standalone adapter also enforces the compiler version in `typst.toml` before
compilation and binds that manifest in its source evidence.

The Typst entry point reads JSON data. Metadata is never interpolated into Typst
source or evaluated as code. The supplied body is a trusted, regular Typst source
file within the project. Calling the low-level `contract-document` function
directly does not perform JSON Schema validation and is outside this interface.

## Supported output

This first slice supports identified English PDF output with `purpose` set to
`draft` or `examination`, no requested PDF standard, and the shared default
bibliography configuration. The bibliography setting is normalized but the
synthetic body contains no citations or reference resources; this slice does not
qualify bibliography rendering.

| Configuration | Bounded behavior |
| --- | --- |
| `metadata.title` | Visible title and native PDF title metadata |
| `metadata.author.student_record_name` | Visible author and native PDF author metadata |
| `metadata.author.orcid` | Visible ORCID when supplied; no invented value when absent |
| `metadata.degree.kind`, `metadata.degree.course` | Validated degree kind and visible course name |
| `metadata.academic_units` | Visible units, preserving their supplied order |
| `metadata.submission.month` | Literal year-month, without inferring a day |
| `metadata.abstract` | Optional abstract page before the declaration |
| `metadata.declarations.original_work`, `word_count` | Supplied attestation and word count; explicit absence in incomplete drafts |
| `layout`, `double_sided` | Existing style/layout helpers, with typed duplex and print recto placement |

The local matter sequence is title, optional abstract, declaration, contents and
the supplied body. The local oracle checks that sequence, visible metadata,
bookmarks, contents links and their actual destinations. Front matter, including
duplex alignment pages, has Roman PDF page labels. Core labels restart at Arabic
1 and continue through intervening pages. These checks do not certify every
visible header/footer convention or institutional title/declaration wording.

Missing draft fields are displayed as explicit draft placeholders. A draft does
not acquire fabricated author details, dates, signatures or declarations. The
small title and declaration blocks exercise canonical metadata; their successful
rendering does not establish that an examination document is submission-ready.

## Unsupported and invalid are different outcomes

Valid configuration outside this slice is reported with `result: unsupported`,
the exact unsupported paths and exit code 2. No compiler runs and no PDF remains.
This includes blind or deposit projection, other languages/locales, requested PDF
standards or outputs, alternative bibliography settings, approval references and
metadata fields outside the table above. Explicit `original_work: false` is also
unsupported here. In particular, publication/contribution, funding, prior-work,
assistance, creative-output, joint-award and resubmission records are not silently
discarded. Their dedicated rendering and review work remains separate.

Invalid configuration exits 1 with its canonical validation diagnostic. A tool,
artifact, timeout or source-change failure also exits 1, with an execution failure
report. Exit 0 means that this adapter actually generated and structurally checked
the supported PDF. It does not mean that contract acceptance became complete.

The pinned corpus accounts for all 18 canonical fixtures:

| Outcome | Fixture IDs |
| --- | --- |
| Rendered, with independent local output assertions | `doctoral-monograph`, `draft-minimal`, `cli-false`, `print-explicit-false` |
| Valid but unsupported | `blind-draft`, `joint-resubmission`, `masters-publication`, `non-english-creative`, `public-deposit-input` |
| Intended validation rejection | `bad-month`, `bad-orcid`, `blind-examination`, `incompatible-pdf`, `missing-final-title`, `missing-language-approval`, `placeholder-final-title`, `string-boolean`, `unknown-field` |

Three additional local controls cover all five precedence layers, print-profile
defaults and literal markup-like metadata. They are explicitly identified as
adapter-local controls, not additions to the shared fixture manifest.

## Reproduce the bounded checks

Install the repository's Python development requirements and the same Typst,
qpdf, pdfinfo and pdftotext tools used by canonical verification. From the
repository root:

```sh
python3 -m unittest discover -s tests/contract -p test_typst_contract_adapter.py -v
python3 scripts/verify_typst_contract_adapter.py
```

The second command writes `build/contract-adapter-verification/report.json` and
per-case native reports, commands, PDFs, text, native PDF objects and bounding
boxes. The canonical verifier invokes the same corpus under
`build/verification/contract-adapter/`. Its native result remains distinct from
contract requirement acceptance in the parent report. Existing checks and corpus
functions remain in place.

For one pinned canonical specimen:

```sh
python3 scripts/typst_contract_adapter.py \
  --contract-sha256 338f93c64ce84621670f267c0919555d77c592e92e75f04e12afd6cab57cea7c \
  --fixture-manifest-sha256 af82359a786b2be565e49de594e32a5d2edb3354221dfd5371d5d954b33c5757 \
  --output build/adapter-example \
  fixture doctoral-monograph \
  --fixture-sha256 9f5fede93ab19d258364671aa4533b87a47849ee651edbe0265ab0b90615d3ba
```

For caller data, replace the `fixture ...` subcommand with `render --metadata
metadata.json --explicit explicit.json --set double_sided=false`. These JSON
files contain configuration patches, including a nested `metadata` object; they
are not bare author records. `--body path/to/body.typ` is a global option before
the subcommand. Outputs must be in a proper subdirectory of `build`.

## Evidence and failure boundaries

Every external command retains the existing 60-second limit. Reports bind input
pins, normalized configuration, rendering sources, tool versions, commands and
artifact hashes. Known generated files are removed before every invocation, and
an initial failed receipt replaces any old success before processing begins.
The corpus seeds stale outputs in positive, invalid and unsupported cases. It
requires the intended result, not merely a nonzero exit or the presence of a PDF.

The corpus and canonical hook invoke the validated `main(argv)` interfaces in
the same Python process, retaining argument/result and diagnostic receipts. They
restore the shared runner's state after each call. Actual compiler/PDF commands
use the common process supervisor; there is no outer Python subprocess deadline
that can interrupt the inner supervisor's cleanup. The root runner's separate
failed-command cleanup budget does not extend the 60-second execution deadline.

The CLI-style adapter `main(argv)` itself leaves `verify.ROOT` and `verify.OUTPUT`
set for its output directory. This is local to a standalone CLI process. An
in-process caller owns saving and restoring those values; the corpus's
`invoke_adapter` wrapper and the canonical hook do so in `finally` blocks.
Native receipts use `source_kind: content-hash-bound-native-slice`, leave
`source_revision` null and mark it `uncollected`. Source-file hashes identify
the actual inputs. The outer canonical report supplies checkout revision/state
evidence when available; the adapter never infers a commit from an enclosing
checkout that may not contain the executed files.
The source inventory covers the adapter, validator, known rendering modules,
compiler manifest and supplied body. Arbitrary transitive imports or resources
inside a caller's custom body are outside this bounded inventory and corpus.

Native assertions use independently written literal metadata and order
expectations. They associate visible contents rows with native annotations and
check destination coordinates against the target heading's text bounds. Unit
failure controls cover missing or malformed outputs, failed tools, timeouts,
stale receipts, changed sources, wrong compiler versions and invalid/unsupported
inputs. They mock the stable runner interface; separate real-command tests
exercise OS process supervision. Mocked unit tool responses are not counted as
real PDF evidence.

Coverage includes `scripts/typst_contract_adapter.py` as the fifth measured
validation helper. The corpus runner, shared verifier, test oracles and Typst
rendering are outside that Python coverage denominator. Their native execution
evidence must be assessed separately. The retained prototype proof does not
replace a complete `make verify`, exact-head hosted checks or integration review.

Before claiming shared contract acceptance, promote actual supported capabilities
through the canonical compatibility/result protocol, pin a shared matter-order
oracle, bind qualified source revisions and execute the required engine lanes.
The current canonical bundle and its historical source snapshots are unchanged.
