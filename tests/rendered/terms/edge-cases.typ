#import "../../../config/glossary.typ": generate-glossary-page, glossary-term
#import "../../../config/index.typ": (
  auto-extract-index, generate-index, generate-index-page, index-term,
)
#import "../../../endmatter/optional-index.typ": optional-index-page
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif")
#let test = sys.inputs.at("case", default: "roman")
#if test == "roman" {
  set page(numbering: "i")
  [ROMAN FIRST #glossary-term("Roman Sentinel", "ROMAN SYNTHETIC DEFINITION.") #index-term("Roman Index")]
  pagebreak()
  set page(numbering: "1")
  counter(page).update(1)
  [ARABIC FIRST #glossary-term("Roman Sentinel", "ROMAN SYNTHETIC DEFINITION.") #index-term("Roman Index")]
  pagebreak()
  generate-glossary-page(
    include-abbreviations: false,
    include-manual-glossary: false,
    include-categories: false,
  )
  pagebreak()
  generate-index-page(columns: 1, include-statistics: false)
} else if test == "empty-index" {
  generate-index-page()
} else if test == "category" {
  [CATEGORY FIRST #index-term("Zeta Term", category: "Alpha Category") #index-term("Alpha Term")]
  context {
    let values = generate-index(sort-by: "category")
    [CATEGORY ORDER: #values.keys().join(" then ")]
  }
} else if test == "hidden-pages" {
  optional-index-page(
    custom-entries: ("Hidden References": "22, 44-46"),
    show-page-numbers: false,
  )
} else if test == "zero-page" {
  optional-index-page(custom-entries: ("Invalid Reference": "0"))
} else if test == "reversed-range" {
  optional-index-page(custom-entries: ("Invalid Reference": "6-4"))
} else if test == "invalid-page" {
  optional-index-page(custom-entries: ("Invalid Reference": "tomorrow"))
} else if test == "empty-term" {
  index-term("")
} else if test == "automatic-index" {
  auto-extract-index("Synthetic Quantum Concept has a supplied phrase.")
} else if test == "conflicting-definition" {
  glossary-term("Conflict Sentinel", "FIRST SYNTHETIC DEFINITION.")
  glossary-term("Conflict Sentinel", "SECOND SYNTHETIC DEFINITION.")
  generate-glossary-page(
    include-abbreviations: false,
    include-manual-glossary: false,
  )
}
