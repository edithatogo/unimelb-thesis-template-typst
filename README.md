# University of Melbourne Thesis Template (Typst)

A modern, state-of-the-art Typst template for University of Melbourne theses, designed to produce professional academic documents with ease.

## Features

### 🎨 Modern Design
- Clean, professional layout following University of Melbourne guidelines
- Responsive design with proper margins and typography
- Support for blind review mode
- Customizable styling and themes

### 📚 Academic Structure
- Complete front matter (title page, abstract, acknowledgements, declaration)
- Automatic table of contents, list of figures, and list of tables
- Chapter-based organization
- Appendix support
- Bibliography management

### 🔧 Advanced Features
- Integration with modern Typst packages (cetz, codly, tablex, etc.)
- Theorem environments (theorem, lemma, corollary, etc.)
- Algorithm formatting
- Code highlighting with line numbers
- Mathematical equation support
- Cross-referencing system

### 📖 Easy Customization
- Well-documented configuration options
- Modular structure for easy modification
- Support for different degree types
- Flexible metadata system

## Quick Start

### Prerequisites
1. Install Typst: https://typst.app/docs/getting-started/
2. Install VS Code with Typst extension (recommended): https://marketplace.visualstudio.com/items?itemName=nvarner.typst-lsp

### Basic Usage

1. **Clone or download this template**
2. **Configure your thesis details** in `main.typ`
3. **Add your content** to the chapter files
4. **Compile** your thesis: `typst compile main.typ`

## ✨ Key Features

### 🎨 Modern Design & Typography

- Clean, professional layout following University of Melbourne guidelines
- Font coverage control for cross-platform compatibility
- University of Melbourne brand colors and styling
- Responsive design with proper margins and spacing
- Support for blind review mode and double-sided printing

### 📚 Complete Academic Structure
- Modular front matter (title page, abstract, acknowledgements, declaration)
- Automatic table of contents, list of figures, tables, and algorithms
- Chapter-based organization with proper numbering
- Appendix support with custom formatting
- Comprehensive bibliography management

### 🔧 Advanced Features (Typst 0.13+)
- **Theorem Environments**: theorion package for theorems, lemmas, corollaries, definitions
- **Algorithm Support**: lovelace package for pseudocode with cross-referencing
- **Enhanced Code**: codly + zebraw for syntax highlighting with line numbers
- **Diagrams**: cetz + fletcher for technical diagrams and flowcharts
- **Advanced Tables**: tablex with professional formatting
- **Units & Numbers**: unify and numbly for scientific notation
- **Word/Character Counting**: Built-in statistics functions

### 📖 Easy Customization & Modularity
- Well-documented configuration options
- Modular structure: `utils/`, `pages/`, `layouts/` directories
- Support for different degree types and departments
- Flexible metadata system with type safety
- Extensive example configurations

## 🚀 Quick Start

### Installation & Setup

1. **Get the template**:
   ```bash
   git clone https://github.com/dylanmordaunt/unimelb-thesis-template-typst.git
   cd unimelb-thesis-template-typst
   ```

2. **Configure your thesis** in `thesis.typ`:
   ```typst
   #show: thesis.with(
     title: "Your Thesis Title",
     subtitle: "Optional Subtitle",
     author: "Dylan A Mordaunt",
     degree: "Doctor of Philosophy",
     department: "Department of Computing and Information Systems",
     school: "School of Computing and Information Systems",
     university: "The University of Melbourne",
     supervisor: "Professor Jane Smith",
     co_supervisor: "Dr. John Doe",
     submission_date: datetime(year: 2024, month: 12, day: 15),
     abstract: [Your abstract here...],
     keywords: ("keyword1", "keyword2", "keyword3"),
     acknowledgements: [Your acknowledgements...],
     declaration: [Your declaration...],
     preface: [Optional preface...],
     // blind: true,        // For blind review
     // double_sided: true, // For printing
   )
   ```

3. **Write your content** and compile:
   ```bash
   typst watch thesis.typ  # Live preview
   typst compile thesis.typ  # Generate PDF
   ```

## 🤖 Automation Features

This template includes comprehensive automation tools for streamlined development:

### Quick Commands

```bash
# Interactive automation menu
./automate.sh

# Direct commands
./automate.sh compile    # Compile thesis
./automate.sh validate   # Run validation scripts
./automate.sh full       # Complete workflow (compile + validate)
./automate.sh backup     # Create timestamped backup
./automate.sh clean      # Remove build artifacts
./automate.sh update     # Check for updates
```

### CI/CD Pipeline

The template includes GitHub Actions workflows for:

- **Automated Compilation**: Ensures thesis compiles without errors
- **Package Validation**: Checks package compatibility
- **Quality Assurance**: Runs linting and formatting checks
- **Release Management**: Automated tagging and releases

### Development Tools

- **Pre-commit Hooks**: Automatic quality checks before commits
- **Validation Scripts**: Python scripts for template validation
- **Package Management**: Automated dependency checking
- **Backup System**: Timestamped backups of important files

## 🏗️ Project Structure
   ```

## 📋 Configuration Options

### Required Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `title` | `str` | Thesis title | `"Machine Learning in Healthcare"` |
| `author` | `str` | Your full name | `"Dylan A Mordaunt"` |
| `degree` | `str` | Degree type | `"Doctor of Philosophy"` |
| `department` | `str` | Department name | `"Computing and Information Systems"` |
| `school` | `str` | School name | `"School of Computing and Information Systems"` |
| `university` | `str` | University | `"The University of Melbourne"` |
| `supervisor` | `str` | Main supervisor | `"Professor Jane Smith"` |
| `submission_date` | `datetime` | Submission date | `datetime(year: 2024, month: 12, day: 15)` |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `subtitle` | `str` | `none` | Thesis subtitle |
| `co_supervisor` | `str` | `none` | Co-supervisor name |
| `abstract` | `content` | `none` | Thesis abstract |
| `keywords` | `array` | `()` | Keywords array |
| `acknowledgements` | `content` | `none` | Acknowledgement text |
| `declaration` | `content` | `none` | Declaration text |
| `preface` | `content` | `none` | Preface text |
| `blind` | `bool` | `false` | Blind review mode |
## 🏗️ Project Structure

```
unimelb-thesis-template-typst/
├── thesis.typ              # Main thesis file
├── lib.typ                 # Template library and functions
├── utils/                  # Utility functions and styling
│   └── style.typ          # Font config, theorem environments, packages
├── pages/                  # Page components
│   ├── title.typ          # Title page
│   ├── abstract.typ       # Abstract page
│   ├── declaration.typ    # Declaration page
│   └── acknowledgements.typ # Acknowledgements page
├── layouts/                # Layout configurations
│   └── document.typ       # Document layout settings
├── references.bib          # Bibliography database
├── example-config.typ      # Configuration examples
├── sample-chapter.typ      # Chapter writing examples
├── unimelb-logo.svg        # University logo
├── README.md              # This documentation
├── QUICKSTART.md          # Quick start guide
├── LICENSE                # MIT License
└── .gitignore            # Git ignore rules
```

## 🎯 Advanced Usage Examples

### Theorem Environments

```typst
#theorem("Central Limit Theorem")[
  Let $X_1, X_2, ..., X_n$ be i.i.d. random variables with finite mean $mu$ and variance $sigma^2$. Then:
  $
  sqrt(n) (bar(X) - mu) / sigma -> cal(N)(0, 1)
  $
  as $n -> infinity$.
]

#proof[
  The proof follows from the characteristic function approach...
]

#definition("Convex Function")[
  A function $f: RR^n -> RR$ is convex if for all $x, y in RR^n$ and $lambda in [0,1]$:
  $
  f(lambda x + (1-lambda)y) <= lambda f(x) + (1-lambda)f(y)
  $
]
```

### Algorithm Formatting

```typst
#algorithm(
  pseudocode(
    no-number,
    [*Input:* Training data $cal(D) = {(x_i, y_i)}_{i=1}^n$],
    [*Output:* Learned parameters $theta$],
    [*Algorithm:* Gradient Descent],
    block(
      numbering: none,
      [Initialize $theta_0$ randomly],
      [*for* $t = 1$ *to* $T$ *do*],
      block(
        numbering: none,
        [Compute loss $cal(L)(theta_{t-1})$],
        [Compute gradient $nabla_theta cal(L)(theta_{t-1})$],
        [Update $theta_t = theta_{t-1} - eta nabla_theta cal(L)(theta_{t-1})$],
      ),
      [*end for*],
      [*return* $theta_T$],
    )
  ),
  caption: [Gradient descent algorithm]
)
```

### Enhanced Code Blocks

```typst
#code-block(
  ```python
  import numpy as np
  from sklearn.model_selection import train_test_split

  class NeuralNetwork:
      def __init__(self, layers):
          self.layers = layers
          self.weights = [np.random.randn(y, x)
                         for x, y in zip(layers[:-1], layers[1:])]

      def forward(self, X):
          for w in self.weights:
              X = np.maximum(0, X @ w.T)  # ReLU activation
          return X
  ```,
  lang: "python"
)
```

### Diagrams with CeTZ

```typst
#figure(
  cetz.canvas({
    import cetz.draw: *

    // Neural network architecture
    circle((0, 0), radius: 0.5, fill: blue, name: "input")
    content((0, 0), [*Input*])

    circle((2, 1), radius: 0.5, fill: green, name: "hidden1")
    circle((2, -1), radius: 0.5, fill: green, name: "hidden2")
    content((2, 1), [*Hidden*])
    content((2, -1), [*Layer*])

    circle((4, 0), radius: 0.5, fill: red, name: "output")
    content((4, 0), [*Output*])

    // Connections
    line("input", "hidden1", mark: (end: ">"))
    line("input", "hidden2", mark: (end: ">"))
    line("hidden1", "output", mark: (end: ">"))
    line("hidden2", "output", mark: (end: ">"))
  }),
  caption: [Simple neural network architecture]
)
```

### Advanced Tables

```typst
#figure(
  thesis-table(
    columns: (auto, 1fr, 1fr, 1fr),
    align: (center, left, center, right),
    table.header[*Method*][*Description*][*Accuracy*][*Time*],
    [SVM], [Support Vector Machine], [85.2%], [2.3s],
    [RF], [Random Forest], [87.1%], [1.8s],
    [NN], [Neural Network], [91.4%], [45.2s],
    [CNN], [Convolutional Neural Network], [94.7%], [120.1s],
  ),
  caption: [Comparison of machine learning methods]
)
```

## 🎨 Customization

### Font Configuration

The template includes comprehensive font coverage:

```typst
// Automatic font fallback configuration
fonts: (
  serif: font-with-coverage("Times New Roman", ("latin", "cjk")),
  sans: ("Arial", "Liberation Sans", "DejaVu Sans"),
  mono: font-with-coverage("JetBrains Mono", ("latin", "cjk")),
)
```

### Color Scheme

University of Melbourne brand colors are pre-configured:

```typst
colors: (
  primary: rgb("#0F4C81"),    // University blue
  secondary: rgb("#2E2E2E"),  // Dark gray
  accent: rgb("#8B0000"),     // Accent red
)
```

### Page Layout Options

```typst
// Double-sided printing with proper margins
set page(
  paper: "a4",
  margin: if double_sided {
    (
      top: 2.5cm, bottom: 2.5cm,
      left: 3cm, right: 2.5cm,
      inside: 3cm, outside: 2.5cm,
    )
  } else {
    (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm)
  }
)
```

## 📦 Package Ecosystem

This template leverages the latest Typst packages:

| Package | Version | Purpose |
|---------|---------|---------|
| `cetz` | 0.3.1 | Technical diagrams and plots |
| `codly` | 1.1.0 | Code syntax highlighting |
| `tablex` | 0.0.8 | Advanced table formatting |
| `theorion` | 0.1.0 | Theorem environments |
| `fletcher` | 0.5.1 | Flowcharts and diagrams |
| `lovelace` | 0.3.0 | Algorithm pseudocode |
| `numbly` | 0.1.0 | Advanced numbering |
| `unify` | 0.7.0 | Unit formatting |
| `zebraw` | 0.4.0 | Code with line numbers |
| `i-figured` | 0.2.4 | Figure numbering |

## 🔍 Best Practices

### File Organization
- Use separate chapter files: `#include "chapters/chapter1.typ"`
- Store figures in `figures/` directory
- Keep bibliography in `references.bib`
- Use descriptive filenames

### Writing Tips
- Leverage semantic markup for better structure
- Use cross-references: `@theorem:pythagoras`
- Enable blind review mode for submission
- Utilize word counting: `#display-word-count(content)`

### Performance Optimization
- Use `typst watch` for live development
- Compile to PDF for final output
- Optimize large images and diagrams

## 🐛 Troubleshooting

### Common Issues

**Package Installation:**
```bash
# Packages are downloaded automatically by Typst
# No manual installation required
```

**Font Warnings:**
- Template includes comprehensive fallbacks
- Install preferred fonts for best appearance
- Check `utils/style.typ` for font configuration

**Compilation Errors:**
- Verify Typst version 0.13+
- Check syntax in configuration
- Ensure all referenced files exist

### Support Resources

- [Typst Documentation](https://typst.app/docs/)
- [Typst Universe](https://typst.app/universe) - Package repository
- [Modern NJU Thesis](https://github.com/nju-lug/modern-nju-thesis) - Reference implementation
- [Modern SJTU Thesis](https://github.com/tzhtaylor/modern-sjtu-thesis) - Alternative approach

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with comprehensive testing
4. Update documentation as needed
5. Submit a pull request with detailed description

### Development Guidelines

- Follow Typst best practices and conventions
- Test on multiple platforms (macOS, Windows, Linux)
- Ensure compatibility with Typst 0.13+
- Update version numbers appropriately
- Maintain comprehensive documentation

## 📄 License

This template is released under the **MIT License**. See `LICENSE` for full details.

## 🙏 Acknowledgments

**Author:** Dylan A Mordaunt, PhD Candidate, University of Melbourne

**Inspiration & References:**
- [Modern NJU Thesis](https://github.com/nju-lug/modern-nju-thesis) - Modular structure and package integration
- [Modern SJTU Thesis](https://github.com/tzhtaylor/modern-sjtu-thesis) - Advanced features and documentation
- [Typst Community](https://github.com/typst) - Core development and package ecosystem
- University of Melbourne academic guidelines and branding

**Special Thanks:**
- Typst development team for the amazing typesetting system
- Open-source community for comprehensive package ecosystem
- University of Melbourne for academic excellence standards

---

**Latest Updates:** This template is actively maintained and updated with the latest Typst features. For questions or suggestions, please open an issue on [GitHub](https://github.com/dylanmordaunt/unimelb-thesis-template-typst).
3. **Write your content** in the main file or separate chapter files
4. **Compile** using:
   ```bash
   typst compile thesis.typ
   ```
   Or use `typst watch thesis.typ` for live preview

## Configuration

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `title` | Your thesis title | `"Machine Learning in Healthcare"` |
| `author` | Your full name | `"John Smith"` |
| `degree` | Your degree | `"Doctor of Philosophy"` |
| `department` | Your department | `"Department of Computing and Information Systems"` |
| `school` | Your school | `"School of Computing and Information Systems"` |
| `university` | University name | `"The University of Melbourne"` |
| `supervisor` | Main supervisor | `"Dr. Jane Doe"` |
| `submission_date` | Submission date | `"September 2025"` |

### Optional Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `subtitle` | Thesis subtitle | `none` |
| `co_supervisor` | Co-supervisor name | `none` |
| `abstract` | Thesis abstract | `none` |
| `keywords` | Keywords array | `()` |
| `acknowledgements` | Acknowledgement text | `none` |
| `declaration` | Declaration text | `none` |
| `preface` | Preface text | `none` |
| `blind` | Blind review mode | `false` |

## Structure

```
unimelb-thesis-template-typst/
├── thesis.typ              # Main thesis file
├── lib.typ                 # Template library and functions
├── references.bib          # Bibliography file
├── README.md              # This file
└── figures/               # Directory for images and figures
```

## Advanced Usage

### Chapter Organization

You can organize your thesis into separate chapter files:

```typst
// In thesis.typ
= Introduction
#include "chapters/introduction.typ"

= Literature Review
#include "chapters/literature.typ"

// ... more chapters
```

### Custom Environments

#### Theorems and Proofs
```typst
#theorem("Pythagorean Theorem")[
  For a right triangle with legs $a$ and $b$, and hypotenuse $c$:
  $a^2 + b^2 = c^2$
]

#proof[
  The proof follows from the properties of similar triangles...
]
```

#### Algorithms
```typst
#algorithm[
  ```python
  def binary_search(arr, target):
      left, right = 0, len(arr) - 1
      while left <= right:
          mid = (left + right) // 2
          if arr[mid] == target:
              return mid
          elif arr[mid] < target:
              left = mid + 1
          else:
              right = mid - 1
      return -1
  ```
][Binary search algorithm]
```

#### Enhanced Tables
```typst
#figure(
  thesis-table(
    columns: (1fr, 1fr, 1fr),
    align: (left, center, right),
    [*Method*], [*Accuracy*], [*Time*],
    [SVM], [85.2%], [2.3s],
    [Random Forest], [87.1%], [1.8s],
    [Neural Network], [91.4%], [45.2s],
  ),
  caption: [Comparison of classification methods]
)
```

### Mathematical Notation

```typst
// Inline math
The equation $E = mc^2$ is fundamental in physics.

// Display math
$
integral_0^infinity e^(-x^2) dx = sqrt(pi)/2
$

// Numbered equations
$
frac(d){dx} integral_a^x f(t) dt = f(x)
$ <fundamental-theorem>
```

### Bibliography Management

Add references to `references.bib`:

```bibtex
@article{smith2023,
  title={A Great Paper},
  author={Smith, John},
  journal={Journal of Excellent Research},
  year={2023}
}
```

Cite in your text:
```typst
As shown by @smith2023, this approach is effective.
```

## Customization

### Fonts
The template uses Times New Roman as the primary font. To change fonts:

```typst
set text(
  font: ("Your Font", "Fallback Font"),
  size: 12pt,
)
```

### Colors and Styling
Modify colors and styling in `lib.typ`:

```typst
// Custom link color
show link: set text(fill: rgb("#1e40af"))

// Custom heading colors
show heading: set text(fill: rgb("#1f2937"))
```

### Page Layout
Adjust margins and layout:

```typst
set page(
  margin: (
    top: 2.5cm,
    bottom: 2.5cm,
    left: 3cm,
    right: 3cm,
  ),
)
```

## Packages Used

This template leverages several Typst packages for enhanced functionality:

- **cetz**: For diagrams and plots
- **codly**: For code highlighting and line numbers
- **tablex**: For advanced table formatting
- **theorion**: For theorem environments
- **unify**: For unit formatting
- **zero**: For number formatting
- **i-figured**: For figure numbering

## Best Practices

### File Organization
- Keep chapters in separate files for better organization
- Store figures in a dedicated `figures/` directory
- Use descriptive filenames for all assets

### Writing Tips
- Use semantic markup (headings, lists, emphasis)
- Leverage cross-references for figures, tables, and equations
- Keep bibliography entries consistent
- Use blind review mode for submission

### Performance
- Use `typst watch` for live preview during writing
- Compile to PDF when finalizing
- Keep large figures optimized

## Troubleshooting

### Common Issues

**Package not found errors:**
- Ensure all required packages are installed
- Check package versions in `lib.typ`

**Font warnings:**
- Install required fonts on your system
- The template includes fallback fonts

**Compilation errors:**
- Check for syntax errors in Typst code
- Ensure all referenced files exist

### Getting Help

- [Typst Documentation](https://typst.app/docs/)
- [Typst Forum](https://forum.typst.app/)
- [Typst Discord](https://discord.gg/2uDybryKPe)

5. Submit a pull request

## 🏛️ University Compliance

This template is designed to comply with the University of Melbourne's official requirements for graduate research theses.

### Graduate Research Thesis Preparation Process

**Version 3 (11 June 2025)** - Current compliance standards:

#### Required Elements

- **Title Page**: Official University logo, candidate details, degree information
- **Abstract**: Maximum 300 words, clear summary of research
- **Declaration**: Original work statement, word count declaration
- **Table of Contents**: Complete with page numbers
- **List of Figures/Tables**: Comprehensive listings
- **Main Content**: Chapters with proper formatting
- **Bibliography**: Consistent citation style
- **Appendices**: Supplementary materials

#### Formatting Standards

- **Paper Size**: A4 (210 × 297 mm)
- **Margins**: 2.5 cm minimum on all sides
- **Font**: Times New Roman 12pt or equivalent
- **Line Spacing**: 1.5 lines
- **Page Numbering**: Roman numerals for prelims, Arabic for main content

#### Official Branding

- **Logo Usage**: Official University logo on title page only
- **Colors**: University brand colors throughout document
- **Fonts**: Fraunces (headings) and Source Sans Pro (body text)

### Design System Compliance

This template implements the University of Melbourne's Gen 3 Design System:

#### Color Palette

```typst
// Primary brand colors
#let traditional-heritage-100 = rgb("#000F46")
#let mt-william-light-100 = rgb("#ABC1A7")
#let river-yarra-100 = rgb("#00ADEF")

// Secondary colors
#let arts-100 = rgb("#C70039")
#let commerce-100 = rgb("#006747")
#let environment-100 = rgb("#8DC63F")
```

#### Typography

- **Headings**: Fraunces (serif)
- **Body Text**: Source Sans Pro (sans-serif)
- **Monospace**: For code and technical content

### Accessibility Standards

- **WCAG 2.1 AA Compliance**: Minimum contrast ratios
- **Color Blind Friendly**: Alternative indicators for color-dependent information
- **Screen Reader Compatible**: Semantic markup and alt text

## 🛠️ Development & Quality Assurance

This template includes comprehensive development tooling for quality control and automated maintenance.

### CI/CD Pipeline

GitHub Actions workflow provides automated quality assurance:

#### Automated Checks

- **Markdown Linting**: Ensures consistent documentation formatting
- **Typst Compilation**: Validates template compiles without errors
- **Template Validation**: Checks for required elements and formatting
- **Package Management**: Verifies all dependencies are available
- **Release Automation**: Automated version tagging and releases

#### Quality Gates

```yaml
# Key workflow steps
- name: Lint Markdown
  run: markdownlint-cli2 "**/*.md"

- name: Compile Template
  run: typst compile main.typ

- name: Validate Template
  run: python scripts/validate_template.py

- name: Check Packages
  run: python scripts/check_packages.py
```

### Development Tools

#### Pre-commit Hooks

Automated quality control before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/markdownlint/markdownlint
    rev: v0.13.0
    hooks:
      - id: markdownlint

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
```

#### Validation Scripts

**Template Validator** (`scripts/validate_template.py`):
- Checks for required thesis elements
- Validates formatting compliance
- Ensures proper file structure

**Package Checker** (`scripts/check_packages.py`):
- Verifies Typst package availability
- Checks version compatibility
- Updates package references

**Update Script** (`scripts/update_template.py`):
- Automated template updates
- Package version management
- Compliance checking

### Code Quality Standards

#### Linting Configuration

```json
// .markdownlint.json
{
  "default": true,
  "MD013": false,
  "MD024": false,
  "MD033": false
}
```

#### Best Practices

- **Semantic Versioning**: Major.Minor.Patch format
- **Conventional Commits**: Structured commit messages
- **Automated Testing**: CI/CD validation
- **Documentation**: Comprehensive README and inline comments

### Maintenance & Updates

#### Automated Updates

- **Package Updates**: Regular dependency updates
- **Typst Compatibility**: Version compatibility checks
- **University Guidelines**: Compliance with latest requirements

#### Version Control

- **Git Flow**: Feature branches and releases
- **Semantic Releases**: Automated versioning
- **Changelog**: Detailed change documentation

## Contributing

We welcome contributions to improve this template while maintaining University compliance.

### Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-repo/unimelb-thesis-template-typst.git
   cd unimelb-thesis-template-typst
   ```

2. **Install development dependencies**

   ```bash
   pip install -r requirements-dev.txt
   pre-commit install
   ```

3. **Run quality checks**

   ```bash
   pre-commit run --all-files
   python scripts/validate_template.py
   ```

### Contribution Guidelines

#### Code Standards

- Follow Typst best practices
- Maintain University branding compliance
- Include comprehensive documentation
- Add tests for new features

#### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

#### Testing Requirements

- All CI/CD checks must pass
- Template must compile successfully
- Maintain compliance with University standards
- Update documentation for changes

### Areas for Contribution

#### High Priority

- **Accessibility Improvements**: Enhanced screen reader support
- **Internationalization**: Multi-language support
- **Performance Optimization**: Faster compilation times

#### Feature Requests

- **Additional Packages**: New Typst packages integration
- **Template Variants**: Different thesis formats
- **Export Options**: Additional output formats

#### Documentation

- **Usage Examples**: More comprehensive examples
- **Troubleshooting Guide**: Common issues and solutions
- **Migration Guide**: Updating from older versions

## License

This template is released under the MIT License. See `LICENSE` for details.

## Acknowledgments

- Inspired by various open-source Typst thesis templates
- Built using modern Typst features and packages
- Designed for the University of Melbourne academic community

---

_For the latest updates and additional resources, visit the [GitHub repository](https://github.com/your-repo/unimelb-thesis-template-typst)._
