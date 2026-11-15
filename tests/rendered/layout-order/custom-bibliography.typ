#import "/lib.typ": thesis-bibliography
#set page(paper: "a4", margin: 3cm)
#set text(font: "Libertinus Serif")
LAYOUT STANDALONE CITATION #cite(<layout-reference>)
#thesis-bibliography(
  (bibliography_style: "ieee"),
  "/tests/rendered/layout-order/references.bib",
  title: "LAYOUT CUSTOM REFERENCES",
)
