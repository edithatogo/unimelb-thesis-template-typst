#import "/config/publications.typ": (
  publication-appendix-link, publication-status-table,
)

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#show raw: set text(font: "Libertinus Serif")
#let case = sys.inputs.at("case", default: "plain")
#assert(("plain", "label").contains(case))
#let entry = (
  citation: "CitationGamma (2024)",
  status: "published",
  consent: true,
  appendix: if case == "plain" { "Appendix A" } else { "#cor01-appendix" },
)

COR01 appendix-links #case

#publication-status-table((entry,), show_links: true)

#if case == "label" [
  Direct native reference: #publication-appendix-link(
    (citation: "Synthetic native display", status: "published", appendix: "Appendix A"),
    anchor: <cor01-appendix>,
  )
]

Synthetic appendix destination. <cor01-appendix>

#pagebreak()
Raw code control

#raw("v.at(\"citation\", default: \"\")", block: true)
