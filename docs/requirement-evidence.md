# Requirement evidence foundation

This is a bounded implementation for [issue #22](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/22),
EVD-01 and EVD-02. It produces an internal, hash-bound receipt from an existing
native verification report and the seeded property report. It also verifies a
receipt against an independently supplied wrapper digest and the exact clean
source checkout.

The result is **partial** or **fail**. This foundation cannot issue full programme
acceptance, institutional approval, or a blind-safe delivery claim. A passing
regression corpus remains a bounded observation. The canonical requirement
catalogue still records planned acceptance cases; this tool does not rewrite it
or silently qualify the shared Typst/LaTeX contract.

## One central wrapper, a separately versioned sidecar

The wrapper uses the existing central
[verification-receipt schema v1](https://github.com/edithatogo/repository-standards/blob/e195af3b0f46db74e797c5bf2e177b7882085186/schemas/verification-receipt.schema.json).
Its exact bytes already reside in the canonical contract's source snapshots. The
helper checks that file's SHA-256 and Git blob identity. There is no second estate
wrapper schema. The [evidence source ledger](../evidence/v1/sources.json) records
the original planning pin, contract pin and dated current-tree observation; all
three refer to the same central schema blob. Central changes remain under the
[existing owner issue](https://github.com/edithatogo/repository-standards/issues/19).

The thesis-owned [profile](../evidence/v1/manifest.json) separately pins a request
schema, status-sidecar schema, adapter registry and source ledger. The output is:

| File | Meaning |
| --- | --- |
| `verification-receipt.json` | Central v1 wrapper; only central fields, with hashes for every declared artifact |
| `requirement-status.json` | Independently versioned thesis status and provenance sidecar |
| `requirements.md` | Deterministic readable view of all 51 stable requirement IDs |
| `artifacts/…` | Exact copied native report, property report and their supported declared artifacts |
| `source-before/`, `source-after/` | Bounded local Git probe logs |

The original `build/verification/report.json` is copied unchanged. Its v1
interface and existing `passed` meaning are preserved; the central wrapper does
not replace it or reinterpret a successful compiler exit as thesis approval.

## Source, artifact and time binding

The caller supplies the repository, full commit and tree IDs, trusted native and
property report hashes, and explicit `not_before` and `review_by` timestamps.
Production checks the actual Git root, revision, tree, clean working state and
every tracked regular file against its Git blob. It also checks all pinned
contract files against that source inventory. Links, submodules and unmerged
entries are unsupported in this first source-inventory profile.

The native report must name the exact clean commit. Equal trees do not substitute
for equal commits: execution reported for one commit cannot be relabelled as an
ancestry-only merge with the same tree. Its start and finish must fall within the
requested window, and it must use the manifest's compiler pin and the existing
60-second command budget. Required documents, corpora, tool identity fields,
command records and supported declared files must be present and consistent.

The consumer hashes and parses the same captured wrapper and JSON buffers. The
producer copies the same artifact bytes it checked. The wrapper, status sidecar,
readable report and copied artifact inventory are reconstructed independently
from the preserved native inputs and exact source. A rehashed forged status,
missing requirement, altered source clause, changed output, expired review
window, duplicate artifact or unrelated commit is rejected. The helper also
checks for source and artifact changes during the operation.

All subprocesses use the existing bounded verifier runner. It retains the
60-second deadline and existing failed-command process cleanup. The helper
saves and restores runner globals for in-process callers. Output writes stay in
a dedicated directory under `build/requirement-evidence/`, reject symlink and
hardlink output aliases, and cannot overwrite declared input evidence. Consumer
probe directories are checked against the wrapper and every declared artifact
before any log is written. A failed production attempt replaces a previous
receipt with a failure stub and removes its old status/readable sidecars when
the output location can be used safely.

These checks establish byte identity and consistency with the supplied trust
anchor. They do not authenticate who ran a compiler, attest the host, rerender
the PDF, or provide a cryptographic signature. Do not obtain the trusted wrapper
digest solely from an untrusted copy of that same bundle.

## Requirement status and applicability

Each of the 51 rows retains its pinned source URL, clause, retrieval timestamp
and source hash. It separates:

- Programme delivery obligation, which remains required for every stable ID.
- The canonical applicability predicate and its assessment in this evidence
  scope. Programme-wide and Typst/PDF predicates apply to this profile. Purpose,
  identity and other output-projection predicates remain **unassessed**, because
  the legacy multi-fixture report does not supply one canonical configuration.
- Registered implementation state from the canonical acceptance-case catalogue.
  A `planned` registration does not assert that no bounded implementation exists.
- Bounded observations from recognized native corpora, including failures.
- The whole requirement result, which remains blocked, unexecuted or failed.

The helper never marks an untested feature unnecessary merely because this run
selected another output. For example, passing a blind-output fixture does not
make the whole receipt blind-safe, and a draft PDF does not qualify submission
policy. Human decisions and scoped exceptions remain explicitly uncollected or
unsupported; no second reviewer or new approval gate is introduced.

## Gaps carried explicitly

The seeded property report records measured source bytes, seed, counts and
elapsed time. Its legacy interface contains no intrinsic source commit or run
timestamps. The sidecar preserves those source-byte observations but leaves
exact-revision execution uncollected. Attaching the file beside a dated native
report does not fill that gap.

The shipped legacy documents do not expose one canonical normalized
configuration. Configuration and its digest therefore remain null. Native tool
versions and binary hashes are preserved as reported observations; font-source
identity, a complete environment lock and replay qualification are not inferred.
Referenced native JSON files are preserved by hash, but nested third-party and
future schemas are not automatically interpreted.

Optional coverage, accessibility, policy, replay or normalized-configuration
sidecars can be attached with their version and exact digest. Until a semantic
adapter is registered, their status is **unsupported**, including when the caller
marks them required. Their internal pass or approval strings cannot promote the
receipt. Their absence or changed bytes still fails when they are declared.

The complete bundle can contain source names, command paths, identity-bearing PDF
text and other private material. It is **internal provenance**, not a sanitized
public archive or reviewer-safe manifest. EVD-03 privacy/archive work, SCI-01/02,
deposit, accessibility and reproducibility acceptance remain open, as does full
EVD-01/02 acceptance beyond this foundation.

## Use

Run the normal verifier in a clean, committed checkout first. Create a request
matching [the strict request schema](../evidence/v1/request.schema.json), with
actual report hashes and an explicit execution/review window. The required paths
are relative to `--source-root`. Do not put the request or its inputs inside the
output directory.

```sh
python scripts/requirement_evidence.py produce \
  --request build/evidence-request.json \
  --source-root . \
  --output build/requirement-evidence/current

python scripts/requirement_evidence.py verify \
  --receipt build/requirement-evidence/current/verification-receipt.json \
  --source-root . \
  --expected-revision FULL_EXPECTED_COMMIT \
  --trusted-sha256 INDEPENDENTLY_RECORDED_WRAPPER_SHA256
```

Exit 0 means a consistent **partial** receipt was produced or verified. Exit 1
means valid evidence records a failure. Exit 2 means malformed, missing,
tampered, stale or unsupported structural input prevented verification. No exit
code means submission approval. Receipts are bound to the producer's content hash
and pinned profile; use the matching version when consuming historical evidence.

The new maintenance tests are discovered by existing `make verify-python` and
`make verify`. They use small, isolated local Git repositories and explicitly
synthetic report bytes. They exercise real file identity and write guards; their
non-PDF byte specimens are never represented as compiler output. Actual native
consumer demonstrations use separately retained clean-source reports. This
increment adds no native corpus and does not change the current verifier report.

`scripts/requirement_evidence.py` is included in the measured coverage scope,
retaining the existing 80% floors and zero excluded lines. Its test coverage
measures helper correctness; native PDF and programme acceptance have their own
evidence.

## Post-build consumer controls

The existing `Verify template and properties` job invokes
`tests/evidence/qualify.py` after `make verify` has finished. This preserves the
completed native report and avoids a self-referential receipt. The driver records
the exact checkout, native and property digests, and eight consumer controls:
an intact partial receipt, an unrelated revision, an expired window, an untrusted
wrapper digest, changed PDF bytes, a missing PDF, a rehashed false requirement
pass, and a missing required sidecar. Its own orchestration tests run separately.

The automation window begins at the native report's start and ends seven days
after its finish. This is a freshness limit for the automated observation, not a
human review or institutional approval. Policy and replay reports declared by
that native run are attached by exact digest with unsupported semantic-adapter
status. An explicitly unexecuted corpus without a report declaration stays
unexecuted in the copied native report. A partially declared, missing or changed
attachment fails the controls.

Each qualification needs a fresh `negative/` directory. Existing negative
evidence is rejected before probes or copying, preserving its contents. An early
failure still replaces a stale qualification success with a failed report when
that report path is safe. The positive bundle remains separate from deliberate
tamper specimens. CI retains both under `build/requirement-evidence/`; these are
internal evidence and are not approved public or blind-review deliveries.
