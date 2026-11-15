#import "/pages/title.typ": title-page
#import "/utils/style.typ": make-thesis-style
#import "/utils/locales.typ": locale-labels
#let requested = sys.inputs.at("cor03-logo", default: "omitted")
#let ctx = (
  style: make-thesis-style(font_theme: "classic"),
  labels: locale-labels(),
  locale: "en",
)
#if requested != "omitted" {
  ctx.insert("show_logo", if requested == "true" { true } else if requested
    == "false" { false } else { requested })
}
#title-page(
  ctx,
  title: "COR03 DIRECT TITLE SENTINEL",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
)
