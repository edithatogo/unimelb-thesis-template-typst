#import "../utils/style.typ": *
#import "../config/abbreviations.typ": abbreviations, validate-abbreviations-detailed, print-validation-report, get-sorted-abbreviations, get-abbreviation-stats, abbreviations-with-categories, get-abbrevs-by-category, create-abbrev-groups
#import "../config/glossary.typ": glossary-entries, validate-glossary, get-sorted-glossary, get-glossary-categories, get-glossary-stats, get-glossary-by-category

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

  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Glossary of Terms and Abbreviations
    ]
  ]

  v(1cm)

  // Validate both systems
  let abbrev-validation = validate-abbreviations-detailed()
  let glossary-validation = validate-glossary()

  let has-errors = abbrev-validation.errors.len() > 0 or glossary-validation.errors.len() > 0

  if has-errors {
    text(fill: red, weight: "bold")[Validation failed. Please fix the following errors:\n]

    if abbrev-validation.errors.len() > 0 {
      text(fill: red)[*Abbreviation Errors:* \n]
      for error in abbrev-validation.errors {
        [- #error\n]
      }
    }

    if glossary-validation.errors.len() > 0 {
      text(fill: red)[*Glossary Errors:* \n]
      for error in glossary-validation.errors {
        [- #error\n]
      }
    }
    return
  }

  // Show warnings if any
  if abbrev-validation.warnings.len() > 0 or glossary-validation.warnings.len() > 0 {
    text(fill: orange, weight: "bold")[Warnings:\n]
    for warning in abbrev-validation.warnings + glossary-validation.warnings {
      [- #warning\n]
    }
    v(0.5cm)
  }

  // Get combined statistics
  import "../config/glossary.typ": get-combined-stats
  let combined-stats = get-combined-stats()

  // Abbreviations section
  if abbreviations.len() > 0 {
    text(size: 14pt, weight: "bold", fill: colors.secondary)[Abbreviations\n]
    v(0.5cm)

    // Group abbreviations by category
    let abbrev-groups = create-abbrev-groups()

    for category in abbrev-groups.keys().sorted() {
      let group-abbrevs = abbrev-groups.at(category)
      if group-abbrevs.len() > 0 {
        text(size: 12pt, weight: "bold")[#category\n]
        v(0.3cm)

        for entry in group-abbrevs.sorted(key: e => e.short) {
          block[
            *#entry.short* — #entry.key: #entry.long
          ]
          v(0.3em)
        }
        v(0.5cm)
      }
    }
  }

  // Glossary section
  if glossary-entries.len() > 0 {
    pagebreak()
    align(center)[
      #text(size: 14pt, weight: "bold", fill: colors.secondary)[
        Glossary of Terms
      ]
    ]
    v(0.5cm)

    // Group glossary by category
    let categories = get-glossary-categories().sorted()

    for category in categories {
      let category-entries = get-glossary-by-category(category)
      if category-entries.len() > 0 {
        text(size: 12pt, weight: "bold")[#category\n]
        v(0.3cm)

        for entry in category-entries.sorted(key: e => e.term) {
          block[
            [#label("glossary-" + entry.term)]
            *#entry.term*: #entry.definition
          ]

          // Show related terms if any
          if "related" in entry and entry.related.len() > 0 {
            text(size: 9pt, fill: gray)[
              Related: #entry.related.join(", ")
            ]
          }

          v(0.5em)
        }
        v(0.8cm)
      }
    }
  }

  // Statistics and summary
  if abbreviations.len() > 0 or glossary-entries.len() > 0 {
    v(1cm)
    text(size: 10pt, fill: gray)[
      *Summary Statistics:*\n
      Abbreviations: #combined-stats.abbreviations.total total (#combined-stats.abbreviations.avg-abbrev-length avg length)\n
      Glossary terms: #combined-stats.glossary.total total (#combined-stats.glossary.avg-term-length avg term length, #combined-stats.glossary.categories categories)\n
      Total terms: #combined-stats.total-terms
    ]
  }
}