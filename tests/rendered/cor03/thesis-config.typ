#import "/lib.typ": thesis
#let case = sys.inputs.at("cor03-case", default: "control")
#let bibliography-raw = "/tests/rendered/cor03/raw.bib"
#let bibliography-resolved = "/tests/rendered/cor03/resolved.bib"
#let options = (
  title: "Synthetic Configuration Study",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  show_logo: false,
  font_theme: "classic",
  include_bibliography: false,
)
#if case == "cli-logo" {
  let _ = options.remove("show_logo")
} else if case == "cli-font" {
  let _ = options.remove("font_theme")
} else if case == "double-true" {
  options.insert("double_sided", true)
} else if case == "double-false" {
  options.insert("double_sided", false)
} else if case == "double-string" {
  options.insert("double_sided", "false")
} else if case == "bib-disable" {
  options.insert("include_bibliography", true)
  options.insert(
    "bibliography_path",
    "/tests/rendered/cor03/SHOULD-NOT-BE-OPENED.bib",
  )
  options.insert("metadata_overrides", (include_bibliography: false))
} else if case == "bib-enable" {
  options.insert("metadata_overrides", (
    include_bibliography: true,
    bibliography_path: bibliography-resolved,
    bibliography_style: "ieee",
  ))
} else if case == "bib-path" {
  options.insert("include_bibliography", true)
  options.insert("bibliography_path", bibliography-raw)
  options.insert("metadata_overrides", (
    bibliography_path: bibliography-resolved,
  ))
} else if case == "bib-style" {
  options.insert("include_bibliography", true)
  options.insert("bibliography_path", bibliography-resolved)
  options.insert("bibliography_style", "apa")
  options.insert("metadata_overrides", (bibliography_style: "ieee"))
} else if case == "custom-declaration" {
  options.insert("declaration", [COR03 CUSTOM DECLARATION SENTINEL])
} else if case == "unknown-override" {
  options.insert("metadata_overrides", (include_bibliogaphy: false))
}
#show: thesis.with(..options)

= COR03 CHAPTER ONE
COR03 FIRST CHAPTER BODY

#if (
  case in ("bib-enable", "bib-path", "bib-style")
) [COR03 CITATION #cite(<cor03-reference>)]

= COR03 CHAPTER TWO
COR03 SECOND CHAPTER BODY
