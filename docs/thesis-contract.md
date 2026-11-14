# Shared thesis contract

The candidate UMTHESIS 1.0.0 schema/API milestone lives in
[contracts/thesis/v1](../contracts/thesis/v1/manifest.json). It materialises
[issue #13](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/13)
through [issue #14](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/14).

This increment validates configuration and evidence interfaces. Existing thesis
rendering remains on its existing interface until the correctness/native-feature
work integrates the normalized values. Both document adapters are explicitly
planned in compatibility.json. Neither schema validity nor a passing negative
fixture certifies a thesis, institutional approval, accessibility or public release.

## Contents and provenance

The bundle includes nine JSON Schema 2020-12 schemas, the complete 51-requirement
catalogue, all 53 legacy-ID mappings, ten dated source records and their exact
offline snapshots, 18 licensed synthetic configuration fixtures, defaults/profile
defaults and the adapter compatibility boundary.

The source ledger separates the project contract, historical checklists and
pinned central standards. It does not label a historical source as current
university policy. Current policy-source retrieval and interpretation remain with
#17. Raw snapshots preserve historical wording, formatting and task-completion
claims solely as evidence; they do not reinstate those claims.

Every bundle file except manifest.json appears in the manifest with its exact
UTF-8 byte SHA-256. The contract pin is the SHA-256 of the manifest's exact bytes.
Missing, additional, altered or escaping files fail validation. Source snapshots
must also match the independently recorded ledger hashes. No source or schema is
downloaded during verification; external schema references are rejected.

The parent requirement outcomes are compared with the retained issue snapshot.
Owners, acceptance cases, source/fixture mappings and legacy IDs cannot silently
disappear. Planned catalogue cases remain planned until their specific
implementation and execution evidence are attached.

## Install and verify

Use the repository's documented Python version and pinned dependencies:

~~~sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --requirement requirements-dev.txt
make verify-contract
make verify
make coverage
~~~

The existing required "Verify template and properties" and "Python validation
coverage" checks execute these gates. No extra required check or publishing event
is introduced. The contract report is build/contract/report.json; it records the
source revision, dirty state, contract digest and expected/observed fixture
outcomes. Its scope is explicitly contract-schema-api, with both document
adapters unexecuted. It is a native report, not the central verification receipt.

Coverage now measures four executable helpers: preflight, template validation,
repository policy and thesis_contract. The actual run reports the percentage;
the earlier 97.74% three-tool receipts remain historical. Coverage is not a
measurement of Typst layout, policy correctness or human usability.

## Input and precedence

The independent dimensions are purpose, layout, double_sided, identity, output,
pdf_standards, language and label_locale. Metadata and approval_refs are distinct.
A print layout does not imply examination or deposit purpose.

Values resolve in this exact order:

1. Built-in defaults.
2. Defaults for the highest-precedence selected layout.
3. Metadata-file values.
4. Typed CLI overrides.
5. Explicit function arguments.

Objects merge recursively; arrays and scalar values replace the prior value.
Every supplied layer is validated before applying overrides, so a malformed
lower-priority value cannot be hidden. An absent value differs from explicit false,
zero, an empty optional collection or an allowed null. These candidate fields are
new; the existing renderer's parameters are not silently reinterpreted.

Create a JSON file containing a configuration patch, for example:

~~~json
{
  "layout": "print",
  "double_sided": false,
  "metadata": {
    "title": "Synthetic working title",
    "author": {"student_record_name": "Synthetic Student"}
  }
}
~~~

Normalize it with:

~~~sh
python scripts/thesis_contract.py normalize \
  --metadata metadata.json \
  --set double_sided=false \
  --set metadata.declarations.word_count=1200 \
  --output build/normalized-configuration.json
~~~

String fields remain strings. Boolean/numeric/array/object overrides use their
declared JSON types. Duplicate or overlapping assignments, duplicate JSON object
members, nonfinite numbers, unknown fields, invalid enums, invalid calendar months
and incorrect ORCID check digits are rejected. Inputs are data and are never
evaluated as Typst or Python code.

Drafts report missing metadata without inventing it. Non-draft purposes reject
missing/known-placeholder required values and blind identity. Language differs
from label locale: a non-English final-purpose input requires an English summary
and a reference for the relevant human decision. A decision reference remains a
human-review-required diagnostic; its presence is not verified approval.

The normalized configuration hash uses SHA-256 over UTF-8 JSON serialized with
sorted keys, separators (comma, colon), ensure_ascii=False and allow_nan=False.
This is the reference Python encoding recipe, not a claim of RFC 8785
canonicalization. Adapters consume the emitted normalized bytes and digest.

Normalized author data is internal input. Do not automatically include it in
blind-review or public-deposit packages; those projections belong to #23/#24.

## Adapter interface and result binding

An adapter consumes an exact manifest digest, a fixture ID/digest and the already
normalized configuration. Pin both the repository revision and contract digest.
A generated vendored bundle must retain every file and source identity, and must
pass the same inventory/hash check; editing a copied policy creates drift.

~~~sh
python scripts/thesis_contract.py \
  --contract contracts/thesis/v1 \
  --contract-sha256 ACTUAL_MANIFEST_SHA256 \
  check --report build/contract/report.json
~~~

The result schema separates source/fixture/configuration identities, engine and
adapter versions, requirement applicability, implementation state, executed
outcomes, human decisions and artifact hashes. Both current adapters are planned,
so they cannot claim executed results. A retained native report may accompany an
unexecuted record without changing its state.

Validate a produced result against its expected source and artifact directory:

~~~sh
python scripts/thesis_contract.py validate-result result.json \
  --expected-revision ACTUAL_SOURCE_COMMIT \
  --artifacts-root build/adapter
~~~

Unknown/stale contract, fixture or adapter identities; a self-consistent hash for
the wrong configuration; missing or unrelated requirement/source references; contradictory
states; missing evidence; and missing/changed/escaping artifacts fail. Actual
execution claims require an implemented adapter, clean declared source, command,
exit status and bound evidence. Result validation checks those bindings; the
producer still needs independent semantic/output tests. No institutional,
scientific or human decision is inferred from an automated pass.

The LaTeX consumer is
[companion issue #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18).
Its minimal metadata/order/invalid-input slice can now target this API. Full
CON-03 acceptance requires real execution by both engines; this increment does
not close it or create a second LaTeX policy.

## Versioning and rollout

The manifest is a candidate schema/API version, not a published thesis-template
release. Reviewed repository files define this executable candidate; the retained
parent contract continues to govern delivery obligations beyond it.

Breaking field, default or meaning changes require a major contract version or an
explicit migration. Compatible additions use a minor version; clarifications use
a patch version. A policy-source change gets its own dated ledger update and
reviewed semantic diff, followed by the affected acceptance cases.

No aliases are deprecated in this initial candidate. Any future alias needs a
documented replacement, removal version and collision behavior; do not treat a
canonical field and its alias as two independent overrides.

Rollback selects a previously qualified engine/compiler/template-revision/
contract-digest/fixture-manifest tuple. No tuple is invented in compatibility.json.
The existing template remains usable while these adapters are qualified.

See the [Conductor track](../conductor/tracks/umthesis_v1_20261115/index.md) for
implementation order and outstanding execution gates. Historical docs/tasks.md,
tasks.md and the companion todo.md are mapped by the crosswalk and ledger; their
old completion counts are not the current programme status.
