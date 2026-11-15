# Local packaging and author starter

## Current scope

This is the bounded PKG-01/02/03 increment of
[issue #21](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/21).
It supplies a curated local archive/install interface, a separate six-file author
starter and executable packaging checks. It keeps the existing package name,
version and Apache-2.0 decision. It does not close the full packaging issue.

The current reconstructed candidate is composed on adapter/native PR #32 source
`3f540359796802a873a9c2ff5392d2cf297c8dc3`, which retains the repaired correctness
PR #31 base `3086863a1ddc3a699d172a10132a183b22979192`. Its newly reconstructed helper,
tests, starter and harness require their own source and receiving CI. The local
checks below apply to the measured candidate bytes; the earlier prototype's
results do not qualify reconstructed files.

## Manifest and payload

`typst.toml` keeps package version `0.2.1` and the exact repository build pin
`0.15.1`, adds compiler floor `0.15.1`, uses the supported `thesis` category,
and omits discipline restrictions for a generally applicable thesis template.
The starter now lives at `template/main.typ`. Manifest exclusions identify
repository tooling, evidence, generated output and font payload separately.

The local builder uses an explicit 50-file allowlist: 39 existing runtime and
compatibility modules, five root metadata/documentation files, and six author
files. It includes the root README, citation metadata, executable README example,
manifest and Apache licence. It retains public compatibility module paths.
It excludes repository CI, tests, source evidence, caches, font binaries and
archives. The font tree remains unchanged in the source repository.

The archive has deterministic file ordering, permissions, ownership metadata,
timestamps and gzip metadata. Its receipt records every member's byte count and
SHA-256, plus the actual archive hash. Installation verifies those values and
rejects missing/unexpected/duplicate members, non-regular files, traversal,
symlinks, inconsistent identity and an already installed version. Archive and
receipt destinations are checked together before writes, including hardlink
aliases to source or each other. Existing files under the selected source root
are protected even when excluded from the archive, including scripts, guides and
the thumbnail. Only the top-level `build/`, `dist/` and `target/` directories
are treated as generated output areas; their ordinary outputs can be rebuilt.
External archive/receipt destinations remain supported, but hardlinks to
protected source are rejected wherever the alias is placed.

The reviewed local archive profile is narrower than a claim that every rule of
a future Universe submission has passed. The official registry applies its own
submission, naming, rights and publication review.

## Resource ownership and fonts

The initialized author project imports `@local/unimelb-thesis-template:0.2.1`.
Its native bibliography path and nested image path are resolved in the caller's
project. Replacing or relocating those author files must change the actual
consumer output without accessing repository-relative resources.

The starter explicitly selects the existing `classic` theme. The packaging
corpus uses `--ignore-system-fonts` and records PDF font names/embedding and
environment flags. It does not certify per-face font source bytes, every font
theme, every writing system or a locked rendering environment. See
[the font inventory and limits](fonts-and-package-payload.md).

## Executable checks

The packaging module runs through the existing canonical verifier and its
unchanged 60-second command budget. It does not create another workflow or
required check. Existing document, correctness, adapter and native gates must
remain present when the small additive hook is integrated.

| Case | Required observation |
| --- | --- |
| Archive, install and initialization | Deterministic archive, exact receipt, fresh local package, exactly six author files and a real PDF |
| Library import | An isolated project imports the installed package |
| Relocation | The moved author project preserves its text |
| Nested image edit | Blue pixels become red in the actual image page |
| Bibliography override | The new caller-owned reference title appears and the old one disappears |
| Added chapter and draft input | The new chapter renders with the explicit CLI profile selected |
| Missing resources | Intended image and bibliography errors, exit 1 and no stale PDF |
| Watch and edit | Native completed builds, retained initial/final PDFs and the authored edit in the new output |
| README example | The executable root example compiles with its literal sentinel |
| Thumbnail | The committed image equals a fresh native render of the initialized starter |

Every actual command retains argv, exit status, diagnostics, deadline and log
hash. Package files, native output, assertions and source-before/after identities
are retained. Watch uses the canonical process group and has bounded inner waits;
it does not create an independent session that could escape the owner deadline.

The production archive/install helper is the seventh measured Python helper
after the separate adapter/native integration. Its 21-method unit
suite covers real file mutations, archive tampering, aliases and namespace
containment. The native orchestration is outside that coverage component.
Existing project and patch coverage floors stay at 80%; no exclusions are added.

## Real thumbnail recovery

The manifest points to `thumbnail.png`, a render of page 1 of the initialized
starter. It is not a fabricated illustration. The default gate fails if it is
missing or differs from the newly rendered image.

When recovering an unavailable binary, run this explicit bootstrap command
in the pinned local or existing hosted environment:

```sh
python3 scripts/verify_package.py --recover-thumbnail
```

It builds/installs the actual candidate, initializes the starter, and executes:

```sh
typst compile --root <author-project> --package-path <installed-packages> --ignore-system-fonts --creation-timestamp 1794700800 --format png --pages 1 --ppi 150 <author-project>/main.typ <output>/rendered-thumbnail.png
```

The command emits SHA-256, byte count and base64 between
`BEGIN_TYPST_PACKAGE_THUMBNAIL_BASE64` and
`END_TYPST_PACKAGE_THUMBNAIL_BASE64`. The encoded payload is limited to 512 KiB;
native PNG dimensions must meet the registry's 1080-pixel minimum longer edge and
its file limit. The recovery receipt is explicitly `generated-unqualified` with
`canonical_gate_pass: false`. Inspect the actual image and commit those exact
bytes, then run the complete canonical gate. Bootstrap success is not a gate pass.

## Current local observations

On 15 November 2026 (Brisbane), the initial reconstructed helper's 18 unit methods passed
on Python 3.15.1. Coverage.py 7.17.3 measured 199/201 statements and 78/80 branches,
98.57651245551601% combined, with zero exclusions. This measures only
`scripts/package_template.py`, SHA-256
`c6a45a4585f215ecad1588560a4c07026192b73feab18fd86475d5674724fa39`;
the combined seven-helper gate remains a separate report.

The actual ten-case packaging run passed all 18 assertions with source hashes
unchanged, completing at `2026-11-15T02:39:20.739044Z`. Its report SHA-256 is
`0de4b928ca69ba0f29c891b0eb67c77d16bdc21c36bd31235195f1f22df4b6b2`.
The tested archive contained 50 files and 181,150 payload bytes, compressed to
49,323 bytes; initialization produced six author files totaling 15,534 bytes.
The native commands used Typst 0.15.1, disabled system fonts and used a separately
provisioned ordinary package cache. This does not establish a cold-cache pass.

The committed thumbnail was rendered from that initialized starter and visually
inspected. It is 1240 by 1754 pixels, 86,616 bytes, SHA-256
`0ca4a7ff1aa9cdaa7bfc134cfcba42512ec9db0c1156f1852bb02fba12c4da74`.
The initial absent-thumbnail gate failed as intended and remains retained.
A later preparation race changed the thumbnail during verification; its
source-stability check correctly failed despite all ten semantic cases passing.
That failed run is retained separately from the subsequent unchanged-source pass.

Receipts, commands, logs and the earlier failures are under
`build/package-recovery/`; native results are under `build/package-focused/`.
These local observations do not replace the complete canonical gate or the
actual proposed and receiving revisions' hosted checks. They do not establish
registry acceptance or closure of issue #21.

A subsequent root review demonstrated that this initial helper protected only
archive payload files: archive/receipt destinations could overwrite excluded
repository source, including through hardlinks. Eight isolated CLI reproductions
confirmed that defect without changing the retained candidate. The current guard
also protects existing non-payload source and adds three regression methods for
direct/aliased writes and ordinary rebuilds. The 18-method and ten-case observations
above remain evidence for the earlier helper hash, not qualification of this
correction; the corrected source requires its own full verification and coverage.

## Retained historical observations

Before the workspace disconnect, a different local prototype completed ten unit
methods and ten native cases with 25 assertions. Its helper coverage was
152/175 statements and 62/84 branches, 82.62548262548262% combined with zero
exclusions. That prototype's archive contained 50 files, 181,857 payload bytes
and 49,665 compressed bytes; its six-file starter occupied 14,998 bytes.
Those values are historical and must be remeasured for this new candidate.

The earlier cold-cache compile exceeded the unchanged 60-second gate budget.
Its receipt SHA-256 was
`1cbf091d6c006783a8e005a5e71028bf8f84e9ddb756876f0bdc717e20f79670`.
A separate, explicitly authorized 180-second provisioning operation produced
`02a3eea01fe6d171e2d63923972ccef2f30b8c8adaf71e531c5323b773062cbc`.
The subsequent 60-second provisioned retry produced
`128e8502370492d9a864ca32daa66c174ae4841d75862d3704e4938975698836`.
The original failure remains a failure. A fresh local package directory does not
establish an empty ordinary dependency cache, offline resolution or complete
environment replay.

The historical final containment/watch refinements were not executed before
the disconnect. The reconstructed suite includes those intentions and the
subsequently reviewed archive/receipt alias correction. The current local
observations above remain separate from those historical results and from
the proposed and receiving revisions' hosted qualification.

## Remaining acceptance

Full release/version synchronization, all required rights and CFF automation,
registry naming/publication approval, exhaustive author examples, web-app
qualification, shared-contract parity, accessibility, locked replay, deposit
packaging and empirical usability retain their existing issue ownership.
The source font inventory is retained; unused assets were not bulk-relicensed
or deleted. Private author data and approval documents are not package fixtures.

The saved `docs/source-material/modern-uit-global.typ` was an actual 404 HTML
page and failed compilation. Its bytes are retained under the truthful
`.html` extension; SHA-256
`01e219e36a6901b8702e61486bcd2c1a7656e66777a007545e26144d54ed0d60`.
Historical receipts keep their original source paths and hashes.

## Primary references

The bounded manifest/resource review used
[typst/packages at 76fcf18](https://github.com/typst/packages/tree/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814):

- [Manifest and thumbnail rules](https://github.com/typst/packages/blob/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814/docs/manifest.md).
- [Caller paths, fonts and resource rights](https://github.com/typst/packages/blob/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814/docs/resources.md).
- [Categories](https://github.com/typst/packages/blob/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814/docs/CATEGORIES.md)
  and [disciplines](https://github.com/typst/packages/blob/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814/docs/DISCIPLINES.md).

The pinned compiler's [CLI arguments](https://github.com/typst/typst/blob/v0.15.1/crates/typst-cli/src/args.rs)
and [watch completion states](https://github.com/typst/typst/blob/v0.15.1/crates/typst-cli/src/watch.rs)
define the native commands exercised here.
