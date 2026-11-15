// Synthetic replay specimen; no private thesis data.
#import "../../lib.typ": thesis-image

#let configuration = json("configuration.json")
#assert(configuration.seed == 7)
#set document(
  title: configuration.title,
  author: "Synthetic Replay Author",
  date: datetime(year: 2026, month: 11, day: 15),
)
#set page(paper: "a4", margin: 2cm)
#set text(
  font: "Source Serif Pro",
  fallback: false,
  size: 11pt,
  lang: "en",
  region: "AU",
)

= Bounded replay specimen

REPLAY BODY SENTINEL. Fixed synthetic seed: #configuration.seed.
*REPLAY BOLD SENTINEL.* _REPLAY ITALIC SENTINEL._

#figure(
  thesis-image(
    path("icon.svg"),
    width: 24mm,
    alt: "Synthetic blue square with a white circle.",
  ),
  caption: [REPLAY IMAGE SENTINEL],
)

A synthetic reference exercises caller-owned bibliography and style inputs @replay.

#bibliography(
  path("references.bib"),
  style: path("synthetic.csl"),
  title: "Replay references",
)
