#import "layouts/document.typ": main-matter-layout

main-matter-layout(title: "My Title", double-sided: false)[
  p("First page: no header should appear here")
  pagebreak()
  p("Second page: header should show My Title and a page number")
]
