#import "/pages/appendix.typ": appendix-page
#import "/utils/style.typ": make-thesis-style
#let ctx = (
  style: make-thesis-style(font_theme: "classic"),
  locale: "en",
  profile: "default",
)
#set page(paper: "a4", margin: 20mm, numbering: "1")
#set text(font: "Libertinus Serif", size: 11pt)
#counter(page).update(7)
NAV ARABIC PAGE CONTROL
#pagebreak()
#appendix-page(ctx, (
  appendices: (
    (
      title: "NAV APPENDIX ALPHA",
      content: [NAV APPENDIX ALPHA BODY #pagebreak()],
    ),
    (title: "NAV APPENDIX BETA", content: [NAV APPENDIX BETA BODY]),
  ),
))
