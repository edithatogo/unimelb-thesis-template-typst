# requirements

This document captures the functional and documentation requirements for the University of Melbourne Typst thesis template. Requirements are expressed using the Easy Approach to Requirements Syntax (EARS). Each entry follows a Kiro-style structure with an identifier, priority, cited source(s), the EARS statement, and supporting notes.

## Legend
- **Priority**: Must (policy compliance), Should (strongly recommended best practice), May (optional enhancement).
- **Source codes**: 
  - `UoM-Prep` – Preparation of Graduate Research Theses Process (Version 3, 11 Jun 2025).
  - `UoM-Pub` – Incorporating your published work in your thesis (Graduate Research Hub, accessed Oct 2025).
  - `UoM-AI` – Statement on responsible use of digital assistance tools in research (University of Melbourne, 2025).
  - `ASEP` – Australian Standards for Editing Practice, 2nd Ed. (Standards C, D, E).
  - `Typst-UIT` – modern-uit-thesis Typst template (v0.1.6, 2025).
  - `Typst-UM` – modern-um-thesis Typst template (v0.1.0, 2025).
  - `Typst-ThesIST` – ThesIST Typst template (v1.0.2, 2025).
  - `LaTeX-UoM` – unimelb-thesis-template-latex (commit main, 2025).

---

## Conceptual Overview

```mermaid
flowchart LR
  subgraph Policy Inputs
    A[UoM-Prep]
    B[UoM-Pub]
    C[UoM-AI]
    D[ASEP Standards]
  end

  subgraph Reference Templates
    E[Typst-UIT]
    F[Typst-UM]
    G[ThesIST]
    H[LaTeX-UoM]
  end

  subgraph Requirement Domains
    R1[Format & Layout]
    R2[Preface & Declarations]
    R3[Publication Integration]
    R4[Appendices & Creative]
    R5[Integrity & AI]
    R6[Submission & Automation]
    R7[Implementation Scaffolding]
  end

  subgraph Outcomes
    O1[Template Compliance]
    O2[Author Guidance]
    O3[Repeatable Automation]
  end

  Policy Inputs --> R1
  Policy Inputs --> R2
  Policy Inputs --> R3
  Policy Inputs --> R5
  Policy Inputs --> R6

  Reference Templates --> R1
  Reference Templates --> R3
  Reference Templates --> R4
  Reference Templates --> R7

  R1 --> O1
  R2 --> O1
  R3 --> O1
  R4 --> O1
  R5 --> O2
  R6 --> O3
  R7 --> O2
  R7 --> O3
```

## 1. Thesis format and layout

### R-FMT-001 — A4 layout and margins
- Priority: Must
- Source: UoM-Prep §3.4(a–d)
- EARS Requirement: The template shall produce an A4 thesis PDF with left and right margins of at least 30 mm, logical page numbering, and configuration to deliver the written components as a single clearly named file.
- Notes: Configure Typst to default to `paper: a4` and enforce margin constraints; document how to rename the compiled artifact when uploading to TES.

### R-FMT-002 — Print-ready spreads
- Priority: Should
- Source: UoM-Prep §3.5
- EARS Requirement: When the user enables print-ready output, the template shall lay out pages for double-sided printing with mirrored inner margins and guidance for thermal binding, including optional spine text using the candidate’s legal name in uppercase family name.
- Notes: Provide a typst flag or profile for print-export and document how to adjust spine width.

### R-FMT-003 — University branding compliance
- Priority: Must
- Source: UoM-Prep §3.6
- EARS Requirement: When rendering any page, the template shall omit the University of Melbourne logo and avoid assets that could be mistaken for official branding.
- Notes: Replace logos with neutral typographic marks; mention policy in docs.

### R-FMT-004 — Declaration without signatures
- Priority: Must
- Source: UoM-Prep §3.7, §3.10
- EARS Requirement: When generating the declaration page, the template shall present the mandatory statements without signature lines or cues requesting handwritten signatures.
- Notes: Provide editable text blocks for clauses 3.10(a–d) and a field for the approved word count.

### R-FMT-005 — Lists and copyright register
- Priority: Must
- Source: UoM-Prep §3.8(i–j)
- EARS Requirement: When the thesis includes ten or more tables, figures, or illustrations, the template shall automatically generate the corresponding lists and a dedicated register enumerating third-party copyright material with permission status fields.
- Notes: Supply macros to tag assets for inclusion and a table structure for permissions.

---

## 2. Front matter metadata

### R-FM-001 — Title page completeness
- Priority: Must
- Source: UoM-Prep §3.8(a), §3.9
- EARS Requirement: When composing the title page, the template shall capture and display the thesis title, optional discrete titles for creative outputs, candidate legal name, ORCID, degree title, submission month/year, resubmission month/year, relevant department(s)/school(s)/faculty, and any jointly awarding institution.
- Notes: Provide metadata fields and validation hints; allow multiple departmental entries.

### R-FM-002 — Abstract obligations
- Priority: Must
- Source: UoM-Prep §3.8(c)
- EARS Requirement: When rendering the abstract section, the template shall enforce a 300–500 word range and include a prompt to describe the form and presentation of creative outputs when present.
- Notes: Offer character count helpers or compile-time warnings; mention that abstracts for creative works must outline exhibition format.

### R-FM-003 — Funding acknowledgements
- Priority: Must
- Source: UoM-Prep §3.8(f–g)
- EARS Requirement: When emitting acknowledgements, the template shall provide slots to acknowledge funding sources, grant identifiers, RTP fee-offset scholarships, and other contributors.
- Notes: Include optional structured table for grant numbers; remind users to follow RTP wording.

---

## 3. Preface and declarations

### R-PRE-001 — Contribution disclosure scaffold
- Priority: Must
- Source: UoM-Prep §3.11(a–f); UoM-Pub “The preface”
- EARS Requirement: When generating the preface, the template shall prompt the candidate to record author contributions, chapter/page locations of incorporated material, prior or external work, editorial or generative AI assistance (including tools, dates, and prompts), and third-party human assistance with discipline expertise status.
- Notes: Provide tabular and narrative templates; encourage exhaustive detail per policy examples.

### R-PRE-002 — Publication status register
- Priority: Must
- Source: UoM-Prep §3.11(g); UoM-Pub “Declaration of incorporated publications”
- EARS Requirement: When preparing the preface, the template shall collect each incorporated publication with its citation and status categorised as unpublished, submitted, in revision, accepted, or published.
- Notes: Enforce category enumeration; allow multiple publications via repeatable blocks.

### R-PRE-003 — Declaration wording and word limits
- Priority: Must
- Source: UoM-Prep §3.10(b–d)
- EARS Requirement: When assembling the declaration, the template shall include configurable statements covering due acknowledgment, word-count compliance (with an overridable approved total), and dissertation versus creative output percentages summing to 100.
- Notes: Provide placeholders for the PVC-approved word limit where applicable.

---

## 4. Publications integration

### R-PUB-001 — Inclusion criteria reminders
- Priority: Must
- Source: UoM-Prep §3.14–3.16; UoM-Pub “Overview”
- EARS Requirement: When the user marks a chapter as an incorporated publication, the template shall prompt confirmation that the work was produced during candidature with substantial candidate contribution, that supervisor and coordinating author consent is recorded, and that obligations to third parties do not block inclusion.
- Notes: Include checklist annotation that stays out of the PDF but is surfaced in documentation or build logs.

### R-PUB-002 — Chapter linkage and footnotes
- Priority: Should
- Source: UoM-Pub “Format of the thesis”, FAQ on partial reuse
- EARS Requirement: When inserting publication-derived chapters or sections, the template shall facilitate chapter-open footnotes describing the source publication, reuse scope, and publication status, while omitting the publication from the main bibliography where it is included verbatim.
- Notes: Supply macros for `#include-publication` with citation metadata and optional appendix linkage.

### R-PUB-003 — Publication status updates
- Priority: Should
- Source: UoM-Pub “The examination”
- EARS Requirement: When the publication status changes between examination submission and final submission, the template shall enable easy updates to the preface and changelog to reflect the new status.
- Notes: Provide a single source of truth for status metadata reused across front matter and appendix lists.

### R-PUB-004 — Literature review supplementation
- Priority: Should
- Source: UoM-Pub FAQ on literature surveys
- EARS Requirement: When the thesis relies on publication-embedded literature reviews, the template shall surface guidance to include supplementary review material covering gaps and recent work.
- Notes: Add documentation call-outs and sample chapter stubs for integrative reviews.

### R-PUB-005 — iThenticate guidance block
- Priority: Should
- Source: UoM-Pub “iThenticate report”
- EARS Requirement: When preparing submission documentation, the template shall provide instructions to run the entire thesis through iThenticate, exclude self-matching publications appropriately, and record any applied filters in a declaration uploaded to TES.
- Notes: Include paragraph in README and optional appendix template for the iThenticate declaration.

### R-PUB-006 — Declaration form handling
- Priority: Must
- Source: UoM-Pub “Completing the forms”
- EARS Requirement: When documenting submission steps, the template shall instruct candidates to complete a Declaration for publication incorporated in a thesis form for each work and to upload the combined PDF to TES without embedding the forms in the thesis.
- Notes: Provide merge tips (e.g., Nitro Pro, Preview) and remind that multi-authored works require Part C completion.

---

## 5. Appendices and creative outputs

### R-APP-001 — Supportive appendices only
- Priority: Must
- Source: UoM-Prep §3.18–3.19
- EARS Requirement: When adding appendices, the template shall position them after the bibliography and provide guidance that only material supporting the thesis argument—such as full publications, datasets, instruments, or creative documentation—may be included.
- Notes: Supply appendix section macros; suggest including full publications when partial content appears in chapters.

### R-APP-002 — Creative output linkage
- Priority: Must
- Source: UoM-Prep §3.13; §3.8(c)
- EARS Requirement: When the thesis includes creative outputs, the template shall support embedding descriptions, media references, and stable links in both the abstract and dedicated appendix sections, noting that online works must remain unchanged during examination.
- Notes: Allow URL footnotes and captions for recordings, scores, or galleries.

---

## 6. Digital assistance and integrity

### R-AI-001 — Digital assistance log prompt
- Priority: Must
- Source: UoM-Prep §3.24; UoM-AI “Acknowledgement”
- EARS Requirement: When capturing preface declarations, the template shall prompt candidates to record the digital assistance tools used, dates of use, prompts, and verification steps, with instructions to retain logs for supervisory or examination requests.
- Notes: Provide table template for tool, purpose, prompt, output disposition.

### R-AI-002 — Confidentiality warning
- Priority: Should
- Source: UoM-AI “Responsible use”
- EARS Requirement: When documenting digital assistance guidance, the template shall warn candidates not to enter confidential or proprietary information into third-party tools unless University-hosted.
- Notes: Include highlighted caution box in README and preface instructions.

### R-AI-003 — Verification and citation guidance
- Priority: Should
- Source: UoM-AI “Content assistance”
- EARS Requirement: When describing acceptable AI use, the template shall instruct candidates to verify generated material, run plagiarism and copyright checks where appropriate, and cite AI-generated content via footnote with tool, version, date, and prompt.
- Notes: Provide sample footnote syntax consistent with University referencing guidance.

---

## 7. Editorial boundaries

### R-EDT-001 — Supervisor intervention limits
- Priority: Must
- Source: UoM-Prep §3.22; ASEP Standard C
- EARS Requirement: When outlining editorial support, the documentation shall state that supervisors may intervene only within ASEP Standard C (substance and structure) and remind candidates of their responsibility for substantive content.
- Notes: Summarise Standard C expectations and link to ASEP citation.

### R-EDT-002 — Third-party and tool limits
- Priority: Must
- Source: UoM-Prep §3.23; ASEP Standards D & E
- EARS Requirement: When describing non-supervisor assistance, the documentation shall limit permitted interventions to ASEP Standards D and E (language, illustrations, completeness, consistency) whether the assistance is human or digital.
- Notes: Provide concise outline of Standards D/E topics; emphasise that substantial rewriting is out of scope.

---

## 8. Submission and repository readiness

### R-SUB-001 — Originality reporting reminder
- Priority: Must
- Source: UoM-Prep §3.1(a–c)
- EARS Requirement: When listing submission prerequisites, the template shall remind candidates to upload the electronic thesis, originality report, and required supervisor/coordinating author declarations to TES.
- Notes: Provide checklist in README or docs page.

### R-SUB-002 — Final copy compliance
- Priority: Must
- Source: UoM-Prep §3.25–3.26
- EARS Requirement: When the thesis passes examination, the documentation shall direct candidates to prepare a durable electronic copy incorporating examiner amendments and conforming to University repository guidelines.
- Notes: Link to Minerva repository specifications and explain bundling of multimedia components.

---

## 9. Template structure and implementation

### R-IMP-001 — Modular project layout
- Priority: Must
- Source: Typst-UIT; Typst-ThesIST; LaTeX-UoM structure
- EARS Requirement: The template shall organise content into reusable components (global configuration, per-chapter files, assets, bibliographies) to mirror the modular conventions used in leading Typst and LaTeX thesis templates.
- Notes: Provide a `global.typ`-style configuration module and sample `chapters/` directory.

### R-IMP-002 — Rich metadata interface
- Priority: Must
- Source: Typst-UIT; LaTeX-UoM metadata options
- EARS Requirement: When initialising a project, the template shall expose metadata fields for supervisors (multiple roles), faculty/school, degree type, major, ORCID, keywords, and submission dates so they flow into front matter elements.
- Notes: Use structured Typst dictionaries; include validation comments.

### R-IMP-003 — Preface contribution matrix
- Priority: Should
- Source: LaTeX-UoM sample preface; UoM-Pub guidance
- EARS Requirement: When rendering the preface, the template shall provide optional tables to capture contribution percentages per publication or task.
- Notes: Include sample table with columns for author, contribution, percentage.

### R-IMP-004 — Automated lists and indices
- Priority: Must
- Source: Typst-UIT figure/table indexes
- EARS Requirement: When compiling the thesis, the template shall automatically generate table of contents, lists of figures/tables/illustrations, list of abbreviations, and optional code listing index when the corresponding items exist.
- Notes: Provide toggles to enable/disable lists; rely on Typst counters.

### R-IMP-005 — Abbreviations and glossary support
- Priority: Should
- Source: Typst-UIT abbreviations block; Typst-ThesIST guidance
- EARS Requirement: When the user registers abbreviations, the template shall render first-use expansions and provide an abbreviations list in the front matter.
- Notes: Implement helper functions for first-use detection and list generation.

### R-IMP-006 — Code and algorithm styling
- Priority: Should
- Source: Typst-UIT code configuration; LaTeX-UoM example chapters
- EARS Requirement: When displaying source code or algorithms, the template shall offer consistent styling with language-specific highlights and captioning conventions.
- Notes: Bundle `codly` configuration or equivalent and document usage.

### R-IMP-007 — Bibliography integration
- Priority: Must
- Source: LaTeX-UoM (biblatex workflow)
- EARS Requirement: When compiling references, the template shall support BibTeX/BibLaTeX-equivalent workflows via Typst’s bibliography system and document citation practices aligned with University referencing guidance.
- Notes: Provide sample `.bib` file, cite commands, and compile instructions.

### R-IMP-008 — Build automation guidance
- Priority: Should
- Source: LaTeX-UoM automated build; Typst-UM getting started
- EARS Requirement: When describing project usage, the template shall include CLI commands or scripts for local builds, continuous preview (watch mode), and cleaning artifacts.
- Notes: Offer shell scripts or task runner configs; mention Typst web app alternative.

### R-IMP-009 — Multilingual readiness
- Priority: May
- Source: Typst-UM multilingual support
- EARS Requirement: When configuring localisation, the template may provide mechanisms to switch key labels (e.g., abstract, acknowledgements) to alternative languages while retaining compliance with English summary obligations.
- Notes: Implement via translation dictionaries; default to English.

### R-IMP-010 — Sample content and QA prompts
- Priority: Should
- Source: Typst-UIT sample chapters; LaTeX-UoM example directory
- EARS Requirement: When delivering the template, the package shall include sample chapters demonstrating figures, tables, equations, citations, and publication integration scenarios, accompanied by QA checklists referencing University requirements.
- Notes: Use samples to illustrate lists, cross-references, and AI disclosure language.

---

## 10. Extended usability and automation

### R-STR-001 — Template section structure
- Priority: Must
- Source: UoM-Prep §3.8; UoM-Pub format guidance
- EARS Requirement: When generating the thesis, the template shall provide front matter, main matter, and end matter scaffolding in the mandated order (title page, abstract, declaration, acknowledgements, preface, TOC/Lists, chapters, bibliography, appendices/optional material) with sample files mirroring this structure.
- Notes: Ensure repository layout and documentation map to the required sequencing.

### R-OPT-DED-001 — Optional dedication page
- Priority: May
- Source: Typst-UIT and modern Typst templates
- EARS Requirement: When the author opts in, the template shall render a dedication page positioned after the title page.
- Notes: Exclude from default flow; document usage.

### R-OPT-AUTH-001 — Statement of authorship
- Priority: Should
- Source: Typst reference templates; LaTeX-UoM
- EARS Requirement: When the author enables it, the template shall provide a structured statement of authorship/contribution section compliant with UoM preface requirements.
- Notes: Can be merged with preface or standalone.

### R-OPT-GLOS-001 — Glossary and abbreviations
- Priority: Should
- Source: Typst-UIT glossary usage; UoM-Prep §3.8(i)
- EARS Requirement: When glossary or abbreviation data exists, the template shall generate the corresponding lists in the end matter with automatic first-use expansion support.
- Notes: Align with R-IMP-005 implementation.

### R-OPT-IDX-001 — Optional index
- Priority: May
- Source: Typst/LaTeX thesis patterns
- EARS Requirement: When the author supplies index terms, the template shall produce an end-matter index in accordance with UoM ordering.
- Notes: Provide instructions for generating index entries.

### R-FNT-001 — Font theme profiles
- Priority: Should
- Source: Typst-UIT font bundles; Typst-UM multilingual defaults
- EARS Requirement: When configuring document styling, the template shall expose selectable serif and sans-serif font themes with documented fallbacks that maintain accessibility contrast.
- Notes: Provide defaults aligned with open-license fonts and guidance for custom overrides.

### R-LOC-001 — Localised labels
- Priority: Should
- Source: Typst-UM localisation usage; UoM-Prep §3.8(b–c)
- EARS Requirement: When the user opts into a supported locale, the template shall render chapter and front-matter labels in that language while retaining the mandated English summary.
- Notes: Maintain English fallback and highlight requirements for bilingual submissions.

### R-BLD-001 — Build profiles
- Priority: Should
- Source: Typst CLI profile support; print guidance in UoM-Prep §3.5
- EARS Requirement: When invoking builds, the tooling shall provide `draft`, `screen`, and `print` profiles that adjust margin mirroring, image compression, and watermarking according to the selected output mode.
- Notes: Profiles should map to command-line shortcuts and documentation.

### R-QA-001 — Preflight validation command
- Priority: Should
- Source: ThesIST tooling patterns; R-IMP requirements
- EARS Requirement: When preparing for submission, the repository shall offer a preflight command that compiles the thesis, verifies metadata completeness, appendix ordering, publication registry status, and AI disclosure logs, emitting actionable warnings.
- Notes: Integrate with CI and surface instructions in README.

### R-SMP-001 — Expanded sample library
- Priority: Should
- Source: Typst-UIT and ThesIST sample projects; LaTeX-UoM example chapters
- EARS Requirement: When shipping the template, the package shall include sample chapters covering publication integration, creative outputs, AI disclosures, funding acknowledgements, and QA checklist usage.
- Notes: Samples should be referenced in documentation for quick onboarding.

### R-BIB-001 — Bibliography style presets
- Priority: Should
- Source: Typst bibliography system; LaTeX-UoM style switches
- EARS Requirement: When configuring citations, the template shall provide selectable bibliography styles (e.g., numeric, author–year, IEEE) that can be chosen via metadata and documented for discipline-specific guidance.
- Notes: Ensure presets stay in sync with Typst releases.

### R-CI-001 — CI matrix builds
- Priority: Must
- Source: Repository CI/CD best practice; Typst CLI usage
- EARS Requirement: When running continuous integration, workflows shall compile sample projects across all supported build profiles and the pinned Typst version to detect regressions before merge.
- Notes: Upload generated PDFs or logs as artefacts for review.

### R-CI-002 — Typst compatibility audit
- Priority: Should
- Source: Typst release cadence; repo maintenance best practice
- EARS Requirement: On a scheduled cadence, automation shall compile against the latest Typst release and report API changes or failures to maintainers.
- Notes: Document remediation steps when incompatibilities arise.

### R-CI-003 — Automated Typst upgrade helper
- Priority: Should
- Source: Automation best practice
- EARS Requirement: When a new Typst release is detected, the repository shall provide a script that updates configuration pins, refreshes lockfiles if applicable, and summarises changelog notes for maintainers.
- Notes: Script may open a pull request automatically or provide manual instructions.
