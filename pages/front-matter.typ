#import "../utils/style.typ": *

#let toc-page(ctx) = {
  let style = ctx.style
  let labels = ctx.labels
  let locale = ctx.locale
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  align(center)[
    #text(size: 16pt, weight: "bold")[#labels.table_of_contents]
  ]

  v(2em)

  set text(size: 11pt, font: style.fonts.sans, lang: locale)
  outline(depth: 3, indent: 1em)

  pagebreak()
}

#let lof-page(ctx) = {
  let style = ctx.style
  let labels = ctx.labels
  let locale = ctx.locale
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  align(center)[
    #text(size: 16pt, weight: "bold")[#labels.list_of_figures]
  ]

  v(2em)

  set text(size: 11pt, font: style.fonts.sans, lang: locale)
  outline(
    title: none,
    target: figure.where(kind: image),
  )

  pagebreak()
}

#let lot-page(ctx) = {
  let style = ctx.style
  let labels = ctx.labels
  let locale = ctx.locale
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  align(center)[
    #text(size: 16pt, weight: "bold")[#labels.list_of_tables]
  ]

  v(2em)

  set text(size: 11pt, font: style.fonts.sans, lang: locale)
  outline(
    title: none,
    target: figure.where(kind: table),
  )

  pagebreak()
}

#let loa-page(ctx) = {
  let style = ctx.style
  let labels = ctx.labels
  let locale = ctx.locale
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  align(center)[
    #text(size: 16pt, weight: "bold")[#labels.list_of_algorithms]
  ]

  v(2em)

  set text(size: 11pt, font: style.fonts.sans, lang: locale)
  outline(
    title: none,
    target: figure.where(kind: "algorithm"),
  )

  pagebreak()
}

#let third-party-page(ctx, items) = {
  if items.len() > 0 {
    let style = ctx.style
    let labels = ctx.labels

    set page(
      margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
      numbering: "i"
    )

    heading("Third-Party Copyright Register", numbering: none, outlined: false)
    v(1em)

    table(
      columns: 3,
      column-gutter: 1em,
      stroke: 0.5pt,
      [*Material*], [*Source*], [*Permission Status*],
      ..items.map(item => (
        item.at("material", default: ""),
        item.at("source", default: ""),
        item.at("permission", default: "")
      ))
    )

    pagebreak()
  }
}
