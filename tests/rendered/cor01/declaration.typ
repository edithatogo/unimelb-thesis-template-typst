#import "/pages/declaration.typ": declaration-page

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#show raw: set text(font: "Libertinus Serif")
#let case = sys.inputs.at("case", default: "empty")
#assert(("empty", "one", "multiple").contains(case))

COR01 declaration #case

#declaration-page(
  (labels: (declaration: "Declaration", submission_date_label: "Probe date")),
  candidate_name: "Synthetic Candidate",
  thesis_title: "Synthetic declaration probe",
  degree: "Doctor of Philosophy",
  word_count: if case == "empty" { none } else { 12345 },
  ai_usage: if case == "multiple" { "Synthetic AI disclosure alpha." } else {
    none
  },
  third_party_assistance: if case == "multiple" {
    "Synthetic human disclosure beta."
  } else { none },
)

Raw code control

#raw("v.at(\"citation\", default: \"\")", block: true)
