// Minimal Typst file to test header text extraction

set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  header: context {
    let current = counter(page).get().first()
    if current > 1 {
      context[
        block(width: 100%)[
          set text(size: 12pt, weight: "bold", hyphenate: false)
          text()[ "MY MINIMAL TITLE" #h(1fr) #counter(page).display() ]
          line(length: 100%, stroke: 0.5pt)
        ]
      ]
    }
  }
)

p("First page, no header expected.")
pagebreak()
p("Second page, header should say MY MINIMAL TITLE and the page number.")
