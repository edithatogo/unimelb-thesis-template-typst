// Minimal reproduction: import document layout and produce multi-page content
#import "layouts/document.typ": *

// Use the main-matter layout with a title so the header code runs
main-matter-layout(title: "The Secret Life of Quantum Penguins: A Computational Analysis", double-sided: false)[
  = Introduction

  // Produce enough filler to create multiple pages so the header appears
  // Increase lorem to guarantee at least two pages in most page sizes
  #lorem(2000)
]
