#import "../../../config/index.typ": generate-index-page, index-term
#import "../../../endmatter/optional-index.typ": (
  index, optional-index-page, optional-index-with-subentries,
)
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif")
#let test = sys.inputs.at("case", default: "marked")
#if test == "marked" or test == "columns" {
  [INDEX FIRST PAGE #index-term("Synthetic Alpha") #index-term("Synthetic Alpha")]
  pagebreak()
  [INDEX SECOND PAGE #index-term("Synthetic Alpha") #index-term("Synthetic Beta", subterm: "detail")]
  pagebreak()
  generate-index-page(
    columns: if test == "columns" { 2 } else { 1 },
    include-statistics: false,
  )
} else if test == "manual" {
  optional-index-page(
    custom-entries: ("Synthetic Alpha": "2, 4-6", "Synthetic Beta": "3"),
    columns: 1,
  )
} else if test == "subentries" {
  optional-index-with-subentries(
    entries: ("Synthetic Alpha": ("Detail One": "2, 4-6", "Detail Two": "3")),
    columns: 1,
  )
} else if test == "alias" {
  [INDEX ALIAS FIRST #index("Synthetic Alias")]
  pagebreak()
  generate-index-page(columns: 1, include-statistics: false)
}
