# Typst Package Submission Guide

This document outlines the steps to submit the `unimelb-thesis-template` to the official Typst package repository at https://github.com/typst/packages.

## Current Status

✅ **Repository is ready for submission** - All validation checks pass and the template meets Typst package standards.

## Submission Process

### Prerequisites Checklist

Before submitting, ensure:

- ✅ **Package metadata**: `typst.toml` is complete and valid
- ✅ **Entrypoint**: `lib.typ` exports the template function
- ✅ **License**: Open source license (Apache-2.0) specified
- ✅ **Version**: Semantic versioning (0.2.0)
- ✅ **README**: Clear documentation with usage examples
- ✅ **Examples**: Working examples that compile successfully
- ✅ **Repository**: Clean git history, no sensitive data
- ⚠️ **Thumbnail**: Need to verify/create thumbnail image for package listing

### Typst Packages Repository Requirements

According to https://github.com/typst/packages/tree/main/docs:

1. **Package Structure**
   - Must have `typst.toml` with valid package metadata
   - Must have entrypoint file specified in `typst.toml`
   - Must include LICENSE file
   - Must include README.md with usage documentation

2. **Package Naming**
   - Package name: `unimelb-thesis-template`
   - Must be unique in the package registry
   - Should be descriptive and lowercase with hyphens

3. **Version Requirements**
   - Must use semantic versioning (MAJOR.MINOR.PATCH)
   - Current version: `0.2.0`
   - Each submission must have a unique version number

4. **Content Requirements**
   - No bundled binaries or large files
   - Assets should be reasonably sized
   - No sensitive data or credentials
   - All dependencies properly declared

### Issues to Address Before Submission

#### 1. Thumbnail Image (Required)

The `typst.toml` references `thumbnail = "unimelb-logo.svg"` but this file needs to be:
- Created or obtained (official UoM logo not included due to licensing)
- Should be a representative preview image of the template
- Recommended: Create a sample page preview instead of using the logo

**Action needed**: Create a thumbnail image showing a sample thesis page.

#### 2. Repository URL

Current repository URL in `typst.toml`:
```toml
repository = "https://github.com/dylanmordaunt/unimelb-thesis-template-typst"
```

**Action needed**: Verify this is the correct canonical repository URL. If the repository has moved to `edithatogo/unimelb-thesis-template-typst`, update the URL.

#### 3. Package Version

Current version: `0.2.0`

**Action needed**: Decide if this should be `0.2.0` (current) or bump to `1.0.0` for first public release.

## Submission Steps

### Option 1: Submit via Pull Request to typst/packages (Recommended)

1. **Fork the typst/packages repository**
   ```bash
   # Visit https://github.com/typst/packages and click "Fork"
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/packages.git
   cd packages
   ```

3. **Create package directory**
   ```bash
   mkdir -p packages/preview/unimelb-thesis-template/0.2.0
   ```

4. **Copy package files**
   Copy the following files from this repository:
   - `typst.toml`
   - `lib.typ`
   - `thesis.typ`
   - `README.md`
   - `LICENSE`
   - All directories: `assets/`, `config/`, `layouts/`, `pages/`, `utils/`, `frontmatter/`, `endmatter/`, `examples/`
   - Any other files needed for the template to function

5. **Create/update thumbnail**
   ```bash
   # Create a preview image (PNG recommended, max 512x512px)
   # Place in packages/preview/unimelb-thesis-template/0.2.0/
   ```

6. **Test the package locally**
   ```bash
   # From the packages repository root
   typst compile --root . packages/preview/unimelb-thesis-template/0.2.0/thesis.typ
   ```

7. **Create pull request**
   ```bash
   git checkout -b add-unimelb-thesis-template
   git add packages/preview/unimelb-thesis-template/
   git commit -m "Add unimelb-thesis-template v0.2.0"
   git push origin add-unimelb-thesis-template
   ```

8. **Open PR on GitHub**
   - Go to https://github.com/typst/packages
   - Open a pull request from your fork
   - Title: "Add unimelb-thesis-template v0.2.0"
   - Description: Brief description of the template and its purpose

### Option 2: Request Package Maintainer to Submit

If you don't want to submit directly, you can:

1. Create a GitHub issue in typst/packages requesting package inclusion
2. Provide link to this repository
3. Confirm all requirements are met
4. Wait for Typst team to review and add the package

## Post-Submission

After the package is accepted:

1. **Tag the release** in this repository:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0 - Typst package submission"
   git push origin v0.2.0
   ```

2. **Update documentation** to reference the package:
   ```typst
   #import "@preview/unimelb-thesis-template:0.2.0": thesis
   ```

3. **Monitor feedback** from users and address issues

4. **Plan updates**: Future versions will need new submissions to typst/packages

## Pre-Submission Checklist

Before submitting, complete these tasks:

- [ ] Create appropriate thumbnail image (not university logo)
- [ ] Verify repository URL in typst.toml is correct
- [ ] Decide on version number (0.2.0 or 1.0.0)
- [ ] Test package installation works from typst/packages structure
- [ ] Review all documentation for accuracy
- [ ] Ensure no sensitive data in repository
- [ ] Verify all examples compile without errors
- [ ] Check file sizes are reasonable (no large unnecessary files)
- [ ] Confirm license is appropriate (Apache-2.0)

## Recommendations

### Thumbnail Creation

Create a simple thumbnail showing the template:

```typst
// thumbnail.typ - Generate thumbnail image
#set page(width: 512pt, height: 512pt, margin: 0pt)
#set text(size: 10pt)

#import "@preview/unimelb-thesis-template:0.2.0": *

// Show a miniature version of the title page or first page
// Export as PNG: typst compile thumbnail.typ thumbnail.png
```

Alternatively, create a simple graphic showing:
- University of Melbourne branding
- "Thesis Template" text
- Sample page elements

### Version Strategy

Consider bumping to `1.0.0` for first public release to indicate:
- Template is production-ready
- API is stable
- Breaking changes will follow semver conventions

### Repository Organization

Ensure the repository stays organized:
- Keep main template files in root
- Examples in `examples/` directory
- Documentation in `docs/`
- Assets properly organized

## Need Help?

- Read the full submission guide: https://github.com/typst/packages/blob/main/CONTRIBUTING.md
- Review existing package submissions for examples
- Ask questions in Typst Discord or GitHub Discussions
- Check package requirements: https://github.com/typst/packages/tree/main/docs

## Current Validation Status

Last validation: 2025-10-05

```
✅ Directory structure is valid
✅ Required files are present
✅ typst.toml is valid
✅ Color definitions are valid
✅ Typst syntax validation completed
Validation Results: 5/5 checks passed 🎉
```

The template is ready for submission pending the action items above.
