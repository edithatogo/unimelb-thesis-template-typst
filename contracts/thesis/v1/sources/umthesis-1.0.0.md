<!-- typst-foundation-handoff:start -->
## Typst foundation completion — 15 November 2026 (Australia/Brisbane)

The Typst foundation has completed its existing acceptance: [#4](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/4), [#5](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/5) and [#6](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/6) are closed as completed. PRs #10, #12 and #11 are integrated; citation PR #26 is also integrated. Final qualified consumer main is [`f8dafbac5f906fc4b6419266d67a9ae8b319711d`](https://github.com/edithatogo/unimelb-thesis-template-typst/commit/f8dafbac5f906fc4b6419266d67a9ae8b319711d), whose tree matches tested PR #11 source `4aa590eb9bb16a5eb5bc63a0abcc07e2105a6f17`. All applicable final source and receiving checks, including actual Codecov processing, passed. The exact workflow, check, provider and coverage identities are recorded in [#6's completion checkpoint](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/6).

Live ruleset 27266891 matches the versioned policy, including conversation resolution, all eight Actions-bound required contexts, zero mandatory human approvals and owner-only recovery. [Central classification PR #142](https://github.com/edithatogo/repository-standards/pull/142) is integrated and receiving-qualified at `e195af3b0f46db74e797c5bf2e177b7882085186`; it records measured Python helper coverage, Python/Actions CodeQL applicability and the scoped published-artifact profile. These results supersede the earlier Typst foundation status observations below, while preserving the historical baseline and canonical contract.

The 51-requirement document programme and #14–#25 implementation acceptance remain open. This checkpoint does not complete the combined Typst/LaTeX governance checkbox or claim LaTeX qualification. Offline-security PR #9 and central #126 remain separate drafts pending their actual runtime prerequisites; they do not block independent document-contract work.
<!-- typst-foundation-handoff:end -->

## Purpose, authority and status

**Normative planning contract: UMTHESIS-1.0.0. Recorded 15 November 2026 (Australia/Brisbane). Implementation and qualification are pending.**

This issue is the coordinating source of truth for the requested complete upgrade of the University of Melbourne Typst thesis template, its semantic alignment with the [LaTeX companion](https://github.com/edithatogo/unimelb-thesis-template-latex), current Typst capabilities, and the applicable [repository standards](https://github.com/edithatogo/repository-standards). The contract below is defined now; its implementation issue must materialise it as versioned schemas, fixtures and executable checks. Creating or closing a planning issue is not evidence that a thesis, repository control or publication is compliant.

MUST/SHALL requirements are release acceptance obligations for their declared scope. Optional features remain optional for authors; their delivery and qualification remain in this programme. Experimental capability is labelled and isolated. A university requirement, a project quality target and an institutional/human decision MUST remain distinguishable.

### Existing owners and observed baseline

- Original document audit: 6d4652936b4eabaac29462ab8caf86e248c0f96a. Live main advanced to b947d5ea0ad1a9c118a9c3670bcb82200052c9a2 after PR #10 merged on 14 November 2026 at 15:14 UTC; #4 is now closed. PR #12 has been retargeted to main and still requires final-head qualification. Existing [#4](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/4)/[PR #10](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/10), [#5](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/5)/[PR #12](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/12), and [#6](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/6)/[PR #11](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/11) retain generic verifier, CI, security, coverage, governance and integration ownership. This programme adds document-specific semantics and output evidence.
- LaTeX main advanced during planning to 805d7accbeb953aa121ba1d00d30055e8ff939e3. [PR #15](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/15) and [#7](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/7) are delivered groundwork. Reuse its make verify/make replay and [quality contract](https://github.com/edithatogo/unimelb-thesis-template-latex/blob/805d7accbeb953aa121ba1d00d30055e8ff939e3/docs/quality-checks.md). [#8](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/8)/[PR #16](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/16) retain governance ownership; [#9](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/9)/[PR #17](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/17) own remaining integration disposition.
- Standards baseline: [10e59936e132f28597cb7d2f10efa27629dc4837](https://github.com/edithatogo/repository-standards/tree/10e59936e132f28597cb7d2f10efa27629dc4837). Recheck all heads and relevant standards before implementation/merge; PR descriptions can lag actual commits and checks.
- Existing offline-security drafts [Typst #9](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/9), [LaTeX #13](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/13), and [central #126](https://github.com/edithatogo/repository-standards/pull/126) retain their isolated-runner/scanner/model provisioning and real-integration prerequisites. They are a separate conditional lane, not permission to bypass a gate or block all document work indefinitely.
- No new generic hardening tree or second update bot is introduced. Existing central owners include [typesetting #5](https://github.com/edithatogo/repository-standards/issues/5), [validation #6](https://github.com/edithatogo/repository-standards/issues/6), [dependencies/publication #8](https://github.com/edithatogo/repository-standards/issues/8), [gates #17](https://github.com/edithatogo/repository-standards/issues/17), [receipts #19](https://github.com/edithatogo/repository-standards/issues/19), [supply chain #20](https://github.com/edithatogo/repository-standards/issues/20), and [duplicate prevention #76](https://github.com/edithatogo/repository-standards/issues/76).

## 1. Contract boundary and data model

The canonical implementation location SHALL be contracts/thesis/v1/ in this repository, with one versioned manifest, metadata schema, requirement catalogue, source ledger, fixture manifest, expected semantic outputs, result schema and compatibility manifest. The LaTeX adapter SHALL consume a pinned contract version/digest; it must not maintain a divergent copied policy. A generated vendored snapshot is acceptable only with origin/digest and a drift check.

The input schema SHALL distinguish:

- **Purpose:** draft, examination, deposit-full, deposit-public.
- **Layout:** existing default/draft/screen/print profiles, including explicit double-sided behaviour.
- **Identity:** identified or blind-review. Blind review is not automatically a valid examination/deposit mode; reject combinations that conflict with required title metadata.
- **Output:** PDF, experimental HTML, experimental bundle; selected PDF standards are explicit.
- **Language:** thesis language and label locale are distinct. Non-English permission and English-summary applicability do not follow from UI labels.
- **Metadata:** title, student-record author name, ORCID, degree/course, academic units, submission/resubmission month/year, joint award, abstract, declarations, funding/grants, publications/contributions, prior work, human/digital assistance, creative outputs, third-party rights and resource references.
- **Evidence:** actual inputs/artifact identities, source and policy revisions, execution parameters and separate human decision references. Private approval documents, signatures and assistance logs are not embedded by default.

Resolution order SHALL be built-in defaults < selected profile defaults < metadata file < parsed CLI overrides < explicitly supplied function arguments. Unspecified arguments must remain distinguishable from explicit defaults. Resolve once, then pass the canonical value to every renderer. Version and document any compatibility changes; preserve deprecated aliases with diagnostics for a declared transition.

Types, enums, date forms, ORCID syntax/check digit and resource types SHALL be validated. Do not invent metadata or infer authorship/permissions. Unknown keys, malformed booleans/numbers, contradictory modes and unsupported combinations must produce precise errors. Drafts may contain clearly reported missing required author data; examination/deposit qualification rejects missing values and known demonstration placeholders. Policy invariants cannot be weakened through a lower-level styling flag.

## 2. Requirement catalogue and ownership

Each ID is stable. Every row SHALL map to at least one acceptance case, an implementation owner, an applicability predicate and evidence. The final linked issue table maps the owner keys below to execution issues. Splitting a requirement later requires a versioned crosswalk, not silent deletion.

| ID | Normative outcome | Primary implementation owner |
|---|---|---|
| CON-01 | Version the normative contract, source ledger, legacy-requirement crosswalk, migration policy and requirement-to-test-to-evidence map; preserve one canonical owner. | contract |
| CON-02 | Validate typed metadata and independent purpose/layout/identity/language/output dimensions, precedence and invalid combinations before rendering. | contract |
| CON-03 | Both engines consume the same versioned synthetic fixtures and expected scholarly/policy semantics through independent adapters; report unsupported cases explicitly. | contract |
| CON-04 | Version schemas and policy snapshots; distinguish implementation progress, executed results, applicability, unresolved human review and institutional approval. | contract |
| COR-01 | Render declaration clauses, contribution/publication tables and footnotes as intended content, never as source expressions or unfinished placeholders. | correctness |
| COR-02 | Produce populated and correctly linked contents, lists, references, bookmarks, logical page labels, appendices, abbreviations, glossary and index. | correctness |
| COR-03 | Resolve configuration once with documented precedence and typed CLI parsing; propagate layout profile, double-sided mode, bibliography, declaration and assistance fields consistently. | correctness |
| COR-04 | Blind review output removes declared author identifiers from all emitted public surfaces, including declaration, PDF metadata, tags and supporting evidence. | correctness |
| COR-05 | Optional sections render on their own applicability conditions; invalid metadata and unfinished automation produce actionable diagnostics rather than silent fallback or fabricated success. | correctness |
| TYP-01 | Initially qualify Typst 0.15.1 as the latest stable compiler and package minimum, retain the separate exact repository build pin, and recheck latest stable at execution. | typst |
| TYP-02 | Use native multiple bibliographies/targets/groups and typed resource paths where appropriate; verify bibliography scope, numbering and installed-package resource resolution. | typst |
| TYP-03 | Offer an optional licensed variable-font profile with fixed axes, embedding, glyph coverage and math pairing; retain a qualified static profile. | typst |
| TYP-04 | Use fail-closed typst eval and native dependency JSON as validated evidence inputs; supplement path inventories with explicit compiler/font/package/asset hashes. | typst |
| TYP-05 | Maintain a tested compiler/support matrix, migration notes and bounded upgrade canaries; detect layout convergence warnings and relevant semantic/layout regressions. | typst |
| POL-01 | Enforce A4, applicable margins, logical pagination, ordered title metadata and the university prohibitions on logos and signatures. | policy |
| POL-02 | Enforce the prescribed front/core/end-matter order, abstract range and conditional third-party copyright inventory. | policy |
| POL-03 | Implement degree/course-specific word limits, explicit count scope and approved exceptions; never equate a raw source/text count with the institutional count. | policy |
| POL-04 | Handle approved non-English theses and English-summary limits independently of UI locale; validate creative-output description, proportions and durable components. | policy |
| POL-05 | Render applicable funding/grant/RTP acknowledgement, prior work, human editing and digital/AI assistance disclosures; keep private assistance logs separate. | policy |
| POL-06 | Represent publication identity, version/status/location/contributions/permissions and integrated argument; apply incorporated-publication bibliography rules and keep signed forms separate. | policy |
| POL-07 | Generate an exact-artifact submission checklist covering originality report, supervisor review, exceptions, TES naming and final amendments without claiming institutional approval. | policy |
| TST-01 | Use rendered text, metadata, structure and controlled visual baselines as independent oracles; retain minimal regressions for every reproduced audit defect. | testing |
| TST-02 | Exercise the supported profile/feature matrix with bounded seeded properties, negative fixtures and targeted fault injection; record scoped applicability rather than ceremonial test counts. | testing |
| TST-03 | Extend the canonical verifier to reject missing fixtures/tools, stale outputs, swallowed subprocess failures, timeouts and invalid reports; retain deterministic failure evidence. | testing |
| ACC-01 | Preserve semantic headings, tables, figures, lists, citations and equations with language, reading order, usable descriptions and appropriate decorative artifacts. | accessibility |
| ACC-02 | Qualify full examples against an explicit engine-supported PDF/UA plus compatible PDF/A profile using compiler checks, a named external validator and recorded human accessibility review. | accessibility |
| ACC-03 | Reject incompatible standards and unsupported PDF-image embedding combinations; isolate unstable accessibility helpers and disclose target/web-app capability limits. | accessibility |
| REP-01 | Record immutable compiler, package, font, asset and toolchain inputs; demonstrate a clean provisioned offline build without hidden system-font or cache dependence. | reproducibility |
| REP-02 | Control time, locale and nondeterministic inputs; require independently rebuilt byte identity for deterministic-build claims in a pinned environment, failing mismatches, and distinguish semantic repeatability elsewhere. | reproducibility |
| REP-03 | Publish only explicit tagged, qualified artifacts bound to source and evidence hashes; provide checksums, warranted provenance/SBOM, consumer verification and rollback guidance. | reproducibility |
| PKG-01 | Validate official package metadata, compiler floor, resource boundaries, real thumbnail and exclusions; compile a freshly installed starter outside the repository. | packaging |
| PKG-02 | Reduce unjustified font/dependency payload; preserve rights and licence decisions and keep authoritative version, changelog, citation and release metadata consistent. | packaging |
| PKG-03 | Provide tested CLI/web-app authoring, watch/build/verification/migration guides and actionable diagnostics; replace stale completion/compliance claims with evidence-linked status. | packaging |
| EVD-01 | Emit a central-schema-valid verification receipt linking independently versioned native report sidecars, exact source revision, commands and SHA-256 artifacts. | evidence |
| EVD-02 | Generate per-requirement policy/evidence reports with source clause/date/hash, applicability, observed result, artifact binding and separate human decisions. | evidence |
| EVD-03 | Validate and privacy-filter reports, logs and public evidence on success and failure; reject stale, malformed, missing or unrelated evidence. | evidence |
| SCI-01 | Trace each generated result/figure/table to input identity/digest, analysis revision/environment, parameters/seed/transforms, output digest and rights. | evidence |
| SCI-02 | Keep bibliographic metadata checks, citation-support review, reproducibility and scientific validity as separate claims; integrations remain optional, local-first and explicitly network-enabled. | evidence |
| DEP-01 | Produce examination/full/public-deposit variants from explicit permitted content projections, retaining private rights and redaction records outside public artifacts. | deposit |
| DEP-02 | Verify synthetic restricted content is absent from every public output surface and archive, while preserving the declared placeholder/pagination contract. | deposit |
| DEP-03 | Generate a durable deposit package and exact-artifact checklist, keep signed forms and confidential logs separate, and leave permissions/access/embargo decisions explicitly human. | deposit |
| WEB-01 | Provide an opt-in experimental HTML/MathML rendition with equivalent scholarly content and identifiers, usable navigation and separately tested browser accessibility. | web |
| WEB-02 | Qualify opt-in bundle outputs, assets, links, path safety and public-content projection; document CLI/web-app limitations and preserve a stable PDF/deposit route. | web |
| BEN-01 | Predeclare and run a licensed cross-engine semantic/policy benchmark corpus with failures, selection limits and engine-specific output expectations reported. | qualification |
| BEN-02 | Measure cold/warm/watch latency, memory, output size and failure rate on declared hardware; establish justified regression budgets from observed variance. | qualification |
| BEN-03 | Execute novice, experienced-author and assistive-technology task protocols; record completion/recovery/error evidence separately from automated test success. | qualification |
| BEN-04 | Issue dated, scoped and revocable qualification claims only after applicable gates pass on the final integrated revision; separate machine conformance, human review and comparative advantage. | qualification |
| GOV-01 | Preserve zero mandatory approvals/CODEOWNERS/team gates, owner recovery, blocked force-push/deletion and required conversation resolution; activate and read back actual settings. | Typst #5; LaTeX #8 |
| GOV-02 | Reuse canonical make verify, stable automated checks, least privilege, immutable actions, bounded execution, fast PR/deep scheduled lanes and qualified dependency/security gates. | Typst completed #4; LaTeX completed #7 |
| GOV-03 | Reconcile registry and executable-helper coverage/CodeQL applicability using actual measured components and provider evidence; assess release supply-chain profile without fabricated coverage. | Typst #5; LaTeX #8 |
| GOV-04 | Reconcile integrated revisions and evidence, time-bound exceptions and existing owners; preserve the separate offline-runner provisioning hold and prevent duplicate hardening trackers. | Typst #6; LaTeX #9 |

## 3. Policy provenance and human boundaries

Each policy rule SHALL record its source URL, clause, retrieval date, source-content digest, effective/version information where reliable, applicability, severity and interpretation. The current preparation page has inconsistent version labels; do not infer authority from a banner alone. Preserve dated source evidence and reviewed changes.

Policy fixtures SHALL cover the current prescribed matter/title order, A4/margins/pagination, abstract, declarations, funding, publication integration, rights inventory, language/creative conditions and degree/course word-count rules. Reconcile all existing docs/requirements.md EARS IDs, docs/tasks.md, tasks.md, README claims and LaTeX todo.md; old “complete” checklists are not acceptance evidence. University exceptions need their actual approval/reference, not a maintainer-created policy exemption.

Automated checks SHALL NOT assert institutional approval, originality, scientific validity, permission to republish, approval of AI use, suitability of human editing or usability by a screen-reader user. Store each as a distinct human decision or research result. Required human review may be performed by the responsible author/appropriate authority; this is not a second-maintainer or mandatory PR-review rule.

## 4. Latest Typst and output capability contract

The official latest stable release observed during planning is **Typst 0.15.1** (17 July 2026). Initially declare 0.15.1 as both qualification compiler and package minimum. Retain [tool].typst.version as the exact repository pin consumed by the existing verifier; add [package].compiler for package compatibility. Recheck the latest stable release when implementing and qualify any later upgrade deliberately.

The adoption matrix SHALL include native multiple bibliographies and targets/groups; typed paths across package boundaries; optional variable-font axes; typst eval with correct failure exit status; native dependency JSON; semantic tagged PDF and compatible simultaneous PDF standards; improved diagnostics and layout migration behaviour. Exact binaries, packages, fonts and validation tools need independent digests.

Native dependency JSON contains paths, including output paths, not a complete hashed/font/toolchain lock. typst eval is the CLI introspection facility, not a reason to evaluate untrusted configuration as source code.

The ordinary accessible/archival target is PDF/UA-1 plus PDF/A-2a, subject to successful qualification. PDF/A-3a is a separately justified attachment profile. PDF/UA-1 cannot be combined with PDF/A-4/PDF 2.0; PDF/UA-2 is not a current supported claim for Typst. PDF files used as images are currently incompatible with specified PDF/A/PDF/UA export modes and do not preserve source tags. Accessible publication text must have a qualified alternative; rendering an entire article as a graphic is not equivalent.

The LaTeX companion may separately qualify PDF/UA-2 with compatible PDF/A-4 or PDF/A-4f and appropriate MathML tagging, as described in the [official LaTeX tagging instructions](https://tagging-project.latex-project.org/documentation/usage-instructions). This is a planned engine-specific capability, subject to actual class/package compatibility, independent validation and human review; it is not current repository support. Shared accessibility semantics do not require identical PDF standard versions.

HTML/MathML, bundle export and a11y-extras have explicit experimental compatibility adapters. Bundle/a11y-extras web-app limits must be documented. Their availability does not certify accessibility or authorize publication. pdf.artifact(kind: "redaction") labels a placeholder; restricted content must actually be omitted upstream.

## 5. Shared fixtures and acceptance interfaces

The engine-neutral corpus SHALL include monograph and publication theses; doctoral and research-masters cases; valid/invalid metadata; draft/screen/print configurations; named/blind identity cases; approved non-English and joint-award/resubmission cases; creative outputs; funding and AI/human assistance; long/complex tables, images, equations, code/algorithms, citations, glossary/index and appendices; restricted/public content variants; and deliberate failures.

Each fixture SHALL have a stable ID, licence, synthetic/public classification, source digest, applicability, expected pass/fail/unsupported result and expected semantic assertions. Negative fixtures must fail for the intended reason. Compare engines on meaning, required ordering, reference integrity and policy outcomes. Cross-engine identical PDF bytes, page counts, pixels, APIs or line breaks are not requirements. Visual goldens are controlled within an engine/font/toolchain profile.

Keep make verify as the canonical bounded entry point. Implementation may add documented subtargets for contract, output, accessibility, reproducibility, package, evidence, deposit and experimental-web checks, with fast PR and scheduled/release matrices. These are proposed interfaces until implemented. Missing required tools, fixtures, fresh output or sidecars must fail; a skipped lane never substitutes for an applicable result. Retain seeds, commands, timeouts and useful minimal counterexamples.

## 6. Evidence and closure semantics

The common wrapper MUST validate against the pinned central [verification-receipt schema](https://github.com/edithatogo/repository-standards/blob/10e59936e132f28597cb7d2f10efa27629dc4837/schemas/verification-receipt.schema.json): schema_version 1, repository, revision, generated_at, result (pass/fail/partial), nonempty checks (pass/fail/skip), and permitted artifact/metric fields. The schema forbids arbitrary extra top-level keys. Existing native reports remain valid sidecars; do not relabel them as central receipts.

A versioned thesis result sidecar SHALL carry at least:

- contract_version/digest, source revision/tree state, fixture ID/digest, engine/compiler/tool versions, normalized configuration hash, purpose/layout/identity/output and run ID/time;
- requirement ID, source rule reference, applicability/reason, implementation state, expected and observed result, command/exit/seed/duration and evidence references;
- produced artifact paths/digests, dependency/font/toolchain manifest references, validator identities and independent human decision references;
- exceptions with scope, responsible owner, rationale and expiry; public/private evidence classification.

Implementation state (planned/implemented) is separate from result: **executed-pass, executed-fail, unexecuted, blocked, unsupported, not-applicable, human-review-required**. Actual recorded human decisions remain separate from automated results. Map these truthfully into the central wrapper: fail for a failed required check; partial for unresolved required work; skip only with an explicit reason. Unsupported mandatory functionality is not not-applicable. A test expecting an invalid thesis to fail may pass as a regression test without certifying that thesis.

Only public/synthetic evidence may enter public CI/releases. Normalize external paths; do not publish restricted manuscript text, private prompts, identifying diagnostics or secret sentinels. Test successful and failing execution paths for leaks.


For blind-review delivery, retain the full provenance receipt internally/privately and emit a separately specified reviewer-safe manifest. Repository names, commit identities, run URLs, source paths and source bundles can reveal authorship; never automatically include them in the reviewer-facing package. For any deterministic-build claim, independently rebuilt artifacts in the declared pinned environment must have identical bytes/digests; mismatch is an acceptance failure, not merely an observation. Semantic repeatability is a separate scoped claim.

## 7. Repository standards and execution gates

The [solo-maintainer](https://github.com/edithatogo/repository-standards/blob/10e59936e132f28597cb7d2f10efa27629dc4837/docs/solo-maintainer-standard.md), [continuous-conformance](https://github.com/edithatogo/repository-standards/blob/10e59936e132f28597cb7d2f10efa27629dc4837/docs/continuous-conformance-standard.md), [product-metadata](https://github.com/edithatogo/repository-standards/blob/10e59936e132f28597cb7d2f10efa27629dc4837/docs/repository-product-metadata-standard.md), archetype and scientific-result contracts govern applicable work.

- Preserve zero mandatory human approvals/CODEOWNERS/team gates and explicit owner recovery. Require conversation resolution, blocked force-push/deletion and stable automated checks. Desired JSON is not active enforcement: verify settings read-back.
- Reconcile Typst PR #12's observed required_review_thread_resolution:false with the central requirement, or record a justified explicit exception in the existing governance owner.
- Keep source/workflow permissions read-only by default, job-scoped writes, immutable pins, concurrency/timeouts, bounded retries, expiring quarantine and tag-only release publication. Never enable TeX shell escape. Required tooling must remain usable through free/local or qualified free-service paths; do not introduce paid/trial-only mandatory gates.
- Apply Python coverage/CodeQL to actual executable helpers, not .typ/.tex layout. The central July registry's no-executable-coverage classification needs reassessment after integrated helper tests; measure the declared files/exclusions and real hosted provider results. Assess published-artifact supply-chain applicability rather than inheriting supply_chain_profile:none indefinitely.
- Update canonical context and existing Conductor track indexes when materialising work; link central F04 verification, F05 release provenance and F07 certification without duplicating them. Planned central tracks and blocked live collectors are not estate-wide execution evidence.

## 8. Milestones, dependencies and completion

1. **Foundation:** use delivered Typst #10, qualify the now-retargeted #12 and refresh #11; use delivered LaTeX #15 and existing #8/#9 owners. Exact receiving-revision checks are required. Settings activation remains with its existing owner.
2. **Shared contract and regression baseline:** materialise this contract/corpus and the companion adapter; retain failing examples before semantic fixes. Contract design can proceed while foundation PRs finish.
3. **Submission qualification:** fix semantics/configuration; implement current native features and policy; then qualify semantic/visual and accessible/archival output.
4. **Production and research qualification:** deterministic builds, clean package/author experience, schema-valid evidence/provenance, public/full deposit projections and release verification.
5. **Experimental capability and comparative evaluation:** HTML/MathML/bundles are an opt-in branch after semantic foundations. Measure both engines, performance and actual author/accessibility tasks; publish dated scope/limits.

Work may run in parallel after declared dependencies. A leaf issue closes only with exact-revision evidence for its IDs, receiving-branch verification, documentation/migration and all applicable negative tests. A core PDF release need not wait for optional web support, but this full programme does not silently discard the requested web/research/evaluation work.

The coordinating issue closes only when every mapped requirement has executed acceptance or a legitimate, recorded scope-specific non-applicability decision; required human/research evidence must remain open until obtained. Any reduction of requested scope is an explicit contract change. A universal “beyond frontier” label is not an acceptance shortcut: report measured advantages, comparator versions, limitations and review/expiry triggers.

## 9. Primary references

- [Typst 0.15.1](https://typst.app/docs/changelog/0.15.1/) and [0.15.0 capabilities/migrations](https://typst.app/docs/changelog/0.15.0/).
- [Native bibliographies](https://typst.app/docs/reference/model/bibliography/), [paths](https://typst.app/docs/reference/foundations/path/), [PDF standards](https://typst.app/docs/reference/pdf/), [image restrictions](https://typst.app/docs/reference/visualize/image/), [HTML](https://typst.app/docs/reference/html/), [bundle](https://typst.app/docs/reference/bundle/) and [package manifest](https://github.com/typst/packages/blob/main/docs/manifest.md).
- [Melbourne preparation process](https://gradresearch.unimelb.edu.au/processes/preparation-of-graduate-research-theses), [writing/word limits](https://gradresearch.unimelb.edu.au/preparing-my-thesis/writing-and-preparing-your-thesis), [thesis with publication](https://gradresearch.unimelb.edu.au/preparing-my-thesis/thesis-with-publication), [submission](https://gradresearch.unimelb.edu.au/examination/submitting-your-thesis) and [library deposit](https://gradresearch.unimelb.edu.au/examination/my-thesis-in-the-library).

<!-- umthesis-execution-links:start -->
## 10. Linked execution backlog

All acceptance issues below are open/planned at creation; delivered foundation work retains its existing issue state.

| Owner key | Execution issue | Requirement IDs | Sequence |
|---|---|---|---|
| contract | [#14 — Materialise UMTHESIS v1 schemas, shared fixtures and LaTeX adapter boundary](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/14) | CON-01, CON-02, CON-03, CON-04 | 1 — contract/API milestone |
| correctness | [#15 — Repair rendered declarations, navigation, configuration and blind output](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/15) | COR-01, COR-02, COR-03, COR-04, COR-05 | 2 — semantic/configuration repairs |
| typst | [#16 — Adopt current native capabilities with a tested compatibility contract](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/16) | TYP-01, TYP-02, TYP-03, TYP-04, TYP-05 | 2 — current native capabilities |
| policy | [#17 — Implement current Melbourne requirements, publications and disclosures](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/17) | POL-01, POL-02, POL-03, POL-04, POL-05, POL-06, POL-07 | 3 — Melbourne submission policy |
| testing | [#18 — Add semantic, visual, negative and generated document regression tests](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/18) | TST-01, TST-02, TST-03 | 1 — failing specimens and output oracles |
| accessibility | [#19 — Qualify semantic PDFs, PDF/UA-1 and compatible PDF/A](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/19) | ACC-01, ACC-02, ACC-03 | 4 — accessible/archival PDF |
| reproducibility | [#20 — Lock fonts and inputs, replay clean builds and bind release evidence](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/20) | REP-01, REP-02, REP-03 | 4 — input lock and replay; release binding after evidence |
| packaging | [#21 — Ship a clean starter, valid package and executable documentation](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/21) | PKG-01, PKG-02, PKG-03 | 5 — clean distribution and author workflow |
| evidence | [#22 — Produce requirement receipts and traceable research artifacts](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/22) | EVD-01, EVD-02, EVD-03, SCI-01, SCI-02 | 4 — receipt/research adapter; consume later validators |
| deposit | [#23 — Build full/public variants with verifiable redaction and rights records](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/23) | DEP-01, DEP-02, DEP-03 | 5 — full/public deposit |
| web | [#24 — Add semantic HTML, MathML and multi-file bundle exports](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/24) | WEB-01, WEB-02 | 5 — experimental branch |
| qualification | [#25 — Benchmark both engines, test author usability and publish qualified claims](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/25) | BEN-01, BEN-02, BEN-03, BEN-04 | 6 — complete empirical qualification |

- [ ] [LaTeX local contract consumer #18](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/18) — shared semantics, policy, evidence, privacy and benchmark participation.
- [ ] Existing governance/evidence acceptance: Typst [#5](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/5), [#6](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/6); LaTeX [#8](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/8), [#9](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/9).
- Delivered verifier groundwork: Typst [#4](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/4)/[PR #10](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/10), LaTeX [#7](https://github.com/edithatogo/unimelb-thesis-template-latex/issues/7)/[PR #15](https://github.com/edithatogo/unimelb-thesis-template-latex/pull/15).

### Dependency semantics

Issue links express prerequisite interfaces/milestones, not a requirement to close an entire broad workstream before another starts. In particular:

- The schema/API milestone of #14 unblocks both engines and #18 output tests. LaTeX #18 supplies a minimal adapter slice before #14 closes; its full parity work remains open until its own criteria pass.
- #15 correctness and #16 native features proceed alongside #18 failing specimens; #17 consumes their interfaces.
- #19 accessibility, #20 deterministic input/replay work and #22 evidence/report adapters can proceed in parallel once their prerequisite fixtures exist. #16's compiler/native-interface milestone unblocks #20; #20's later replay gate supplies #16's final upgrade-automation evidence. #18's initial fixture/oracle interface unblocks #19 before all accessibility results exist.
- #20 final release binding consumes final #19/#21/#22/#23 evidence; its earlier inventory/replay work does not depend on those issues closing.
- #23 deposit uses #22 evidence and supplies the versioned rights-projection API, core PDF/LaTeX tests and web adapter fixtures. #24 owns final HTML/bundle execution and consumes that early projection milestone without waiting for #23 to close. Its public distribution gate must use the verified projection.
- #25 protocol design starts early. Final acceptance consumes the applicable completed outputs and LaTeX #18, including genuine empirical/human evidence.
- Existing ruleset/provider activation and held offline-security provisioning remain with their established owners.

The complete request is represented by **51 stable requirement IDs**, **12 focused Typst execution issues**, the **LaTeX consumer**, and the pre-existing governance/CI owners.
<!-- umthesis-execution-links:end -->
