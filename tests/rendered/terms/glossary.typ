#import "../../../config/glossary.typ": (
  auto-extract-glossary, extract-terms-from-content, generate-glossary-index,
  generate-glossary-page, glossary, glossary-term,
)
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif")
#let test = sys.inputs.at("case", default: "first-use")
#if test == "first-use" {
  [GLOSS FIRST: #glossary("Citation", link: false).]
  parbreak()
  [GLOSS SECOND: #glossary("Citation", link: false).]
  pagebreak()
  [GLOSS THIRD: #glossary("Citation", link: false).]
  pagebreak()
  generate-glossary-page(include-categories: false)
} else if test == "marked" {
  [Marked #glossary-term("Sentinel Concept", "SYNTHETIC DEFINITION ALPHA.") on the first page.]
  parbreak()
  [Repeated #glossary-term("Sentinel Concept", "SYNTHETIC DEFINITION ALPHA.") on the first page.]
  pagebreak()
  [Repeated #glossary-term("Sentinel Concept", "SYNTHETIC DEFINITION ALPHA.") on the second page.]
  pagebreak()
  generate-glossary-page(
    include-categories: false,
    include-abbreviations: false,
    include-manual-glossary: false,
  )
} else if test == "index" {
  generate-glossary-page()
  pagebreak()
  generate-glossary-index()
} else if test == "automatic" {
  auto-extract-glossary([Synthetic Quantum Concept has a supplied phrase.])
  pagebreak()
  generate-glossary-page(
    include-categories: false,
    include-manual-glossary: false,
  )
} else if test == "extract" {
  let observed = extract-terms-from-content(
    [Synthetic Quantum Concept has a supplied phrase.],
  )
  [EXTRACTION RESULT: #repr(observed)]
}
