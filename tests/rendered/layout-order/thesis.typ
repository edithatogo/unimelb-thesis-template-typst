#import "/lib.typ": thesis
#let case = sys.inputs.at("layout-case", default: "control")
#let boundaries(prefix) = block(width: 100%)[
  #set par(first-line-indent: 0pt)
  #align(left)[#prefix LEFT BOUNDARY]
  #align(right)[#prefix RIGHT BOUNDARY]
]
#let options = (
  title: "Synthetic Layout Order Study",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [LAYOUT ABSTRACT SENTINEL],
  preface: [LAYOUT PREFACE SENTINEL],
  acknowledgements: [LAYOUT ACKNOWLEDGEMENTS SENTINEL],
  font_theme: "classic",
  show_logo: false,
  include_bibliography: case != "no-bibliography",
  bibliography_path: "/tests/rendered/layout-order/references.bib",
  bibliography_style: "ieee",
  appendices: (
    (
      title: "LAYOUT APPENDIX",
      content: [
        LAYOUT APPENDIX BODY

        #boundaries("APPENDIX")

        == LAYOUT APPENDIX SECTION
        LAYOUT APPENDIX SECTION BODY
      ],
    ),
  ),
)
#if case == "double-true" {
  options.insert("double_sided", true)
} else if case == "double-false" {
  options.insert("double_sided", false)
}
#show: thesis.with(..options)

= LAYOUT CHAPTER ALPHA
LAYOUT FIRST CHAPTER BODY

#boundaries("CORE")

#if case != "no-bibliography" [LAYOUT CITATION #cite(<layout-reference>)]

= LAYOUT CHAPTER BETA
LAYOUT SECOND CHAPTER BODY
