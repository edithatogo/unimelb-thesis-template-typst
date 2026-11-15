#import "/config/publications.typ": (
  publication-chapter-footnote, publication-footnote,
)

#set page(paper: "a4", margin: 20mm)
#set text(font: "Libertinus Serif", size: 11pt)
#show raw: set text(font: "Libertinus Serif")
#let case = sys.inputs.at("case", default: "empty")
#assert(("empty", "one", "multiple").contains(case))
#let entries = (
  (
    citation: "CitationAlpha (2026)",
    status: "published",
    consent: true,
    appendix: "Appendix A",
  ),
  (citation: "CitationBeta (2025)", status: "accepted", consent: false),
)
#let selected = if case == "empty" { () } else if case == "one" {
  entries.slice(0, 1)
} else { entries }

COR01 footnotes #case

#for (index, entry) in selected.enumerate() [
  Direct note #index.#publication-footnote(entry)

]
#if selected.len() > 0 [
  Chapter note by numeric key.#publication-chapter-footnote(selected, 0)

  Chapter note by citation key.#publication-chapter-footnote(selected, "CitationAlpha (2026)")
]

#pagebreak()
Raw code control

#raw("v.at(\"citation\", default: \"\")", block: true)
