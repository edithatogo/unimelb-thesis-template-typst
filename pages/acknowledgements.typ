// =================================
// Acknowledgements Page
// =================================

#let acknowledgements-page(ctx, acknowledgements) = {
  let labels = ctx.labels
  heading(labels.acknowledgements, numbering: none, outlined: false)
  v(1em)
  acknowledgements
  pagebreak()
}
