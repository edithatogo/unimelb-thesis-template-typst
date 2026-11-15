// Synthetic Apache-2.0 fixture. Reviewed replacements are supplied by the
// author of this fixture; the thesis renderer must not rewrite these values.
#import "/lib.typ": thesis
#import "/pages/preface-helpers.typ": contribution-table
#import "/config/publications.typ": publication-footnote

#let identity = sys.inputs.at("cor04-identity", default: "identified")
#let reviewed-input = sys.inputs.at("cor04-reviewed", default: "false")
#let custom-input = sys.inputs.at("cor04-custom-declaration", default: "false")
#assert(identity in ("identified", "blind"))
#assert(reviewed-input in ("true", "false"))
#assert(custom-input in ("true", "false"))
#let reviewed = reviewed-input == "true"
#let custom = custom-input == "true"
#let select(raw, replacement) = if reviewed { replacement } else { raw }

#show: thesis.with(
  title: "COR04 authored identity surfaces",
  author: "COR04AUTOFIELDNAME",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [COR04 SAFE ABSTRACT BODY.],
  keywords: ("synthetic",),
  preface: text(select("COR04AUTHOREDPREFACE", "COR04 SAFE PREFACE BODY")),
  preface_sections: (
    (
      title: select("COR04PREFACEHEADING", "COR04 SAFE PREFACE HEADING"),
      content: text(select(
        "COR04PREFACESECTIONBODY",
        "COR04 SAFE PREFACE SECTION BODY",
      )),
    ),
  ),
  declaration: if custom { text("COR04CUSTOMDECLARATION") } else { none },
  ai_usage: select("COR04AIDISCLOSURENAME", "COR04 SAFE DIGITAL ASSISTANCE"),
  third_party_assistance: select(
    "COR04HUMANDISCLOSURENAME",
    "COR04 SAFE HUMAN ASSISTANCE",
  ),
  blind: identity == "blind",
  show_logo: false,
  font_theme: "classic",
  include_bibliography: true,
  bibliography_path: if reviewed {
    "/tests/rendered/cor04/reviewed.bib"
  } else {
    "/tests/rendered/cor04/identified.bib"
  },
)

#heading(select("COR04BOOKMARKNAME", "COR04 SAFE CHAPTER"))

#text(select(
  "COR04PROSENAME wrote this paragraph. ORCID 0000-0000-0000-0001 and email cor04prose@example.invalid.",
  "COR04 SAFE CHAPTER BODY. Authored identifiers have been reviewed in this synthetic specimen.",
))

#figure(
  image(
    "/tests/rendered/cor04/neutral.svg",
    width: 3cm,
    alt: select(
      "COR04ALTNAME cor04alt@example.invalid",
      "Neutral synthetic line diagram",
    ),
  ),
  caption: text(select("COR04CAPTIONNAME", "COR04 SAFE FIGURE")),
)

#if reviewed {
  [Contact details withheld for review.]
} else {
  link("mailto:cor04contact@example.invalid")[Contact]
}

#link(select(
  "https://example.invalid/COR04REPOOWNER",
  "https://example.invalid/resources",
))[Project resources]

The synthetic reference remains cited: @cor04self.

// These raw helper inputs deliberately bypass thesis metadata projection.
#contribution-table((
  (
    name: select("COR04RAWCONTRIBUTOR", "Reviewed contributor"),
    role: "Validation",
    percentage: 100,
  ),
))

The raw helper publication remains attributed.#publication-footnote((
  citation: select("COR04RAWPUBLICATION", "Reviewed publication"),
  status: "published",
  consent: true,
))
