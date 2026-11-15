#import "../utils/style.typ": *
#import "../pages/preface-helpers.typ": (
  ai-usage-note, assistance-section, contribution-table,
  creative-output-section, preface-publications_section, prior-work-section,
)

#let preface-page(ctx, metadata) = {
  let style = ctx.style
  let locale = ctx.locale
  let contributions = metadata.at("preface_contributions", default: ())
  let sections = metadata.at("preface_sections", default: ())
  let publications = metadata.at("publications", default: ())
  let content = metadata.at("preface", default: none)

  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i",
  )

  heading("Preface", numbering: none, outlined: true)
  v(1em)

  if contributions.len() > 0 {
    heading(level: 2, "Contributions")
    v(0.5em)
    contribution-table(contributions)
    v(1em)
  }

  if content != none {
    set par(justify: true, first-line-indent: 1.5em)
    set text(size: 12pt, font: style.fonts.serif, lang: locale)
    content
    v(1em)
  }

  for section in sections {
    let sec-title = if type(section) == dictionary {
      section.at("title", default: "")
    } else { section.at(0, default: "") }
    let sec-content = if type(section) == dictionary {
      section.at("content", default: [])
    } else { section.at(1, default: []) }
    heading(level: 2, sec-title)
    v(0.5em)
    sec-content
    v(1em)
  }

  preface-publications_section(publications)

  assistance-section(metadata.at("assistance", default: ()))
  prior-work-section(metadata.at("prior_work", default: ()))
  creative-output-section(metadata.at("creative_outputs", default: ()))

  // Catch direct legacy callers too; never render private prompt logs.
  if "ai_assistance" in metadata {
    ai-usage-note(metadata.ai_assistance)
  }

  pagebreak()
}
