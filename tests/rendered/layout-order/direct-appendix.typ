#import "/layouts/document.typ": appendix-layout
#import "/utils/style.typ": make-thesis-style
#set text(font: "Libertinus Serif")
#let ctx = (
  style: make-thesis-style(font_theme: "classic", profile: "screen"),
  locale: "en",
  profile: "screen",
)
#appendix-layout(ctx)[
  = LAYOUT DIRECT APPENDIX
  LAYOUT DIRECT APPENDIX BODY
  #block(width: 100%)[
    #set par(first-line-indent: 0pt)
    #align(left)[APPENDIX LEFT BOUNDARY]
    #align(right)[APPENDIX RIGHT BOUNDARY]
  ]
]
