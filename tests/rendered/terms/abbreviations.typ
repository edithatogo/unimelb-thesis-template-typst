#import "../../../config/abbreviations.typ": abbrev, abbreviation-table
#set page(paper: "a4", margin: 2cm, numbering: "1")
#set text(font: "Libertinus Serif")
#let test = sys.inputs.at("case", default: "table")
#if test == "table" {
  heading("TERM TABLE CONTROL", numbering: none)
  abbreviation-table()
} else {
  [TERM FIRST: #abbrev("ML"). TERM SECOND: #abbrev("ML").]
  parbreak()
  [TERM UNEXPANDED: #abbrev("AI", expand: false). TERM LATER FIRST: #abbrev("AI").]
  pagebreak()
  [TERM THIRD: #abbrev("ML").]
}
