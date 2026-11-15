// Synthetic Apache-2.0 fixture: index entries are authored, not anonymized.
#import "/lib.typ": thesis

#let identity = sys.inputs.at("cor04-identity", default: "identified")
#assert(identity in ("identified", "blind"))

#show: thesis.with(
  title: "COR04 authored index surface",
  author: "COR04AUTOFIELDNAME",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [COR04 SAFE ABSTRACT BODY.],
  blind: identity == "blind",
  show_logo: false,
  font_theme: "classic",
  include_bibliography: false,
  include_index: true,
  index_entries: ("COR04INDEXAUTHOR": "2, 4-6"),
)

= COR04 SAFE CHAPTER

COR04 SAFE INDEX BODY.
