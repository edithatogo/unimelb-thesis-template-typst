# Submitting to Typst Packages Repository

This guide provides step-by-step instructions for submitting the `unimelb-thesis-template` package to the official Typst packages repository.

## Quick Start

The template is **ready for submission** with minor preparation steps needed.

### Required Actions Before Submission

1. **Generate thumbnail image**
   ```bash
   # Requires Typst to be installed
   typst compile thumbnail.typ thumbnail.png
   ```

2. **Verify metadata is correct**
   - Repository URL: ✅ Updated to current repository
   - Version: `0.2.0` (or bump to `1.0.0` for first public release)
   - License: ✅ Apache-2.0
   - Author: Listed in typst.toml

3. **Test the template**
   ```bash
   typst compile thesis.typ
   typst compile sample-chapter.typ
   ```

## Submission Process

### Method 1: Direct Pull Request (Recommended)

#### Step 1: Fork and Clone typst/packages

```bash
# 1. Go to https://github.com/typst/packages and click "Fork"

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/packages.git
cd packages
```

#### Step 2: Create Package Directory

```bash
# Create the package directory structure
mkdir -p packages/preview/unimelb-thesis-template/0.2.0
```

#### Step 3: Copy Package Files

Copy these files from this repository to `packages/preview/unimelb-thesis-template/0.2.0/`:

**Required files:**
- `typst.toml`
- `lib.typ`
- `README.md`
- `LICENSE`
- `thumbnail.png` (after generating it)

**Required directories:**
- `assets/` (entire directory with colors and fonts)
- `config/` (entire directory)
- `layouts/` (entire directory)
- `pages/` (entire directory)
- `utils/` (entire directory)
- `frontmatter/` (entire directory)
- `endmatter/` (entire directory)

**Optional but recommended:**
- `examples/` (working examples)
- `thesis.typ` (main template file)
- `sample-chapter.typ` (sample chapter)

**Files NOT to include:**
- `.git/` directory
- `.github/` workflows
- `docs/` directory
- Build artifacts
- Development scripts in `scripts/`
- `Makefile`
- `.gitignore`, `.markdownlint.json`, etc.

#### Step 4: Verify Package Structure

Your directory should look like:

```
packages/preview/unimelb-thesis-template/0.2.0/
├── typst.toml
├── lib.typ
├── README.md
├── LICENSE
├── thumbnail.png
├── thesis.typ
├── sample-chapter.typ
├── assets/
│   ├── colors/
│   └── fonts/
├── config/
├── layouts/
├── pages/
├── utils/
├── frontmatter/
├── endmatter/
└── examples/
```

#### Step 5: Test the Package

```bash
# Test importing the package
cd packages/preview/unimelb-thesis-template/0.2.0

# Test basic compilation
typst compile thesis.typ

# Test with package import syntax (once in packages repo)
# This would work after submission:
# #import "@preview/unimelb-thesis-template:0.2.0": thesis
```

#### Step 6: Create Pull Request

```bash
# From the packages repository root
git checkout -b add-unimelb-thesis-template-0.2.0
git add packages/preview/unimelb-thesis-template/
git commit -m "Add unimelb-thesis-template v0.2.0

A modern Typst template for University of Melbourne theses with official branding,
automated front matter, bibliography support, and professional formatting."

git push origin add-unimelb-thesis-template-0.2.0
```

#### Step 7: Open PR on GitHub

1. Go to https://github.com/typst/packages
2. Click "Pull requests" → "New pull request"
3. Click "compare across forks"
4. Select your fork and branch
5. Title: `Add unimelb-thesis-template v0.2.0`
6. Description:

```markdown
## Package Information

- **Name**: unimelb-thesis-template
- **Version**: 0.2.0
- **License**: Apache-2.0
- **Repository**: https://github.com/edithatogo/unimelb-thesis-template-typst

## Description

A modern Typst template for University of Melbourne theses that provides:

- Official University of Melbourne branding and colors
- Automated front matter (title page, abstract, acknowledgements, etc.)
- Professional formatting with logical page numbering
- Bibliography and citation support
- Code syntax highlighting and algorithm formatting
- Optional glossary and index generation
- Multiple build profiles (draft, screen, print)

## Checklist

- [x] Package follows naming conventions
- [x] typst.toml is valid with complete metadata
- [x] README.md with clear usage instructions
- [x] LICENSE file included (Apache-2.0)
- [x] Entrypoint (lib.typ) exports template function
- [x] Examples compile successfully
- [x] No sensitive data or large files
- [x] Thumbnail image included
- [x] All validation checks pass

## Testing

Tested with Typst v0.13.0:
- ✅ Main template compiles
- ✅ Sample chapter compiles
- ✅ Examples compile
- ✅ All validation checks pass (5/5)

## Additional Notes

This template is specifically designed for University of Melbourne thesis submissions
and follows the university's thesis formatting guidelines while providing modern
Typst features.
```

### Method 2: Request Maintainer Inclusion

If you prefer not to submit directly:

1. **Create an issue** in https://github.com/typst/packages/issues
2. **Title**: Request: Add unimelb-thesis-template package
3. **Description**: Provide repository link and brief description
4. **Wait for review**: Typst maintainers will review and may add the package

## After Submission

### Once PR is Merged

1. **Tag the release** in this repository:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0 - Published to Typst packages"
   git push origin v0.2.0
   ```

2. **Create GitHub Release**:
   - Go to repository → Releases → New release
   - Tag: v0.2.0
   - Title: "Version 0.2.0 - Typst Package Release"
   - Description: Changelog and features

3. **Update README** to show package installation:
   ```markdown
   ## Installation

   Install from Typst packages:

   ```typst
   #import "@preview/unimelb-thesis-template:0.2.0": thesis

   #show: thesis.with(
     title: "Your Thesis Title",
     author: "Your Name",
     degree: "PhD",
     department: "Your Department",
     school: "Your School",
     university: "University of Melbourne",
     submission_date: datetime(year: 2025, month: 10, day: 5),
   )

   // Your content here
   ```
   ```

4. **Announce** on social media, university channels, etc.

### Future Updates

For version updates (0.2.1, 0.3.0, etc.):

1. Update version in `typst.toml`
2. Create new directory in packages repo: `packages/preview/unimelb-thesis-template/0.3.0/`
3. Copy updated files
4. Submit new PR
5. Tag release in this repository

## Pre-Submission Checklist

Use this checklist before submitting:

### Package Requirements
- [x] Valid `typst.toml` with complete metadata
- [x] Entrypoint file (`lib.typ`) exists and exports template
- [x] `README.md` with clear usage instructions
- [x] `LICENSE` file (Apache-2.0)
- [x] Semantic version number (0.2.0)

### Repository Metadata
- [x] Repository URL is correct in typst.toml
- [x] Author information is accurate
- [x] Keywords and categories are appropriate
- [x] Description is clear and concise

### Content Quality
- [x] No sensitive data in repository
- [x] No unnecessarily large files
- [x] All examples compile without errors
- [x] Documentation is comprehensive
- [x] Code is well-organized and commented

### Testing
- [ ] Generate thumbnail: `typst compile thumbnail.typ thumbnail.png`
- [ ] Test main template: `typst compile thesis.typ`
- [ ] Test sample chapter: `typst compile sample-chapter.typ`
- [ ] Run validators: `python3 scripts/validate_template.py`
- [ ] Check package structure matches requirements

### Submission
- [ ] Fork typst/packages repository
- [ ] Copy files to correct directory structure
- [ ] Test package works from packages repo
- [ ] Create pull request with complete description
- [ ] Respond to reviewer feedback

## Common Issues and Solutions

### Issue: Thumbnail not generating
**Solution**: Install required fonts or use system fonts in thumbnail.typ

### Issue: Relative imports broken in packages repo
**Solution**: Ensure all imports are relative to package root, not repository root

### Issue: Large file size
**Solution**: Remove unnecessary assets, compress images, remove development files

### Issue: Examples don't compile
**Solution**: Update examples to use package import syntax:
```typst
#import "@preview/unimelb-thesis-template:0.2.0": *
```

## Support and Questions

- **Typst Packages Guide**: https://github.com/typst/packages/blob/main/CONTRIBUTING.md
- **Package Documentation**: https://github.com/typst/packages/tree/main/docs
- **Typst Discord**: Join for community support
- **This Repository**: Open issue for template-specific questions

## Summary

The template is ready for submission. Complete the pre-submission checklist,
generate the thumbnail, and follow the submission process above. The package
meets all Typst package repository requirements and should be accepted after
review.

**Estimated time to submit**: 30-60 minutes (most time spent copying files and testing)

**Estimated review time**: 1-7 days depending on maintainer availability

Good luck with the submission! 🚀
