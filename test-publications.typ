#import "config/publications.typ": *

// Minimal test document to exercise publication macros
set page(margin: 2cm)

let sample = (
  (
    citation: "Doe, J. (2025). A study of things.",
    status: "published",
    consent: true,
    appendix: "Appendix A"
  ),
  (
    citation: "Smith, A. (2024). Another study.",
    status: "in revision",
    consent: false,
    appendix: "app-b"
  )
)

heading("Publication macros test")

p("Footnote demo:") publication-chapter-footnote(sample, 0)

v(0.5em)

heading(level: 2, "Status table")
publication-status-table(sample, show_links: true)


// Also render a manual appendix link using the anchor parameter
v(1em)
heading(level: 2, "Appendix link demo")
let entry = sample.at(1)
paragraph { publication-appendix-link(entry, anchor: "app-b") }
