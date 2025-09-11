#import "../utils/style.typ": *

// =================================
// Table of Contents Page
// =================================

#let toc-page() = {
  // Page setup
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  // Heading
  align(center)[
    #text(size: 16pt, weight: "bold")[Table of Contents]
  ]

  v(2em)

  // Table of contents
  set text(size: 11pt, font: "Source Sans Pro")
  outline(depth: 3, indent: 1em)

  pagebreak()
}

// =================================
// List of Figures Page
// =================================

#let lof-page() = {
  // Page setup
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  // Heading
  align(center)[
    #text(size: 16pt, weight: "bold")[List of Figures]
  ]

  v(2em)

  // List of figures
  set text(size: 11pt, font: "Source Sans Pro")
  outline(
    title: none,
    target: figure.where(kind: image),
  )

  pagebreak()
}

// =================================
// List of Tables Page
// =================================

#let lot-page() = {
  // Page setup
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  // Heading
  align(center)[
    #text(size: 16pt, weight: "bold")[List of Tables]
  ]

  v(2em)

  // List of tables
  set text(size: 11pt, font: "Source Sans Pro")
  outline(
    title: none,
    target: figure.where(kind: table),
  )

  pagebreak()
}

// =================================
// List of Algorithms Page
// =================================

#let loa-page() = {
  // Page setup
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    numbering: "i"
  )

  // Heading
  align(center)[
    #text(size: 16pt, weight: "bold")[List of Algorithms]
  ]

  v(2em)

  // List of algorithms
  set text(size: 11pt, font: "Source Sans Pro")
  outline(
    title: none,
    target: figure.where(kind: "algorithm"),
  )

  pagebreak()
}
