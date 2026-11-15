// Candidate canonical configuration renderer. The Python adapter validates and
// pins the complete input before calling this low-level rendering function.
// This bounded path does not certify institutional declaration/title policy.
#import "../../../utils/style.typ": make-thesis-style
#import "../../../utils/locales.typ": locale-labels
#import "../../../layouts/document.typ": front-matter-layout, main-matter-layout
#import "../../../pages/abstract.typ": abstract-page
#import "../../../pages/front-matter.typ": toc-page

#let draft-value(value, description) = {
  if value == none or value == "" {
    "[Draft " + description + " not supplied]"
  } else { value }
}

#let contract-document(configuration, body) = {
  assert(
    configuration.contract_version == "1.0.0",
    message: "Unsupported contract version.",
  )
  assert(
    configuration.identity == "identified",
    message: "Blind projection is unsupported by this adapter slice.",
  )
  assert(
    configuration.purpose in ("draft", "examination"),
    message: "Deposit projection is unsupported by this adapter slice.",
  )
  assert(
    configuration.output == "pdf" and configuration.pdf_standards.len() == 0,
    message: "Requested output is unsupported by this adapter slice.",
  )
  assert(
    configuration.language == "en" and configuration.label_locale == "en",
    message: "Requested language is unsupported by this adapter slice.",
  )
  assert(
    type(configuration.double_sided) == bool,
    message: "Expected a typed duplex setting.",
  )

  let metadata = configuration.metadata
  let author = metadata.at("author", default: (:))
  let degree = metadata.at("degree", default: (:))
  let submission = metadata.at("submission", default: (:))
  let declarations = metadata.at("declarations", default: (:))
  let title = draft-value(metadata.at("title", default: none), "title")
  let name = draft-value(
    author.at("student_record_name", default: none),
    "author",
  )
  let course = draft-value(degree.at("course", default: none), "course")
  let month = draft-value(
    submission.at("month", default: none),
    "submission month",
  )
  let units = metadata.at("academic_units", default: ())
  let labels = locale-labels(locale: configuration.label_locale)
  let style = make-thesis-style(
    font_theme: "classic",
    profile: configuration.layout,
  )
  let ctx = (
    style: style,
    labels: labels,
    locale: configuration.language,
    profile: configuration.layout,
  )

  set document(title: title, author: name, keywords: ())
  front-matter-layout(ctx)[
    #align(center)[
      #text(size: 20pt, weight: "bold", title)
      #v(2em)
      #text(size: 16pt, name)
      #if author.at("orcid", default: none) != none {
        par("ORCID: " + author.orcid)
      }
      #v(2em)
      #par(course)
      #if units.len() == 0 {
        par("[Draft academic unit not supplied]")
      } else {
        for unit in units { par(unit) }
      }
      #v(2em)
      // Preserve the contract's month precision; no day is inferred.
      #par("Submission month: " + month)
    ]
    #pagebreak()
    #let abstract = metadata.at("abstract", default: "")
    #if abstract != "" { abstract-page(ctx, abstract) }
    #heading(labels.declaration, numbering: none, outlined: true)
    #if declarations.at("original_work", default: none) == true {
      par("The author declares that the thesis contains their original work.")
    } else {
      par("Original work declaration not supplied.")
    }
    #if declarations.at("word_count", default: none) != none {
      par("Word count: " + str(declarations.word_count) + ".")
    } else {
      par("Word count not supplied.")
    }
    #pagebreak()
    #toc-page(ctx)
    #if configuration.double_sided { pagebreak(weak: true, to: "odd") }
  ]
  main-matter-layout(
    ctx,
    title: title,
    double-sided: configuration.double_sided,
  )[
    #body
  ]
}
