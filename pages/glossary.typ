#import "../utils/style.typ": *
#import "../config/abbreviations.typ": abbreviations, validate-abbreviations-detailed, print-validation-report, get-sorted-abbreviations, get-abbreviation-stats, abbreviations-with-categories, get-abbrevs-by-category, create-abbrev-groups
#import "../config/glossary.typ": glossary-entries, validate-glossary, get-sorted-glossary, get-glossary-categories, get-glossary-stats, get-glossary-by-category, generate-glossary-page, generate-full-glossary, get-extracted-glossary, get-combined-stats

#let glossary-page() = {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Glossary of Terms and Abbreviations
    ]
  ]

  v(1cm)

  // Enhanced validation with detailed reporting
  let validation = validate-abbreviations-detailed()
  if validation.errors.len() > 0 {
    text(fill: red, weight: "bold")[Abbreviation validation failed. Please fix the following errors:\n]
    for error in validation.errors {
      [- #error\n]
    }
    return
  }

  if abbreviations.len() == 0 {
    text("No abbreviations defined.")
  } else {
    // Sort alphabetically by key with enhanced sorting
    let sorted-abbrevs = get-sorted-abbreviations(sort-by: "key")

    for entry in sorted-abbrevs {
      block[
        *#entry.key* (#entry.short): #entry.long
      ]
      v(0.5em)
    }

    // Show statistics
    v(1cm)
    let stats = get-abbreviation-stats()
    text(size: 10pt, fill: gray)[
      *Statistics:* #stats.total total abbreviations, average key length: #stats.avg-key-length, average abbreviation length: #stats.avg-abbrev-length
    ]
  }
}

#let abbreviations-page() = {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      List of Abbreviations
    ]
  ]

  v(1cm)

  // Enhanced validation with detailed reporting
  let validation = validate-abbreviations-detailed()
  if validation.errors.len() > 0 {
    text(fill: red, weight: "bold")[Abbreviation validation failed. Please fix the following errors:\n]
    for error in validation.errors {
      [- #error\n]
    }
    return
  }

  if abbreviations.len() == 0 {
    text("No abbreviations defined.")
  } else {
    // Sort alphabetically by abbreviation
    let sorted-abbrevs = get-sorted-abbreviations(sort-by: "short")

    table(
      columns: (auto, auto, 1fr),
      column-gutter: 1em,
      [*Abbreviation*, *Term*, *Definition*],
      ..sorted-abbrevs.map(entry => [
        entry.short,
        entry.key,
        entry.long
      ])
    )

    // Show statistics
    v(1cm)
    let stats = get-abbreviation-stats()
    text(size: 10pt, fill: gray)[
      *Statistics:* #stats.total total abbreviations, average abbreviation length: #stats.avg-abbrev-length
    ]
  }
}

#let comprehensive-glossary-page() = {
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  // Use the automated glossary generation system
  generate-glossary-page(
    title: "Glossary of Terms and Abbreviations",
    include-abbreviations: true,
    include-manual-glossary: true,
    include-extracted-terms: true,
    show-statistics: true,
    show-validation: true
  )
}