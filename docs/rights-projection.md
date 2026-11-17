# Pre-render rights projection — bounded implementation

This helper implements a deliberately narrow part of
[DEP-01/02](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/23).
It constructs a **new, disjoint Typst input directory** from a private manifest
whose independent entries are UTF-8 literal text. For `deposit-public`, entries
marked `restricted` are replaced with an explicit generic omission paragraph
*before rendering*; the original text, source paths, item IDs, rights ledger
and private manifest are not copied or emitted into the public directory.

This is **not** an automatic copyright determination, free-prose anonymizer,
PDF redactor, PDF/UA/archival validator, binary/PDF attachment processor, or
University submission/deposit tool. It does not preserve full-vs-public PDF
pagination. Do not use it to certify a complete thesis or release before the
remaining #23 and #19 acceptance cases have executed.

## Input

Keep the private manifest, source directory and resulting examination build in
an access-controlled location outside the public repository and CI. Only
synthetic fixtures belong in public tests. Use a JSON object with
`schema_version: 1` and a nonempty `items` array. Each item must have
exactly `id`, `source`, `kind`, `visibility`, and `sha256`.

- `id`: unique opaque lowercase identifier, never exported.
- `source`: unique normalized relative path under the source root, with no
  symlinks (including parent components), traversal, absolute paths or NUL.
- `kind`: currently only `literal-text`.
- `visibility`: `public`, `restricted` or `unresolved`. **Unresolved
  blocks both outputs** and must be reviewed outside the tool.
- `sha256`: lowercase SHA-256 digest of exact source bytes. All referenced
  bytes are checked before any public output is created.

The manifest must record rights decisions elsewhere, with authority, scope,
expiry and use permitted; the projection tool does **not** authenticate them.
The entry order determines the order of generated paragraphs.

## Usage

```sh
python -m scripts.rights_projection \
  --manifest /private/rights.json \
  --source-root /private/sections \
  --destination /tmp/thesis-public-projected \
  --target deposit-public

python -m scripts.rights_projection \
  --manifest /private/rights.json \
  --source-root /private/sections \
  --destination /private/thesis-examination-projected \
  --target examination
```

The output directory must not exist and must not overlap the source tree.
Each successful projection produces only `main.typ` and `projection.json`.
For a public variant, do not include the original source tree, unfiltered
logs, full provenance receipt, private input paths or a copy of the manifest in
any distributed bundle. Compile only from the sealed output tree, with compiler
root and dependencies confined to the reviewed tree; **re-check the final PDF**
and every distributed surface for restricted material before any release.

`main.typ` contains `#par("...")` calls with every included passage encoded
as a Typst *string literal*. Authored Typst markup is never evaluated. Embedded
figures, equations, citations, raw `.typ` modules and document metadata are
**unsupported** rather than silently included. Submission-ready layout,
bibliography, rights attachments, pagination and alternate representations
are the next work in #23, #19 and #24.

## Tests and evidence

```sh
python -m unittest tests.maintenance.test_rights_projection -v
make verify-python
```

Negative cases cover unknown permissions, stale hashes, symlinks, traversal,
unsupported binary content, duplicate sources, unsafe destinations, injection
tokens and the complete public output inventory. A passing test qualifies this
source-selection interface only. The existing `make verify` and exact-head CI
still govern repository acceptance; no extra mandatory reviewer or paid service
is introduced.
