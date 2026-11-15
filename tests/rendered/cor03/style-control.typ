#import "/utils/style.typ": make-thesis-style
#let style = make-thesis-style(font_theme: "classic", profile: "print")
#set text(font: "Libertinus Serif", size: 12pt)
#text(fill: style.colors.primary)[COR03 DIRECT PRINT COLOR]
#repr(style.colors.primary.space())
