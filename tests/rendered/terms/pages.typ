#import "../../../pages/glossary.typ": abbreviations-page
#import "../../../endmatter/optional-glossary.typ": (
  optional-glossary-abbreviations-page,
)
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif")
#if sys.inputs.at("case", default: "abbreviations") == "abbreviations" {
  abbreviations-page()
} else {
  optional-glossary-abbreviations-page(
    separate-pages: false,
    show-validation: false,
    show-statistics: false,
  )
}
