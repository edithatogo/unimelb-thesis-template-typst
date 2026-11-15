// Synthetic Apache-2.0 fixture: no real author or research identifiers.
#import "/lib.typ": thesis

#let identity = sys.inputs.at("cor04-identity", default: "identified")
#assert(identity in ("identified", "blind", "invalid"))
#let blind = if identity == "invalid" { "false" } else { identity == "blind" }

#show: thesis.with(
  title: "COR04 structured identity projection",
  author: "COR04BASEAUTHOR",
  degree: "Doctor of Philosophy",
  department: "COR04DEPARTMENT",
  school: "COR04SCHOOL",
  university: "COR04UNIVERSITY",
  supervisor: "COR04SUPERVISOR",
  co_supervisor: "COR04COSUPERVISOR",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [COR04 SAFE ABSTRACT BODY.],
  keywords: (
    "COR04KEYWORDNAME",
    "0000-0000-0000-0001",
    "cor04author@example.invalid",
  ),
  acknowledgements: [COR04ACKNAME supported this synthetic specimen.],
  preface: [COR04 SAFE PREFACE BODY.],
  preface_contributions: (
    (name: "COR04CONTRIBUTORALPHA", role: "Analysis", percentage: 60),
    ("COR04CONTRIBUTORBETA", "Validation", 40),
  ),
  publications: (
    (
      citation: "COR04PUBLICATIONALPHA (2026)",
      status: "published",
      consent: true,
      appendix: "Appendix COR04PUBLICATIONAPPENDIX",
    ),
    (
      citation: "COR04PUBLICATIONBETA (2025)",
      status: "accepted",
      consent: false,
    ),
  ),
  word_count: 1234,
  ai_usage: "COR04 SAFE DIGITAL ASSISTANCE",
  third_party_assistance: "COR04 SAFE HUMAN ASSISTANCE",
  metadata_overrides: (author: "COR04RESOLVEDAUTHOR"),
  blind: blind,
  show_logo: false,
  font_theme: "classic",
  include_bibliography: false,
)

= COR04 SAFE CHAPTER

COR04 SAFE CHAPTER BODY.
