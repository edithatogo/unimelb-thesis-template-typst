# Public optional sections

Updated 15 November 2026 (Brisbane).

The legacy `thesis(...)` entry point accepts public records for assistance, prior
work, funding and creative outputs. Each populated section renders independently.
Publication records also activate the Preface when no free-form preface text was
supplied. This is a bounded rendering interface; it does not certify institutional
approval, required declaration wording, RTP acknowledgement wording or submission
eligibility.

The record shapes follow the corresponding fields in the
[shared metadata schema](../contracts/thesis/v1/schemas/metadata.schema.json).
This does not imply that the separate canonical contract adapter supports every
legacy `thesis(...)` field. Check that adapter's explicit capability report.

## Record fields and output

Use an array of dictionaries for each field, including a one-record array such as
`((funder: "Synthetic Research Fund"),)`. Omit the field or supply `()` when it is
empty. Records reject unknown keys, missing required fields and wrong value types.
String fields described as nonempty require at least one character. Identifier
fields start with an ASCII letter or digit and then allow ASCII letters, digits,
dot, underscore, colon and hyphen.

| Field | Required record fields | Optional record fields | Rendered output |
| --- | --- | --- | --- |
| `assistance` | `kind`: `"human"`, `"digital"` or `"ai"`; nonempty `description` | `reference`: identifier | The kind label and description in the Preface. The reference is not printed. |
| `prior_work` | Nonempty `description` | Nonempty `degree`, `institution`; `approval_ref`: identifier | Description and supplied degree/institution in the Preface. The approval reference is not printed or treated as verified approval. |
| `funding` | Nonempty `funder` | Nonempty `grant`; `acknowledgement`: string, which may be empty | A separate Funding page containing the supplied public funder, grant and acknowledgement. |
| `creative_outputs` | `id`: identifier; nonempty `description` | `proportion`: finite number from 0 to 100; `resource_ids`: array of unique identifiers | Description and any explicitly supplied record proportion in the Preface. Record/resource identifiers are not printed and do not embed or package resources. |

For example:

```typst
#show: thesis.with(
  // Supply the usual title, author, degree and submission fields too.
  assistance: ((
    kind: "human",
    description: "A colleague commented on the structure of a draft.",
  ),),
  funding: ((
    funder: "Synthetic Research Fund",
    grant: "SYNTHETIC-001",
    acknowledgement: "Synthetic funding example; replace with accurate wording.",
  ),),
)
```

The actual front-matter sequence is title, abstract when supplied, declaration,
Preface when applicable, Funding when supplied, other acknowledgements when
supplied, and contents/list pages. Funding alone does not create an empty Preface.
Legacy `ai_usage` and `third_party_assistance` remain public summaries in the
generated declaration; they do not create a Preface by themselves. A custom
declaration remains author-supplied content.

The same record fields are accepted in `metadata_overrides`. Arrays replace the
earlier array, so an explicit empty array removes a section. Each supplied record
layer is validated before overrides are applied: an invalid earlier record cannot
be hidden by a valid later value. Cross-field creative percentage consistency is
checked on the resolved metadata.

## Creative-output applicability and percentages

Actual `creative_outputs` records activate a factual creative-output clause in
the generated declaration. A minimal record is enough:

```typst
creative_outputs: ((
  id: "synthetic-video",
  description: "A short synthetic video exploring patterns of light.",
),),
```

Without an aggregate percentage pair, the clause states that the thesis includes
the creative outputs described in the Preface. It makes no claim about committee
agreement. Publication records and `includes_publications: true` do not activate
this clause.

To print an aggregate split, explicitly supply both `percentage_dissertation`
and `percentage_creative`. Each must be a finite integer or floating-point number
from 0 to 100, and their sum must be 100. At least one creative record must exist.
One-sided, out-of-range, nonnumeric or inconsistent pairs are rejected. Use numbers
such as `70` and `30`, not Typst ratio values such as `70%`.

The per-record `proportion` field is rendered as a declared record proportion.
It is never used to infer the aggregate dissertation/creative split. This legacy
aggregate pair is not a new field in the shared contract schema; defining shared
aggregate semantics and institutional approval rules remains separate work.

## Migrating private AI logs

The old `ai_assistance` shape and nonempty `ai-usage-note(...)` calls accepted fields
such as `tool`, `date`, `purpose`, `prompt` and `output_ref`. They now fail with an
actionable migration diagnostic. An empty legacy helper call remains harmless.
The obsolete `frontmatter/preface.typ` import forwards to the canonical Preface
renderer, so it cannot retain a second private-log rendering path.

Write a public account of assistance explicitly, using `assistance` records with
`kind` and `description`. Do not copy a private log into a description or rename
the log automatically. Keep prompts, generated outputs and confidential review
notes outside the thesis. The public description should state what actually
happened; the template does not invent verification, permission or tool-use claims.
Existing public `ai_usage` and `third_party_assistance` summaries remain supported.

`reference` and `approval_ref` are bookkeeping identifiers. The template accepts
their syntax and omits them from rendered PDF surfaces; it does not read the
referenced material, verify an approval or publish a private reference. These
values still exist in the source. Source files, internal command diagnostics and
verification receipts are not reviewer-safe packages.

## Blind copies and authored records

Blind projection still controls the template-owned identity fields. Descriptions,
prior-work institutions and funding statements remain authored material requiring
review, like prose, self-citations, alternative text, links and index entries. The
static blind diagnostic lists the new optional fields. It contains no original
identity values and does not certify anonymity.

The rendered corpus includes a blind specimen whose assistance, prior-work,
funding and creative descriptions retain declared identity markers. Its PDF scan
must fail even though the regression assertion correctly detects those residuals.
A second specimen uses explicitly reviewed replacement wording and must have no
declared markers on the captured surfaces. This tests known synthetic markers;
it is not a general anonymization detector or the separate packaging workflow.

## Executable examples and checks

The two standalone samples contain synthetic statements and the current public
fields:

- [Public assistance sample](../examples/samples/sample-ai-disclosure.typ)
- [Creative-output sample](../examples/samples/sample-creative-outputs.typ)

From the repository root, after creating `build/`, compile them with:

```sh
typst compile --root . examples/samples/sample-ai-disclosure.typ build/sample-ai-disclosure.pdf
typst compile --root . examples/samples/sample-creative-outputs.typ build/sample-creative-outputs.pdf
```

`make verify` includes these two files and the compatibility Preface caller in the
47-case COR-05 corpus. It retains commands, source/fixture/output hashes, real PDF
checks, extracted text, native PDF objects, XMP and semantic assertions under
`build/verification/cor05/`. The report begins unexecuted/failed, clears stale
generated outputs, and preserves the existing 60-second per-command budget.

The original 14 COR-01 fixtures and oracles remain unchanged. The optional corpus
adds public values/cardinality, applicability, physical/native-bookmark order,
private-reference absence, legacy summaries, empty/explicit overrides, typed
rejections and the explicit blind residual controls. A successful corpus does not
establish the unimplemented policy, packaging or approval requirements.
