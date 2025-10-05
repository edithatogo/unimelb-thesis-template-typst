# tasks

## Layout & Metada## Imple## Implementation Scaffolding
- [x] R-IMP-001/R-IMP-002: Introduce modular `config/` layer and metadata interface exposed via Typst dictionaries.
- [x] R-IMP-003: Supply contribution matrix templates.
- [x] R-IMP-004/R-IMP-008: Extend sample projects and CI to cover automated compile/watch/clean recipes.
- [x] R-IMP-005: Implement abbreviation/glossary helper utilities.
- [x] R-IMP-006: Standardise code/algorithm styling with documented usage.
- [x] R-IMP-007: Document bibliography workflow aligned with referencing guidance.
- [x] R-IMP-010/R-SMP-001: Expand sample chapters covering publications, creative works, AI disclosures, and QA checklist.
- [x] R-OPT-GLOS-001: Integrate optional glossary/abbreviation list generation via endmatter modules.
- [x] R-OPT-IDX-001: Provide optional index workflow and sample to align with end matter ordering.Scaffolding
- [x] R-IMP-001/R-IMP-002: Introduce modular `config/` layer and metadata interface exposed via Typst dictionaries.
- [x] R-IMP-003: Supply contribution matrix templates.
- [x] R-IMP-004/R-IMP-008: Extend sample projects and CI to cover automated compile/watch/clean recipes.
- [x] R-IMP-005: Implement abbreviation/glossary helper utilities.
- [x] R-IMP-006: Standardise code/algorithm styling with documented usage.
- [x] R-IMP-007: Document bibliography workflow aligned with referencing guidance.
- [x] R-IMP-010/R-SMP-001: Expand sample chapters covering publications, creative works, AI disclosures, and QA checklist.
- [x] R-OPT-GLOS-001: Integrate optional glossary/abbreviation list generation via endmatter modules.
- [x] R-OPT-IDX-001: Provide optional index workflow and sample to align with end matter ordering.
- [x] R-FMT-001/R-FMT-002: Verify A4 layout, margin enforcement, and mirrored print-ready configuration in the Typst styles.
- [x] R-FMT-003/R-FMT-004: Remove branding assets, add spine text helper, ensure declaration page renders without signatures.
- [x] R-FMT-005: Maintain automated lists for figures/tables/algorithms and expose third-party copyright register support.
- [x] R-FM-001..003: Refactor front-matter metadata capture into a shared configuration module with validation hints.
- [x] R-STR-001: Provide repository scaffold (frontmatter/chapters/endmatter) with sample files.
- [x] R-OPT-DED-001: Add optional dedication page template and document usage.
- [x] R-OPT-AUTH-001: Provide statement of authorship block that can be included in preface/front matter.

## Preface, Declarations & Publications
- [x] R-PRE-001/R-PRE-002: Build structured preface macros (contribution tables, publication status register, AI/assistance prompts).
- [x] R-PRE-003: Parameterise declaration statements (word count, % allocations) with configurable placeholders.
- [x] R-PUB-001..004: Create publication registry macros (chapter footnotes, appendix linking, status updates).
- [x] R-PUB-005/R-PUB-006: Document iThenticate workflow and TES declaration packaging in README/docs.

## Appendices & Creative Outputs
- [x] R-APP-001/R-APP-002: Provide appendix helpers enforcing ordering and creative output descriptors.

## Integrity & Editorial Governance
- [x] R-AI-001..003: Add AI usage logging tables, confidentiality warnings, and citation examples to docs/preface templates.
- [x] R-EDT-001/R-EDT-002: Summarise ASEP editorial limits in documentation and template comments.

## Submission & Repository
- [x] R-SUB-001/R-SUB-002: Publish submission checklist (originality report, declarations, final-pass archival guidance).

## Implementation Scaffolding
- [x] R-IMP-001/R-IMP-002: Introduce modular `config/` layer and metadata interface exposed via Typst dictionaries.
- [x] R-IMP-003: Supply contribution matrix templates.
- [x] R-IMP-004/R-IMP-008: Extend sample projects and CI to cover automated compile/watch/clean recipes.
- [x] R-IMP-005: Implement abbreviation/glossary helper utilities.`
- [x] R-IMP-006: Standardise code/algorithm styling with documented usage.
- [x] R-IMP-007: Document bibliography workflow aligned with referencing guidance.
- [x] R-IMP-010/R-SMP-001: Expand sample chapters covering publications, creative works, AI disclosures, and QA checklist.
- [x] R-OPT-GLOS-001: Integrate optional glossary/abbreviation list generation via endmatter modules.
- [x] R-OPT-IDX-001: Provide optional index workflow and sample to align with end matter ordering.

## Extended Features & Automation
- [x] R-FNT-001: Added font theme registry (`utils/fonts.typ`) and integrated with style configuration.
- [x] R-LOC-001: Implemented locale labels (English, Simplified Chinese) and wired into title/abstract/declaration pages.
- [x] R-BLD-001: Flesh out draft/screen build profiles with profile-specific styling (watermarks, asset compression).
- [x] R-QA-001: Added `scripts/preflight.py` for compile and metadata validation; integrated local run.
- [x] R-BIB-001: Provide selectable bibliography presets via metadata and documentation.
- [x] R-CI-001: Updated CI workflow to run Typst matrix builds across `default/draft/screen/print` profiles.
- [x] R-CI-002: Added scheduled compatibility job compiling against latest Typst release.
- [x] R-CI-003: Added `scripts/update_typst.sh` helper for raising Typst version bumps.

## Documentation & Governance
- [x] Update README with build profiles, font themes/localisation, preflight command, and automation helper notes.
- [x] Document where the no-logo policy is enforced and provide instructions for alternative title marks.
- [x] Define contribution/governance process for new locales and typography presets.
- [x] Backfill documentation with link to policy sources and changelog guidance.

### Contribution Process for Locales and Typography Presets

#### Adding New Locales

**Current Locales:**

- `en` (English) - Default locale with comprehensive label translations
- `zh` (Simplified Chinese) - Complete Chinese translations for all thesis sections

**Submission Process:**

1. **Create Locale File**: Add new locale file `utils/locales/{locale-code}.typ` following the existing structure
2. **Define Labels**: Provide complete translations for all required labels (see `utils/locales/en.typ` for reference)
3. **Register Locale**: Update `utils/locales.typ` to import and register the new locale in the `_locales` dictionary
4. **Test Integration**: Verify the locale works with `typst compile --input locale={locale-code} thesis.typ`
5. **Submit PR**: Follow the standard PR template with compiled PDF validation

**Governance Requirements:**

- Must provide complete translations for all thesis section labels
- Should follow ISO 639-1 language codes for locale identifiers
- Requires testing with both `thesis.typ` and `sample-chapter.typ` compilation
- Must maintain consistent terminology with University of Melbourne academic standards

#### Adding New Typography Presets

**Current Font Themes:**

- `unimelb` (default) - University-branded serif/sans/mono stack with Fraunces primary
- `classic` - Traditional academic typography with Libertinus Serif and TeX Gyre fonts
- `modern` - Contemporary styling with STIX Two Text and Inter fonts

**Submission Process:**

1. **Define Font Stack**: Create new theme entry in `utils/fonts.typ` `_font-themes` dictionary
2. **Font Selection Criteria**:
   - Serif: Primary academic text font with good readability at small sizes
   - Sans: Clean, professional heading and UI font
   - Mono: Developer-friendly monospace with clear character distinction
3. **Fallback Strategy**: Include 4-6 fallback fonts per category for cross-platform compatibility
4. **Test Rendering**: Compile thesis with new theme and verify font rendering quality
5. **Submit PR**: Include PDF samples showing the new typography in context

**Governance Requirements:**

- Fonts must be open-source or have appropriate licensing for academic use
- Should maintain professional academic appearance suitable for thesis submission
- Requires cross-platform testing (macOS, Linux, Windows) for font availability
- Must include comprehensive fallback chains to prevent rendering failures

### Logo Policy Enforcement

The University of Melbourne logo policy (per thesis guidelines 3.6) restricts logo usage
to title pages only and prohibits its use in thesis content. This policy is enforced
through the following mechanisms:

**Code Implementation:**

- **Location**: `pages/title.typ` - The `title-page()` function conditionally renders
  the logo based on the `show_logo` context parameter
- **Default Behavior**: Logo is displayed by default (`show_logo: true`)
- **Override Mechanism**: `lib.typ` defines `default-show-logo = sys.inputs.at("show_logo",
  default: true)` allowing command-line control
- **User Control**: Users can hide the logo with `typst compile --input show_logo=false thesis.typ`

**Alternative Title Marks:**

When the logo is disabled, the title page maintains proper spacing and layout without
the logo. No alternative marks are automatically inserted, preserving the clean academic
appearance required by University guidelines.

**Documentation References:**

- README.md: Documents the `--input show_logo=false` compilation option
- assets/README.md: Notes that "University of Melbourne logo should NOT be used in
  thesis content (per thesis guidelines 3.6)"
