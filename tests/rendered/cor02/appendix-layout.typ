#import "/layouts/document.typ": appendix-layout
#import "/utils/style.typ": make-thesis-style
#let ctx = (
  style: make-thesis-style(font_theme: "classic"),
  locale: "en",
  profile: "default",
)
#appendix-layout(ctx)[
  = NAV DIRECT APPENDIX
  NAV DIRECT APPENDIX BODY

  == NAV DIRECT APPENDIX SECTION
  NAV DIRECT SECTION BODY
]
