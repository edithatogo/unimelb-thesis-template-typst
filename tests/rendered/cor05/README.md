# COR-05 optional-section corpus

These synthetic fixtures exercise the legacy `thesis(...)` optional-section
interface. The canonical runner is `scripts/verify.py`; this directory contains
fixture inputs and independent PDF/diagnostic assertions, not another build gate.

The bounded corpus contains **47 cases**: **21 rendered documents** and **26
intentional typed or private-log rejections**. The rendered documents include the
two standalone public examples and an imported compatibility Preface caller.
Expected rejections require exit 1, exactly the intended diagnostic, no timeout,
no new/stale PDF, and no interpolation of the private sentinel values.

The observations distinguish:

- Publication records alone activating the Preface, independently of free prose,
  with one real register, each citation once and no template-owned demo/chapter assertion.
- Human/digital/AI assistance, prior work, funding and creative records rendering
  their declared public values with the expected cardinality.
- Preface, Funding and Acknowledgements occupying the correct physical order,
  with native bookmarks pointing to the actual heading pages.
- A publication flag producing no creative declaration, minimal creative records
  producing a neutral clause, and an aggregate split appearing only for an
  explicitly supplied valid pair. Record proportions never infer a split.
- Legacy public summaries remaining intact, metadata overrides replacing arrays,
  explicit empty overrides suppressing sections, and invalid earlier layers
  remaining invalid.
- Bookkeeping references, private prompt/output sentinels and record/resource IDs
  being absent from captured visible text, native PDF objects and XMP.
- Wrong record/container types, unknown/missing fields, malformed identifiers,
  non-adjacent duplicate resource IDs, invalid kinds/proportions, incomplete or
  inconsistent pairs, booleans, infinities and NaN failing closed.

The blind authored-record specimen deliberately retains four identity markers in
public descriptions. Its `public_surface_scan.result` must remain `fail`; its
regression pass says that the leak was detected. The reviewed-wording control must
have no declared identity markers in the captured visible/native/XMP surfaces.
Neither result certifies anonymity or makes internal provenance safe to publish.

The fixed creation timestamp is `1794700800`. Every compile and PDF/text/native
capture retains a 60-second command budget. Reports record the exact source,
fixture, input, sample, command-log and artifact hashes; stale outputs are removed
before a case runs. A report starts failed/unexecuted and only passes when every
expected case and assertion is present. Existing COR-01/02/03/04 and terms corpora
remain in the same verifier.

See [the public interface and migration guide](../../../docs/optional-sections.md)
for accepted fields, the private-log migration and limits. No policy/RTP wording,
approval decision, media packaging, full contract-adapter support or general
identity detector is claimed by these fixtures.
