#import "/pages/preface-helpers.typ": contribution-table

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#show raw: set text(font: "Libertinus Serif")
#let case = sys.inputs.at("case", default: "empty")
#assert(("empty", "one", "multiple").contains(case))
#let entries = (
  (name: "ContribAlpha", role: "Analysis", percentage: 60),
  ("ContribBeta", "Validation", 40),
)
#let selected = if case == "empty" { () } else if case == "one" {
  entries.slice(0, 1)
} else { entries }

COR01 contributions #case

#contribution-table(selected)

#pagebreak()
Raw code control

#raw("v.at(\"citation\", default: \"\")", block: true)
