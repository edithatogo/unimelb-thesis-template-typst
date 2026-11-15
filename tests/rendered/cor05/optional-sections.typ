// SPDX-License-Identifier: Apache-2.0
// Synthetic public records and private-looking sentinel data only.
#import "/lib.typ": thesis
#import "/pages/preface-helpers.typ": ai-usage-note

#let case = sys.inputs.at("cor05-case", default: "control")
#let publications = (
  (
    citation: "COR05 PUBLICATION ALPHA (2026)",
    status: "published",
    consent: true,
  ),
)
#let assistance = (
  (
    kind: "human",
    description: "COR05 HUMAN ASSISTANCE DESCRIPTION",
    reference: "COR05_PRIVATE_ASSISTANCE",
  ),
  (kind: "digital", description: "COR05 DIGITAL ASSISTANCE DESCRIPTION"),
  (kind: "ai", description: "COR05 AI ASSISTANCE DESCRIPTION"),
)
#let prior-work = (
  (
    description: "COR05 PRIOR WORK DESCRIPTION",
    degree: "COR05 PRIOR DEGREE",
    institution: "COR05 PRIOR INSTITUTION",
    approval_ref: "COR05_PRIVATE_APPROVAL",
  ),
)
#let funding = (
  (funder: "COR05 FUNDER ALPHA"),
  (
    funder: "COR05 FUNDER BETA",
    grant: "COR05 GRANT NUMBER",
    acknowledgement: "COR05 FUNDING ACKNOWLEDGEMENT",
  ),
)
#let creative = (
  (
    id: "COR05_CREATIVE_ID",
    description: "COR05 CREATIVE DESCRIPTION",
    resource_ids: ("COR05_CREATIVE_RESOURCE",),
  ),
)
#let private-log = (
  (
    tool: "Synthetic Tool",
    date: "2026-11-15",
    purpose: "Synthetic private log probe",
    prompt: "COR05_PRIVATE_PROMPT",
    output_ref: "COR05_PRIVATE_OUTPUT",
  ),
)
#let cases = (
  control: (:),
  "publications-only": (publications: publications),
  "publication-flag-only": (includes_publications: true),
  "legacy-digital-only": (ai_usage: "COR05 LEGACY DIGITAL SUMMARY"),
  "legacy-human-only": (third_party_assistance: "COR05 LEGACY HUMAN SUMMARY"),
  "assistance-only": (assistance: assistance),
  "prior-work-only": (prior_work: prior-work),
  "funding-only": (funding: funding),
  "creative-only": (creative_outputs: creative),
  "creative-proportion": (
    creative_outputs: (
      (
        id: "COR05_CREATIVE_ID",
        description: "COR05 CREATIVE DESCRIPTION",
        proportion: 30,
      ),
    ),
  ),
  "creative-percentages": (
    creative_outputs: creative,
    percentage_dissertation: 70,
    percentage_creative: 30,
  ),
  "creative-boundaries": (
    creative_outputs: creative,
    percentage_dissertation: 0,
    percentage_creative: 100,
  ),
  "creative-fractions": (
    creative_outputs: creative,
    percentage_dissertation: 70.5,
    percentage_creative: 29.5,
  ),
  "combined-order": (
    publications: publications,
    assistance: assistance,
    prior_work: prior-work,
    funding: funding,
    creative_outputs: creative,
    preface: [COR05 PREFACE BODY CONTROL.],
    acknowledgements: [COR05 ACKNOWLEDGEMENTS BODY CONTROL.],
  ),
  "metadata-overrides": (
    assistance: (
      (kind: "human", description: "COR05 BASE REPLACED DESCRIPTION"),
    ),
    metadata_overrides: (
      assistance: assistance,
      prior_work: prior-work,
      funding: funding,
      creative_outputs: creative,
    ),
  ),
  "empty-record-overrides": (
    assistance: assistance,
    prior_work: prior-work,
    funding: funding,
    creative_outputs: creative,
    metadata_overrides: (
      assistance: (),
      prior_work: (),
      funding: (),
      creative_outputs: (),
    ),
  ),
  "blind-authored-records": (
    blind: true,
    author: "COR05_MANAGED_AUTHOR",
    assistance: (
      (
        kind: "human",
        description: "COR05_ASSISTANCE_IDENTITY",
        reference: "COR05_PRIVATE_ASSISTANCE",
      ),
    ),
    prior_work: (
      (
        description: "Prior work review control",
        institution: "COR05_PRIOR_IDENTITY",
        approval_ref: "COR05_PRIVATE_APPROVAL",
      ),
    ),
    funding: ((funder: "COR05_FUNDING_IDENTITY"),),
    creative_outputs: (
      (id: "COR05_CREATIVE_ID", description: "COR05_AUTHORED_CREATIVE"),
    ),
  ),
  "blind-reviewed-records": (
    blind: true,
    author: "COR05_MANAGED_AUTHOR",
    assistance: (
      (
        kind: "human",
        description: "Reviewed assistance description",
        reference: "COR05_PRIVATE_ASSISTANCE",
      ),
    ),
    prior_work: (
      (
        description: "Reviewed prior work description",
        approval_ref: "COR05_PRIVATE_APPROVAL",
      ),
    ),
    funding: ((funder: "Funding details withheld for review"),),
    creative_outputs: (
      (
        id: "COR05_CREATIVE_ID",
        description: "Reviewed creative output description",
      ),
    ),
  ),
  "percentages-without-creative": (
    percentage_dissertation: 70,
    percentage_creative: 30,
  ),
  "private-argument": (ai_assistance: private-log),
  "private-override": (metadata_overrides: (ai_assistance: private-log)),
  "private-public-record": (
    assistance: (
      (
        kind: "ai",
        description: "Public description",
        prompt: "COR05_PRIVATE_PROMPT",
      ),
    ),
  ),
  "assistance-missing-kind": (
    assistance: ((description: "Synthetic description"),),
  ),
  "assistance-unknown-kind": (
    assistance: ((kind: "other", description: "Synthetic description"),),
  ),
  "assistance-wrong-container": (assistance: (:)),
  "assistance-wrong-record": (assistance: ("Synthetic string",)),
  "funding-missing-funder": (funding: ((grant: "Synthetic grant"),)),
  "funding-wrong-grant": (funding: ((funder: "Synthetic funder", grant: 42),)),
  "prior-work-empty-description": (prior_work: ((description: ""),)),
  "prior-work-invalid-reference": (
    prior_work: (
      (description: "Synthetic prior work", approval_ref: "invalid reference"),
    ),
  ),
  "creative-invalid-id": (
    creative_outputs: (
      (id: "../private", description: "Synthetic creative work"),
    ),
  ),
  "creative-invalid-proportion": (
    creative_outputs: (
      (
        id: "synthetic",
        description: "Synthetic creative work",
        proportion: 101,
      ),
    ),
  ),
  "creative-wrong-resources": (
    creative_outputs: (
      (
        id: "synthetic",
        description: "Synthetic creative work",
        resource_ids: "one-resource",
      ),
    ),
  ),
  "creative-duplicate-resources": (
    creative_outputs: (
      (
        id: "synthetic",
        description: "Synthetic creative work",
        resource_ids: ("resource-a", "resource-b", "resource-a"),
      ),
    ),
  ),
  "creative-missing-dissertation": (
    creative_outputs: creative,
    percentage_creative: 30,
  ),
  "creative-missing-creative": (
    creative_outputs: creative,
    percentage_dissertation: 70,
  ),
  "creative-boolean-percentage": (
    creative_outputs: creative,
    percentage_dissertation: true,
    percentage_creative: 30,
  ),
  "creative-negative-percentage": (
    creative_outputs: creative,
    percentage_dissertation: -1,
    percentage_creative: 100,
  ),
  "creative-overflow-percentage": (
    creative_outputs: creative,
    percentage_dissertation: 101,
    percentage_creative: 0,
  ),
  "creative-invalid-total": (
    creative_outputs: creative,
    percentage_dissertation: 60,
    percentage_creative: 30,
  ),
  "creative-infinite-percentage": (
    creative_outputs: creative,
    percentage_dissertation: calc.inf,
    percentage_creative: 0,
  ),
  "creative-nan-percentage": (
    creative_outputs: creative,
    percentage_dissertation: float.nan,
    percentage_creative: 0,
  ),
  "invalid-overridden-layer": (
    funding: "Invalid supplied layer",
    metadata_overrides: (funding: funding),
  ),
)

#if case == "private-helper" {
  set page(paper: "a4", margin: 20mm)
  set text(font: "Libertinus Serif")
  ai-usage-note(private-log)
} else {
  assert(case in cases)
  let options = (
    title: "COR05 optional-section specimen",
    author: "Synthetic Candidate",
    degree: "Doctor of Philosophy",
    department: "Synthetic Department",
    school: "Synthetic School",
    university: "Synthetic University",
    submission_date: datetime(year: 2026, month: 11, day: 15),
    abstract: [COR05 ABSTRACT CONTROL.],
    word_count: 1234,
    show_logo: false,
    font_theme: "classic",
    include_bibliography: false,
  )
  for (key, value) in cases.at(case) { options.insert(key, value) }
  show: thesis.with(..options)
  heading("COR05 MAIN CHAPTER")
  [COR05 MAIN BODY CONTROL.]
}
