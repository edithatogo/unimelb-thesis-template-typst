# Quick Start Guide

## 1. Install Typst
```bash
# Using Homebrew (macOS)
brew install typst

# Or download from https://typst.app/
```

## 2. Configure Your Thesis
Edit `thesis.typ` and replace the placeholder values with your information:

```typst
#show: thesis.with(
  title: "Your Thesis Title",
  author: "Your Full Name",
  degree: "Doctor of Philosophy",
  // ... other fields
)
```

## 3. Add Your Content
Replace the placeholder text in `thesis.typ` with your actual thesis content.

## 4. Compile
```bash
# Compile once
typst compile thesis.typ

# Watch for changes
typst watch thesis.typ
```

## 5. Customize (Optional)
- Modify fonts in `lib.typ`
- Adjust page margins and layout
- Add custom styling
- Include additional packages
- Choose bibliography style: Set `bibliography_style` in `thesis.typ`
  (options: "apa", "ieee", "numeric", "author_year", "chicago", "mla")

## File Structure
```
├── thesis.typ          # Main thesis file
├── lib.typ            # Template library
├── references.bib     # Bibliography
├── README.md          # Documentation
├── LICENSE            # License
├── .gitignore         # Git ignore rules
├── figures/           # Image directory
├── sample-chapter.typ # Example chapter
└── example-config.typ # Configuration example
```

## Key Features
- ✅ Professional University of Melbourne formatting
- ✅ Automatic table of contents and lists
- ✅ Bibliography management
- ✅ Theorem and algorithm environments
- ✅ Code highlighting
- ✅ Cross-referencing
- ✅ Blind review mode
- ✅ Modern Typst packages integration
