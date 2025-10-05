# University of Melbourne Logos

This directory should contain the official University of Melbourne logo files.

## Required Files

- `unimelb-logo-official.svg` - Official University of Melbourne logo (SVG format)

## Where to Get the Logo

The official University of Melbourne logo must be downloaded from the official design system:

**Official Source**: <https://designsystem.web.unimelb.edu.au/components/logo-listing/>

## Important Notes

1. **Copyright**: The University of Melbourne logo is trademarked and should only be used by authorized individuals
2. **Usage Guidelines**: Per thesis guidelines section 3.6, the University logo should NOT be used in thesis content, only on the title page
3. **Format**: SVG format is preferred for scalability and quality
4. **Compliance**: Ensure you have appropriate authorization to use the University logo

## For Template Testing

If you're testing the template and don't have access to the official logo:

1. The template will attempt to load `../assets/logos/unimelb-logo-official.svg`
2. You can provide a custom logo by passing the `custom` parameter to the `unimelb-logo()` function
3. For development/testing purposes, you can create a simple placeholder SVG file

## Creating a Placeholder Logo (for testing only)

If you need a placeholder for testing, create a simple SVG file named `unimelb-logo-official.svg`:

```xml
<svg width="200" height="80" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="80" fill="#000F46"/>
  <text x="100" y="45" text-anchor="middle" fill="white" font-size="14" font-family="Arial">
    University of Melbourne
  </text>
</svg>
```

**Note**: This placeholder is for development/testing only and should not be used in official thesis submissions.
