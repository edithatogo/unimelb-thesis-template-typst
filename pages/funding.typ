#import "../config/optional.typ": validate-records

// A public acknowledgement of supplied funding records, not an RTP or award
// compliance certificate. Keep the author's wording and order explicit.
#let funding-page(ctx, entries) = {
  validate-records("funding", entries)
  if entries.len() > 0 {
    heading("Funding", numbering: none, outlined: true)
    v(1em)
    for entry in entries {
      par[
        #strong(entry.funder)
        #if "grant" in entry [ — Grant: #entry.grant]
      ]
      if entry.at("acknowledgement", default: "") != "" {
        par(entry.acknowledgement)
      }
      v(0.5em)
    }
    pagebreak()
  }
}
