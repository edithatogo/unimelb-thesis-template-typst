// Synthetic-only experimental multi-document Typst 0.15.1+ HTML/bundle probe.
// No personal, clinical, copyright-restricted or submission material.
#document("index.html", title: [Synthetic thesis overview])[
  #set text(lang: "en")
  = Synthetic Research Thesis
  This public demonstration is not a complete or approved thesis.
  See #link(<methods>)[methods].
] <home>
#document("chapters/methods.html", title: [Synthetic methods])[
  #set text(lang: "en")
  = Methods
  == Synthetic measurement
  A minimal purely illustrative equation: $x = 1$.
  Return to #link(<home>)[overview].
] <methods>
