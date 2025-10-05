# University of Melbourne Thesis Template

A Typst template for University of Melbourne theses.

## ⚠️ Important Disclaimer

**This template contains fabricated, absurd content for demonstration purposes only.**
The sample thesis content about "quantum penguins" is entirely fictional and should not be used as academic work.
This is purely to showcase the template's formatting capabilities.

## Quick Start

1. Install Typst
2. Clone this repo
3. Edit `thesis.typ` with your details
4. Run `typst compile thesis.typ`

## Features

- University of Melbourne branding and official colors
- All required thesis sections (title page, abstract, acknowledgements, etc.)
- Mathematical equations and algorithm formatting
- Code syntax highlighting with line numbers
- Automatic table of contents and references
- Landscape pages for wide content
- Bibliography and citation support
- Optional glossary and abbreviation lists (auto-generated from abbreviation data)
- Optional index with custom entries and page numbers

## Code and Algorithm Styling

The template provides standardized styling for code snippets and algorithms with consistent formatting and captioning.

### Code Blocks

Use the `code-block()` function for syntax-highlighted code with optional line numbers and captions:

```typst
#code-block(
  caption: [Python implementation of gradient descent],
  ```python
  def gradient_descent(X, y, learning_rate=0.01, n_iterations=1000):
      weights = np.zeros(X.shape[1])
      for _ in range(n_iterations):
          y_pred = X.dot(weights)
          gradient = -2 * X.T.dot(y - y_pred) / len(X)
          weights -= learning_rate * gradient
      return weights
  ```,
  lang: "python"
)
```

**Parameters:**

- `caption`: Optional figure caption (makes it a numbered listing)
- `lang`: Language for syntax highlighting (e.g., "python", "rust", "javascript", "cpp", "r", "bash")
- `numbers`: Enable/disable line numbers (default: `true`)

### Algorithms

Use the `algorithm()` function for pseudocode with automatic numbering and captions:

```typst
#algorithm(
  caption: [Gradient descent algorithm],
  title: [Linear Regression Training],
  [
    + *Input:* Training data $cal(D)$, learning rate $eta$
    + *Output:* Learned weights $w$
    + Initialize $w <- 0^d$
    + *for* $t <- 1$ *to* max_iterations *do*
      + Compute gradient $nabla cal(L)$
      + $w <- w - eta nabla cal(L)$
    + *return* $w$
  ]
)
```

**Parameters:**

- `caption`: Optional figure caption
- `title`: Custom algorithm title (defaults to "Algorithm N")
- `body`: Pseudocode content using lovelace syntax

### Supported Languages

The template supports syntax highlighting for:

- Python 🐍
- Rust 🦀
- JavaScript 🟨
- Java ☕
- C++ ⚡
- C ⚡
- R 📊
- MATLAB 🔢
- Bash 💻
- SQL 🗄️
- LaTeX 📄
- Typst 📝

Algorithms are automatically included in the List of Algorithms in the front matter.

## Structure

- `thesis.typ` - Main file with sample content
- `frontmatter/` - Optional dedication/authorship stubs
- `chapters/` - Sample chapter scaffolding
- `endmatter/` - Sample appendices, bibliography, glossary, index
- `pages/` - Individual page templates used by the core macros
- `utils/` - Styling and utilities
- `assets/` - University logos and colors
- `layouts/` - Document layout configurations

## Requirements

- Typst 0.13+
- Basic knowledge of Typst syntax

## Usage Notes

- Replace the sample content with your actual thesis content
- Update author information and thesis details in `thesis.typ`
- Customize styling in the `utils/` directory if needed
- The template follows University of Melbourne thesis formatting guidelines
- Hide the title-page logo (if your faculty requires it) with `typst compile --input show_logo=false thesis.typ`

## AI Usage and Academic Integrity

This template includes support for documenting AI assistance in your thesis preface:

- **AI Usage Logging**: Track AI tools, dates, purposes, prompts, and outputs
- **Confidentiality Warnings**: Built-in notices about data privacy and intellectual property
- **Citation Examples**: Guidance on how to properly cite AI assistance

Configure AI usage in `thesis.typ`:

```typst
ai_usage: (
  (tool: "ChatGPT", date: "2024-10-01", purpose: "Grammar checking",
   prompt: "Check this paragraph for errors", output_ref: "Revised paragraph in Chapter 2"),
  // Add more entries as needed
),
```

When using AI tools:

- Maintain detailed logs of all interactions
- Ensure AI-generated content is properly cited
- Consult your faculty's policies on AI usage in academic work
- Consider the ethical implications of AI assistance

## Editorial Standards and ASEP Compliance

This template follows the Australian Standards for Editing Practice (ASEP).

### ASEP Editorial Limits Summary

- **Substantive editing**: Limited to clarification of meaning, structure, and coherence
- **Copyediting**: Allowed for grammar, syntax, and style consistency
- **Proofreading**: Permitted for final error checking
- **Developmental editing**: Not permitted (thesis content must remain the author's work)

When using editorial services:

- Choose ASEP-accredited editors
- Document all editorial assistance in your thesis preface
- Retain records of editorial agreements and communications

## Policy References

This template implements requirements from University of Melbourne policies and standards:

- **[Preparation of Graduate Research Theses Process]**
  ([View Policy](https://gradresearch.unimelb.edu.au/students/thesis/preparation)) (UoM-Prep)
  - Thesis formatting and submission requirements
- **[Incorporating your published work in your thesis]**
  ([View Policy](https://gradresearch.unimelb.edu.au/students/thesis/publications)) (UoM-Pub)
  - Guidelines for including publications in theses
- **[Statement on responsible use of digital assistance tools in research]**
  ([View Policy](https://academicintegrity.unimelb.edu.au/policy-and-procedures/responsible-use-of-ai)) (UoM-AI)
  - AI usage disclosure and citation requirements
- **[Australian Standards for Editing Practice]**
  ([View Standards](https://www.asep.edu.au/)) (ASEP)
  - Editorial standards for academic work

## Changelog

### [0.2.0] - 2025-01-XX

- **New Features**
  - Added configurable bibliography presets (APA, IEEE, numeric, author-year, Chicago, MLA)
  - Implemented locale support for English and Simplified Chinese
  - Added font theme system with unimelb, classic, and modern themes
  - Enhanced logo policy enforcement with command-line control
- **Documentation**
  - Added policy reference links for governance compliance
  - Documented contribution processes for locales and typography
  - Expanded preflight and automation documentation

### [0.1.1] - 2025-01-XX

- Added disclaimer and demonstration content
- Enhanced automation features documentation
- Created automation helper script

### [0.1.0] - 2025-01-XX

- Initial release with University of Melbourne branding
- Basic thesis structure and formatting
- Font updates to use official University fonts (Fraunces & Source Sans Pro)
- Fletcher diagram compatibility fixes

## Build Profiles

The template supports multiple build profiles that tailor layout for different
stages of your workflow:

| Profile | Command example | Notes |
| --- | --- | --- |
| `default` | `typst compile thesis.typ` | Standard single-sided layout for drafting |
| `draft` | `typst compile --input profile=draft thesis.typ thesis-draft.pdf` | Single-sided with draft watermark hooks |
| `screen` | `typst compile --input profile=screen thesis.typ thesis-screen.pdf` | For on-screen delivery |
| `print` | `typst compile --input profile=print thesis.typ thesis-print.pdf` | Double-sided layout for binding |

Profiles can also be set inside `thesis.typ` via the `profile` argument on the
`thesis` function if you prefer not to pass CLI inputs.

## Font Themes & Localisation

Switch font stacks or localisation without editing layout files by using Typst
inputs:

```bash
# Modern sans/serif pairing
typst compile --input font_theme=modern thesis.typ thesis-modern.pdf

# Chinese front matter labels while keeping the English abstract summary
typst compile --input locale=zh thesis.typ thesis-zh.pdf
```

Available font themes: `unimelb`, `classic`, `modern` (see `utils/fonts.typ`).
Supported locales currently include English (`en`) and Simplified Chinese
(`zh`). Adding a new locale requires a label set in `utils/locales/` and an
update to documentation.

## Preflight Checks

Use the bundled script to run end-to-end validation before submission:

```bash
python scripts/preflight.py --profile default --profile print
```

The preflight command compiles the main thesis and sample projects, checks for
common placeholder metadata, and stores artefacts under `build/preflight/`.
Warnings are emitted via the exit code so that CI can fail early while still
providing PDFs for inspection.

## CI & Automation Helpers

- `scripts/preflight.py` – runnable locally or in GitHub Actions for
  compilation and metadata checks.
- `scripts/update_typst.sh --apply` – updates the CI workflow to the latest
  Typst CLI release and prints the current/target version comparison.
- GitHub Actions matrix builds compile each profile (`default`, `draft`,
  `screen`, `print`) on every push. A scheduled job also tests against the
  latest Typst release, surfacing any breaking API changes.

## Submission Workflow

Before final submission to the University of Melbourne Thesis Examination System (TES),
ensure your thesis meets integrity and formatting requirements:

### iThenticate Plagiarism Check

1. Generate your final thesis PDF using the `print` profile: `typst compile --input profile=print thesis.typ thesis-print.pdf`
2. Submit the PDF to iThenticate via the University of Melbourne portal
   (accessed through the Graduate Research Hub).
3. Review the similarity report and address any high-similarity sections by revising content or adding proper citations.
4. Aim for a similarity index below the faculty threshold (consult your supervisor or faculty guidelines for specifics).
5. Retain the iThenticate report as proof of originality check.

### TES Declaration Packaging

1. Prepare your declarations:
   - Originality statement (confirming the work is your own).
   - Publication status declarations (if applicable, detailing any incorporated publications).
   - AI usage and third-party assistance disclosures (if used).
2. Package the following in your TES submission:
   - Final thesis PDF (print profile).
   - iThenticate originality report.
   - Signed declaration forms (digital signatures accepted).
   - Any required appendices or supplementary materials.
3. Submit through TES, ensuring all metadata (word count, publication details) matches the declarations.
4. For questions, refer to the Graduate Research Hub or your faculty's thesis submission guidelines.

## Build System

The template includes a comprehensive build system with automated compile/watch/clean recipes and profile support.

### Available Build Profiles

- `default` - Standard thesis compilation
- `draft` - Draft mode (faster compilation, reduced quality)
- `screen` - Screen-optimized (digital viewing)
- `print` - Print-optimized (high quality, CMYK colors)

### Build Commands

```bash
# Compile thesis with default profile
make compile

# Compile with specific profile
make compile PROFILE=draft

# Watch for changes and recompile
make watch PROFILE=screen

# Clean generated files
make clean

# Clean all files including caches
make clean-all

# Run validation tests
make test

# Show available profiles
make profiles

# Get help
make help
```

### Development Workflows

```bash
# Quick development compile
make quick

# Watch sample chapter during development
make watch-sample PROFILE=draft

# Full validation before commit
make validate && make test
```

### CI/CD Integration

The build system is fully integrated with GitHub Actions CI/CD pipeline, automatically
testing all profiles and running comprehensive validation.

## Abbreviation Management

The template includes enhanced abbreviation and glossary utilities for academic writing.

### Using Abbreviations in Text

```typst
#import "config/abbreviations.typ": abbrev

// Auto-expand on first use (citation style)
#abbrev("ML")  // Shows: Machine Learning (ML)
#abbrev("ML")  // Shows: ML (subsequent uses)

// Manual abbreviation
#abbrev("AI", expand: false)  // Always shows: AI
```

### Managing Abbreviations

Use the abbreviation management script to add, remove, and manage abbreviations:

```bash
# Add a new abbreviation
python scripts/manage_abbreviations.py add \
  --key "Machine Learning" \
  --short "ML" \
  --long "A method of data analysis that automates analytical model building"

# List all abbreviations
python scripts/manage_abbreviations.py list --sort short

# Validate abbreviations
python scripts/manage_abbreviations.py validate

# Export to CSV
python scripts/manage_abbreviations.py export --format csv --output abbreviations.csv

# Show statistics
python scripts/manage_abbreviations.py stats
```

### Enhanced Validation

The template now includes detailed abbreviation validation with:

- Duplicate detection
- Format checking (recommended: 2-8 uppercase letters)
- Empty field detection
- Comprehensive error reporting

Abbreviations are automatically validated during compilation, with statistics displayed in glossary pages.

### Optional Glossary and Abbreviations Pages

Enable automatic glossary and abbreviations generation in your thesis endmatter:

```typst
#show: thesis.with(
  // ... other metadata ...
  include_glossary: true,        // Generate glossary page from abbreviations
  include_abbreviations: true,   // Generate abbreviations list page
  // ... rest of configuration ...
)
```

The optional glossary system automatically:

- Generates glossary pages from your abbreviation definitions
- Validates abbreviation data during compilation
- Provides statistics and error reporting
- Supports both separate and combined glossary/abbreviations pages

For advanced usage, you can customize the optional glossary behavior by importing the module directly:

```typst
#import "endmatter/optional-glossary.typ": optional-glossary-abbreviations-page

// Custom combined page
#optional-glossary-abbreviations-page(separate-pages: false, show-statistics: true)
```

## Bibliography and Citation Management

The template provides comprehensive bibliography and citation support aligned with University of Melbourne referencing guidelines.

### Supported Citation Styles

The template includes preset citation styles commonly used in academic disciplines:

- **APA** - American Psychological Association (social sciences)
- **IEEE** - Institute of Electrical and Electronics Engineers (engineering, computing)
- **Numeric** - Numbered references (sciences, mathematics)
- **Author-Year** - Harvard-style author-date citations (humanities, social sciences)
- **Chicago** - Chicago Manual of Style (humanities)
- **MLA** - Modern Language Association (literature, arts)

### Configuring Citation Style

Set your preferred citation style in the thesis metadata:

```typst
#show: thesis.with(
  // ... other metadata ...
  bibliography_style: "apa",  // Options: apa, ieee, numeric, author-year, chicago, mla
  // ... rest of configuration ...
)
```

### Managing References

1. **Create/Edit Bibliography File**: Edit `references.bib` in BibTeX format:

```bibtex
@book{smith2023,
  title={Introduction to Academic Writing},
  author={Smith, John},
  year={2023},
  publisher={Academic Press},
  address={Melbourne}
}

@article{jones2024,
  title={Recent Advances in Research Methodology},
  author={Jones, Mary and Brown, David},
  journal={Journal of Academic Studies},
  volume={45},
  number={2},
  pages={123--145},
  year={2024}
}

@inproceedings{wilson2023,
  title={Conference Paper Title},
  author={Wilson, Robert},
  booktitle={Proceedings of the International Conference},
  pages={567--578},
  year={2023},
  publisher={IEEE}
}
```

2. **Cite References in Text**: Use Typst's built-in citation commands:

```typst
// Author-year style citation
According to @smith2023, academic writing requires...

// Multiple citations
Several studies @jones2024; @wilson2023 have shown...

// Suppress author in citation
The methodology (see @jones2024, p. 125) provides...

// Citation with custom text
As demonstrated in @smith2023 [chap. 2], the approach...
```

### University of Melbourne Referencing Guidelines

**Key Requirements:**

- **Consistency**: Use one citation style throughout your thesis
- **Complete References**: Include all necessary bibliographic details
- **Accuracy**: Ensure all citations correspond to actual references
- **Original Sources**: Cite primary sources where possible

**Discipline-Specific Recommendations:**

- **Arts & Humanities**: MLA or Chicago style
- **Social Sciences**: APA style
- **Sciences & Engineering**: IEEE or numeric style
- **Law**: AGLC (Australian Guide to Legal Citation) - use Chicago as closest approximation

**Best Practices:**

- Cite all sources of information, ideas, and direct quotations
- Include page numbers for direct quotations
- Use "et al." for sources with more than three authors (after first citation)
- Ensure DOI/URL information is current and accessible

### Bibliography Validation

The template includes bibliography validation features:

```bash
# Validate bibliography file format
python scripts/validate_template.py

# Check for missing fields and formatting issues
# Validation runs automatically during compilation
```

### Advanced Citation Features

**Multiple Bibliographies**: Create separate bibliographies for different sections:

```typst
// Primary bibliography
#bibliography("references.bib", title: "References")

// Additional bibliography for appendices
#bibliography("appendix-refs.bib", title: "Appendix References")
```

**Custom Bibliography Styles**: For styles not included in presets, specify custom style files:

```typst
bibliography_style: "custom-style.csl"  // Path to Citation Style Language file
```

## Bibliography Workflow Guide

This section provides a step-by-step workflow for managing references and citations
in your University of Melbourne thesis, aligned with the University's referencing
guidelines and academic integrity requirements.

### Step 1: Choose Your Citation Style

Select an appropriate citation style based on your academic discipline:

```typst
#show: thesis.with(
  bibliography_style: "apa",  // Social sciences, education, psychology
  // bibliography_style: "ieee",  // Engineering, computing, physical sciences
  // bibliography_style: "mla",  // Arts, humanities, literature
  // bibliography_style: "chicago",  // History, some humanities
  // bibliography_style: "numeric",  // Mathematics, some sciences
  // bibliography_style: "author-year",  // Some social sciences, humanities
)
```

### Step 2: Set Up Your Bibliography File

1. **Create or edit `references.bib`** in your project root
2. **Use BibTeX format** with complete bibliographic information
3. **Include all required fields** for your chosen citation style

**Essential Fields by Reference Type:**

```bibtex
@book{smith2023,
  title={Complete Book Title},
  author={Smith, John A.},
  year={2023},
  publisher={Academic Press},
  address={Melbourne, Australia},
  isbn={978-0-123456-78-9}
}

@article{jones2024,
  title={Article Title: Subtitle},
  author={Jones, Mary and Brown, David},
  journal={Journal of Academic Studies},
  volume={45},
  number={2},
  pages={123--145},
  year={2024},
  doi={10.1234/jas.2024.45.2.123}
}

@inproceedings{wilson2023,
  title={Conference Paper Title},
  author={Wilson, Robert},
  booktitle={Proceedings of the International Conference on Research},
  pages={567--578},
  year={2023},
  publisher={IEEE},
  address={Sydney, Australia}
}

@phdthesis{student2023,
  title={Thesis Title},
  author={Student, A. B.},
  school={University of Melbourne},
  year={2023}
}

@online{website2023,
  title={Web Page Title},
  author={Author, First},
  url={https://www.example.com/page},
  year={2023},
  urldate={2023-10-05}
}
```

### Step 3: Cite References in Your Text

**Basic Citations:**

```typst
// Single author citation
According to @smith2023, academic writing requires...

// Multiple authors
Several studies @jones2024; @wilson2023 have shown...

// Suppress author (numeric styles)
The methodology (see @jones2024, p. 125) provides...

// Custom citation text
As demonstrated in @smith2023 [chap. 2], the approach...
```

**Advanced Citation Patterns:**

```typst
// Page-specific citations
The results indicate @smith2023[p. 45] that...

// Multiple pages
See @jones2024[pp. 123--125] for detailed methodology.

// Year-only citations
Research from 2023 @smith2023; @wilson2023 shows...

// Citation with locator
As noted previously @jones2024[see also @wilson2023].
```

### Step 4: Compile and Validate

1. **Compile your thesis:**

   ```bash
   typst compile thesis.typ
   ```

2. **Validate bibliography:**

   ```bash
   python scripts/validate_template.py
   ```

3. **Check for common issues:**

   - Missing citation keys
   - Incomplete bibliographic entries
   - Inconsistent citation style usage

### Step 5: Final Checks Before Submission

**University of Melbourne Requirements:**

- **Complete References**: Ensure all citations have corresponding bibliography entries
- **Consistent Style**: Use one citation style throughout
- **Accurate Details**: Verify all bibliographic information is correct
- **Original Sources**: Prefer primary sources where possible
- **Current URLs**: Ensure web references are accessible and dated

**Academic Integrity Checklist:**

- [ ] All sources are properly cited
- [ ] Direct quotations include page numbers
- [ ] Paraphrased ideas are attributed
- [ ] Personal communications are documented
- [ ] AI-generated content is disclosed and cited
- [ ] Self-citations follow department guidelines

### Troubleshooting Common Issues

**"Citation not found" errors:**

- Check citation key spelling in text vs. bibliography
- Ensure bibliography file path is correct
- Verify BibTeX syntax in `.bib` file

**Formatting inconsistencies:**

- Confirm citation style matches bibliography style
- Check for missing required fields in bibliography entries
- Validate against your discipline's style guide

**Compilation failures:**

- Run `python scripts/validate_template.py` for detailed diagnostics
- Check for malformed BibTeX entries
- Ensure bibliography file is in project root

### Advanced Bibliography Features

**Multiple Bibliography Files:**

```typst
// Primary research bibliography
#bibliography("references.bib", title: "References")

// Additional sources for appendices
#bibliography("appendix-refs.bib", title: "Appendix References")
```

**Custom Citation Commands:**

```typst
// Define custom citation commands for your discipline
#let cite-book = cite.with(style: "chicago-author-date")
#let cite-article = cite.with(style: "apa")

// Use in text
This classic work #cite-book("smith2023") argues that...
```

## Optional Index Workflow

The template provides comprehensive optional index generation capabilities to help readers navigate your thesis content.

### Index Configuration

Enable the optional index in your thesis configuration:

```typst
#show: thesis.with(
  // ... other metadata ...
  include_index: true,
  // Optional: provide custom index entries
  index_entries: (
    "Machine Learning": "15, 23, 45",
    "Neural Networks": "12, 34",
    "Deep Learning": "23, 67-69"
  )
)
```

### Index Features

**Basic Index**: Simple alphabetical listing with page references
**Hierarchical Index**: Support for main terms with sub-entries
**Multi-Column Layout**: Configurable column display for better space utilization
**Combined Index & Glossary**: Integrated index and glossary pages

### Index Entry Types

**Simple Entries**: Direct term-to-page mapping

```typst
index_entries: (
  "Machine Learning": "15, 23, 45",
  "Neural Networks": "12, 34"
)
```

**Hierarchical Entries**: Terms with sub-entries

```typst
index_entries: (
  "Machine Learning": (
    "supervised": "15, 23",
    "unsupervised": "45, 67",
    "definition": "12"
  )
)
```

### Advanced Index Functions

For custom index implementations, use the optional index module functions:

```typst
#import "endmatter/optional-index.typ": optional-index-page, optional-index-with-subentries

// Basic index with custom entries
#optional-index-page(custom-entries: (
  "Algorithm": "25, 67",
  "Data Structure": "12, 89"
))

// Hierarchical index
#optional-index-with-subentries(entries: (
  "Machine Learning": (
    "supervised": "15",
    "unsupervised": "45"
  )
))
```

### Index Best Practices

- **Selective Indexing**: Index only the most important terms and concepts
- **Consistent Terminology**: Use consistent terms throughout your thesis
- **Cross-References**: Include cross-references for related terms
- **Page Ranges**: Use page ranges (e.g., "15-23") for multi-page discussions
- **Sub-Entries**: Use sub-entries for detailed breakdowns of main concepts

### Index Validation

The template includes index validation features:

```bash
# Validate index entries during compilation
# Automatic checks for missing page references and formatting
```

## License

MIT

---

_Created by Dylan A Mordaunt for template demonstration purposes._
