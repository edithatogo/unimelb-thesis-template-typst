#import "/lib.typ": thesis
#let kind = sys.inputs.at("cor03-path", default: "native")
#let resource = if kind == "collection" {
  (path("resolved.bib"), "/tests/rendered/cor03/second.bib")
} else if kind == "override" {
  "/tests/rendered/cor03/raw.bib"
} else {
  path("resolved.bib")
}
#show: thesis.with(
  title: "Synthetic Native Resource Study",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  show_logo: false,
  font_theme: "classic",
  include_bibliography: true,
  bibliography_path: resource,
  metadata_overrides: if kind == "override" {
    (bibliography_path: path("resolved.bib"))
  } else { (:) },
)

= COR03 NATIVE RESOURCE CHAPTER
COR03 NATIVE RESOURCE BODY #cite(<cor03-reference>)
#if kind == "collection" [COR03 SECOND RESOURCE #cite(<cor03-second>)]
