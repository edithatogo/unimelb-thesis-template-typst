#import "/lib.typ": thesis-bibliography
#set text(font: "Libertinus Serif", size: 12pt)
COR03 CITATION #cite(<cor03-reference>)
#thesis-bibliography(
  (bibliography_style: sys.inputs.at("cor03-style", default: "apa")),
  "/tests/rendered/cor03/resolved.bib",
)
