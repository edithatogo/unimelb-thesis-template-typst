# University of Melbourne Thesis Template

This is a modernized version of the University of Melbourne PhD thesis template. It has been updated to use modern LaTeX packages and best practices, making it easier to use, customize, and maintain. The template complies with the latest University of Melbourne thesis preparation guidelines (version 3, 11 June 2025).

## Features

* Modern Packages: Utilizes `biblatex` for bibliography, `fontspec` for Unicode fonts, `geometry` for page layout, `hyperref` for PDF features, `microtype` for typography, and more.
* Structured Example: A comprehensive `example/` directory showcasing common thesis elements like figures, tables, equations, and code listings.
* Automated Build: Includes a `.latexmkrc` file for automated compilation with `lualatex` and `biber`.
* Code Quality: Pre-configured for `chktex` (linter) and `latexindent` (formatter).
* Clear Customization: Well-commented class file (`template/Thesis.cls`) and example files.
* CI/CD Integration: GitHub Actions for automated compilation, linting, formatting, and releases.
* Latest Guidelines Compliance: Updated to 2025 thesis preparation guidelines, including ORCID support, AI declarations, and no university logo usage.

## Compiled Example

A compiled PDF example is available for immediate download:

* **[Thesis-example.pdf](Thesis-example.pdf)** - Complete compiled thesis example in the repository root
* **[example/Thesis-compiled.pdf](example/Thesis-compiled.pdf)** - Same file in the example directory

These files demonstrate the template's output and can be used as references for formatting and structure.

## Requirements

* A full LaTeX distribution, such as [TeX Live](https://www.tug.org/texlive/), [MiKTeX](https://miktex.org/), or [MacTeX](https://www.tug.org/mactex/).
* `biber`: For processing the bibliography (usually included with TeX distributions).
* `chktex` (optional): For linting LaTeX code.
* `latexindent` (optional): For formatting LaTeX code.

## Usage

### Local Compilation

1. Navigate to the `example` directory: `cd example`
2. Run `latexmk`:

    ```bash
    latexmk Thesis.tex
    ```

    This will compile the document (`Thesis.tex`), run `biber` for the bibliography, and re-compile as needed, producing `Thesis.pdf` in the `example/out/` directory.
3. To clean up auxiliary files:

    ```bash
    latexmk -c
    ```

    And to clean up all generated files (including PDF):

    ```bash
    latexmk -C
    ```

### Usage with Overleaf

1. **Upload:** Download this template as a ZIP file and upload it to your Overleaf project.
2. **Compiler:** In the Overleaf menu, set the "LaTeX engine" to `LuaLaTeX`.
3. **Main Document:** Ensure the main document is set to `example/Thesis.tex`. Overleaf usually detects this, but you can confirm in the project settings.
4. **Compile:** Click "Recompile".

### Linting (Optional)

To lint the LaTeX code (from the repository root):

```bash
chktex **/*.tex # Or specify individual files
```

### Formatting (Optional)

To format the LaTeX code (from the repository root, this will modify files in place):

```bash
latexindent -w -s -y **/*.tex # Or specify individual files
```

## Customization

The primary files you'll edit are within the `example/` directory:

* **`example/Thesis.tex`**: This is the main file for your thesis.
  * Set metadata like `\title`, `\authors`, `\degree`, `\university`, `\department`, `\school`, `\supervisor`, etc. here.
  * Include or exclude chapters and preamble sections.
* **`example/Chapters/`**: Contains the individual chapters of your thesis (e.g., `Chapter1.tex`). Add, remove, or rename files here and update their inclusion in `example/Thesis.tex`.
* **`example/Preamble/`**: Contains pre-main matter content like `Abstract.tex`, `Acknowledgements.tex`, `Declaration.tex`, and `Preface.tex`. Edit these to add your own content.
* **`example/Bibliography.bib`**: This is your bibliography file. Add your references here in BibTeX format.
* **`example/Figures/`**: Place your figure files (PDF, PNG, JPG, EPS) in this directory.

Advanced customization can be done in `template/Thesis.cls`:

* **Fonts:**
  * The template uses `fontspec` and defaults to Latin Modern fonts.
  * To change fonts, uncomment and modify the relevant lines in `template/Thesis.cls` (search for `\usepackage{fontspec}`). For example:

    ```latex
    % \setmainfont{Times New Roman}
    % \setsansfont{Arial}
    % \setmonofont{Courier New}
    ```

  * Ensure the fonts you choose are available on your system or on Overleaf.
* **Bibliography Style:**
  * The template uses `biblatex` with `style=numeric-comp`.
  * You can change the style in `template/Thesis.cls` by modifying the `\usepackage[backend=biber, style=...] {biblatex}` line. Common styles include `authoryear`, `apa`, `mla`, etc. Refer to the `biblatex` documentation for available styles and options.
* **`hyperref` Colors:**
  * Link colors are defined in `template/Thesis.cls` within the `\usepackage[...]{hyperref}` command. You can change `linkcolor`, `citecolor`, and `urlcolor` (e.g., to `black` for printing if desired).
* **Other Class Options:** The `Thesis.cls` file is commented to explain various sections and package choices. For deeper modifications, refer to the comments and the documentation of the respective LaTeX packages.

## Troubleshooting

* **Compilation Errors:**
  * Check the LaTeX log file (`example/out/Thesis.log`) for detailed error messages.
  * Ensure all necessary packages are installed.
  * If using `latexmk`, it typically handles multiple runs. If compiling manually, you might need: `lualatex Thesis.tex` -> `biber Thesis` -> `lualatex Thesis.tex` -> `lualatex Thesis.tex`.
* **Fonts Not Found:** If you've changed fonts via `fontspec`, ensure they are correctly named and installed on your system (or supported by Overleaf).
* **Bibliography Issues:**
  * Ensure `biber` is run correctly (automated by `latexmk`).
  * Check `Bibliography.bib` for syntax errors in your BibTeX entries.
  * Ensure all cited keys exist in your `.bib` file.
* **EPS Figures:** If you have issues with EPS figures, ensure `epstopdf` is working or pre-convert them to PDF. The template comments out `\usepackage{epstopdf}` in `Thesis.cls` as `lualatex` often handles this, but it can be re-enabled if needed.

## LaTeX Best Practices

This template attempts to follow several LaTeX best practices:

* **Vector Graphics:** Use vector graphics (PDF, EPS) for diagrams, plots, and illustrations whenever possible to ensure they scale without loss of quality. Use raster graphics (PNG, JPG) for photographs.
* **`booktabs` for Tables:** Use the `booktabs` package for professional-looking tables (avoid vertical rules, use horizontal rules sparingly). See `example/Chapters/Chapter1.tex`.
* **`microtype` for Typography:** The `microtype` package is included to improve the visual appearance of text (e.g., character protrusion, font expansion).
* **`csquotes` for Quotations:** The `csquotes` package provides context-sensitive quotation marks and is recommended for use with `biblatex`.
* **Semantic Markup:** Use commands and environments for their semantic meaning (e.g., `\emph` for emphasis, specific theorem environments) rather than just for visual styling.
* **Separate Content and Presentation:** Keep your main content in `.tex` files within `Chapters/` and `Preamble/`. Styling is primarily handled by `template/Thesis.cls`.

## Contributing

Contributions to improve this template are welcome! Please feel free to submit a pull request or open an issue with suggestions or bug reports.
(This is a placeholder, you can expand this section if you wish).

## License

This template itself is provided under a permissive license like MIT or CC0 (you should choose one and add a `LICENSE` file).
The University of Melbourne logo is subject to the University's branding guidelines and copyright.
Any documents produced using this template are the property and responsibility of the author.

**Placeholder for License Choice:**
You should choose a license (e.g., MIT License) and add a `LICENSE.md` file to the repository root.
Example text for MIT License:

```text
MIT License

Copyright (c) [Year] [Your Name/Group]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Remember to replace `[Year]` and `[Your Name/Group]`.

## Note

This README provides a starting point. Feel free to expand or modify it further.
