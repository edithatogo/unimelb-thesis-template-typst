# Dated Melbourne submission-policy data checks

This is a bounded foundation for **UMTHESIS-1.0.0 POL-03 through POL-07** and issue
[#17](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/17).
It validates supplied records and local file identities. A successful data result
leaves the overall result **partial**, all human decisions outstanding, and
`submission_approved: false`. It does not establish that a thesis is ready to submit.

## Authority and source identity

The profile in `policies/unimelb/2026-11-15/` records primary sources retrieved on
**15 November 2026, Australia/Brisbane**. `sources.json` retains the URLs, UTC
retrieval timestamps, HTTP results, exact byte lengths and SHA-256 digests.
`rules.json` maps the bounded interpretations to clauses. The original retrieved
HTML is retained in the development evidence, outside the Git tree; full webpages
are not redistributed in the package.

The sources are the University’s [preparation requirements](https://gradresearch.unimelb.edu.au/processes/preparation-of-graduate-research-theses),
[writing guidance](https://gradresearch.unimelb.edu.au/preparing-my-thesis/writing-and-preparing-your-thesis),
[publication guidance](https://gradresearch.unimelb.edu.au/preparing-my-thesis/thesis-with-publication),
[submission process](https://gradresearch.unimelb.edu.au/examination/submitting-your-thesis), and
[library deposit guidance](https://gradresearch.unimelb.edu.au/examination/my-thesis-in-the-library).
The preparation page displayed version **5**, while its latest history row named
version **6**, dated 17 June 2026. The profile preserves both observations and does
not invent a resolved effective version. Policy currentness remains a human task.

`manifest.json` binds all five profile/schema/ledger files. The checker pins that
manifest’s digest. Changing a threshold, schema, source observation or rule therefore
requires an explicit reviewed profile change; there is no command-line maximum or
policy-bypass option. The existing canonical contract bundle remains separately
pinned and unchanged.

## Inputs and precedence

`scripts/submission_policy.py` accepts one strict JSON request conforming to
`request.schema.json`. Duplicate keys, non-finite numbers, unknown sidecar fields,
incorrect types and invalid calendar dates are rejected.

The `layers` object contains `metadata`, `cli` and `explicit`. These feed the existing
canonical normalizer, which supplies its defaults and selected profile. The effective
order is **defaults → profile → metadata → CLI → explicit**. Each supplied layer is
validated before merging, so a valid later value cannot conceal an invalid earlier
one. CLI values use the existing `key=JSON` interface. Boolean false stays a boolean.

The separate `policy` object supplies evidence that the shared metadata schema does
not model. It does not extend that schema or switch the renderer. Its sections are:

| Section | Supplied data checked |
| --- | --- |
| `word_count`, `course_rule` | Component inventory, exclusions, count adjustments, selected course source and scoped excess decision |
| `creative` | Canonical output IDs, descriptions, matching electronic/durable files and agreed proportions |
| `funding` | Explicit completeness, per-funder grant applicability and RTP applicability |
| `prior_work`, `assistance` | Indexed disclosures, editing roles, verification records and private log references |
| `publications` | Official status, location/version, contribution data, rights, separate form records and bibliography/integration plans |
| `submission` | Written-file inventory, exact-PDF originality/review records and final-deposit decisions |
| `documents`, `decisions` | File identity and typed, dated, scoped decision records |

Indices refer to the final normalized metadata arrays. Duplicate, missing or extra
indices do not silently remap records. Publication and creative IDs must agree with
the final canonical configuration.

### What the conditional checks mean

The University distinguishes course maxima from recommendations, includes footnotes
in the count, and permits specified exclusions. The profile keeps those concepts
separate. Its component counts are supplied data; it does not claim to count the
actual PDF. Adjustments need a recorded reason and author decision. An adjustment
does not replace an institutional excess approval. The selected course source and
any approved numerical scope remain subject to human interpretation and authentication.

Thesis language is independent of label locale. Conditional summary, creative and
RTP checks follow the dated clause ledger. The RTP wording and DOI exist once in
`profile.json`; fixtures substitute that literal. A fee-offset flag activates the
same check. Unknown funding applicability is blocked, rather than treated as absent.

The official publication statuses include `in-revision`. Canonical v1 has no
equivalent enum member. The sidecar preserves that status and reports
`canonical_publication_bridge: unsupported-in-revision`; it does not present a
placeholder canonical value as a faithful rendering bridge. Overlapping contribution
roles need not total 100. An explicitly supplied exclusive partition must name the
recorded contributors and total 100. This is arithmetic/data consistency, not a
judgment of substantial authorship.

Publication forms remain separate records; declared signatures are not verified
signatures. The figure-only case has its explicit form exception. Bibliography inputs
are named `planned_*`: they cannot establish observed PDF content. Matching-source
filters are checked against the supplied incorporation categories, while similarity,
originality and scholarly integration remain human assessments.

### Evidence is not approval

Each evidence file has a relative path, SHA-256, kind and classification. Files must
stay inside the explicit evidence root, cannot be symlinks, and must differ from the
thesis PDF. Matching bytes establish identity only. A synthetic document can exercise
validation without becoming an actual approval or licence.

An accepted decision record must have the intended kind, authority label, state,
dates, course, purpose and relevant numerical/language/publication/PDF scope. The
subject digest binds the supplied student-record name; it does not authenticate an
individual. Every such record still appears on the outstanding authenticity checklist.
The tool never infers a signature, institutional authority or consent from an arbitrary
file or a caller’s `approved` string.

Private assistance logs, signed forms and other evidence are referenced, not copied
into reports. Reports are nevertheless marked **internal-not-reviewer-safe** because
record IDs, hashes and applicability can themselves reveal information. They must not
be treated as a blind-review attachment.

## Run the checker

Use the repository’s pinned Python dependencies. Supply a real PDF and a policy request:

```sh
python scripts/submission_policy.py \
  --input /private/request.json \
  --pdf /private/thesis.pdf \
  --evidence-root /private/evidence \
  --report build/submission-policy/report.json \
  --as-of 2026-11-15
```

The default assessment date uses Australia/Brisbane time. The PDF’s bytes and actual
filename are read from disk; a caller-supplied digest is never used instead. This helper
checks the PDF header and file identity only, and reports `pdf_structure: unexecuted`.
Independent compilation/structural validation belongs to the native verification gate.

| Exit | Meaning |
| --- | --- |
| `0` | Supplied-data checks passed; overall result is still `partial` |
| `1` | One or more applicable supplied-data checks failed |
| `2` | Input, configuration, artifact, pinned profile or report handling prevented validation |

Reports are restricted to `build/submission-policy/`. Output aliases, links and attempts
to replace an input/evidence file are rejected. A previous success is replaced before
evaluation. Report-write failure cannot return success. A missing or malformed PDF
cannot acquire a successful checklist.

Every checklist item is bound to the actual PDF SHA-256 and remains
`human-review-required`. Changing the PDF invalidates supplied supervisor, originality,
author-verification and final-decision bindings where applicable. No user-supplied
section-order or rendered-observation string is accepted as an alternative to inspecting
the output.

## Bounded validation corpus

The **64 synthetic scenarios** under `tests/policy/fixtures/` have exact intended
outcomes: 27 data-valid cases and 37 intended data failures. Those failures are useful
negative controls, not clean or approved documents. The fixture manifest binds each
file’s bytes. `applicability-matrix.json` maps 25 conditional checks to satisfying,
missing/invalid and not-applicable cases. It separately lists unconditional,
unexecuted, unknown-applicability and unsupported behavior.

The maintenance tests exercise layer precedence, strict types, policy tampering,
decision scope/dates, evidence aliases, changed PDF bindings, privacy and stale reports.
Run them with:

```sh
python -m unittest discover -s tests/maintenance -p test_submission_policy.py -v
```

The separate bounded native fixture gate is:

```sh
python tests/policy/verify.py
```

It uses the existing 60-second command runner and manifest-pinned Typst, compiles one
neutral synthetic page, checks it with qpdf/pdfinfo/pdftotext, and then binds all 64 data
scenarios to those actual PDF bytes. It verifies exact failure sets, outstanding-review
bindings, unchanged source/artifact identities and fresh reports. The neutral page does
**not** render the 64 metadata requests. Its successful compilation establishes no
policy compliance. The fixture runner also restores the shared runner’s state when
invoked in process.

## Integration and remaining acceptance

The canonical verifier invokes the fixture gate in process after the existing
209 rendered/native/package cases. Its report keeps the 64 supplied-data scenarios
in a separate `submission_policy_corpus`, with `rendered_policy_qualified: false`
and `submission_approved: false`. The existing shared metadata schema, workflows,
check names and command/process deadlines are unchanged.

`scripts.submission_policy` is the eighth measured Python helper. Both existing
80% coverage floors remain in place, with no exclusions. The policy helper's line
and branch coverage cannot establish rendered compliance or approval authenticity.
Source and receiving qualification require their own actual canonical and hosted
results; earlier isolated policy results retain their original candidate identity.

Issue #17 remains open. This slice does not qualify POL-01/POL-02 geometry, title and
front-matter order, abstract wording/length, logo/signature absence or pagination. It
does not inspect disclosure or bibliography rendering, derive a real thesis word count,
authenticate any approval, execute the LaTeX lane, register both-engine canonical
acceptance, operate TES, or prove final deposit/access arrangements. Full applicability
and boundary fixtures for the remaining clauses, actual rendered observations and
the required human decisions are still separate work. A later policy observation must
retain its own date and reviewed source identity.
