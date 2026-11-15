// SPDX-License-Identifier: Apache-2.0
// Standalone synthetic public-disclosure example. Compile from the repo root:
// typst compile --root . examples/samples/sample-ai-disclosure.typ build/sample-ai-disclosure.pdf
#import "../../lib.typ": thesis

#show: thesis.with(
  title: "Synthetic Public Assistance Example",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  font_theme: "classic",
  show_logo: false,
  include_bibliography: false,
  assistance: (
    (
      kind: "human",
      description: "Synthetic example: a colleague commented on the structure of a draft.",
    ),
    (
      kind: "digital",
      description: "Synthetic example: a spelling checker suggested corrections.",
    ),
    (
      kind: "ai",
      description: "Synthetic example: an AI tool suggested alternative wording for author review.",
    ),
  ),
)

= Public disclosure example

This is a synthetic interface example. Replace each description with an accurate
account of assistance actually used, after reviewing the applicable requirements.
The records do not establish approval or certify compliance.

Public assistance records contain a kind and description. Keep prompts, tool
outputs, confidential material and private review notes outside the thesis.
For migration from the former private log helper, see the optional-sections guide.
