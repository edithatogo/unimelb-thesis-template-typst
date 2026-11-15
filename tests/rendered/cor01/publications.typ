#import "/config/publications.typ": publication-status-table

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#show raw: set text(font: "Libertinus Serif")
#let case = sys.inputs.at("case", default: "empty")
#assert(("empty", "one", "multiple").contains(case))
#let entries = (
  (citation: "CitationAlpha (2026)", status: "published", consent: true),
  (citation: "CitationBeta (2025)", status: "accepted", consent: false),
)
#let selected = if case == "empty" { () } else if case == "one" {
  entries.slice(0, 1)
} else { entries }

COR01 publications #case

#publication-status-table(selected)

#pagebreak()
Raw code control

#raw("v.at(\"citation\", default: \"\")", block: true)
