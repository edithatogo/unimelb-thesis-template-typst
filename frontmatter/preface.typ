#import "../utils/style.typ": *
#import "../config/index.typ": config

#let preface-page(ctx, metadata) = {
  let style = ctx.style
  let locale = ctx.locale
  let contributions = metadata.at("preface_contributions", default: ())
  let sections = metadata.at("preface_sections", default: ())
  let publications = metadata.at("publications", default: ())
  let content = metadata.preface

  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  heading("Preface", numbering: none, outlined: false)
  v(1em)

  if contributions.len() > 0 {
    config.contributions.matrix(contributions, template: "detailed")
    v(1em)
  }

  if content != none {
    set par(justify: true, first-line-indent: 1.5em)
    set text(size: 12pt, font: style.fonts.serif, lang: locale)
    content
    v(1em)
  }

  for section in sections {
    let title = section.at("title", default: "") if type(section) == dictionary else section.at(0, default: "")
    let section-content = section.at("content", default: []) if type(section) == dictionary else section.at(1, default: [])
    heading(level: 2, title)
    v(0.5em)
    section-content
    v(1em)
  }

  if publications.len() > 0 {
    heading(level: 2, "Publication Register")
    v(0.5em)
    config.publications.publication-status-table(publications)
    v(1em)
  }

  pagebreak()
}
