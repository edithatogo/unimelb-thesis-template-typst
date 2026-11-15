// SPDX-License-Identifier: Apache-2.0
// Standalone synthetic creative-output example. Compile from the repo root:
// typst compile --root . examples/samples/sample-creative-outputs.typ build/sample-creative-outputs.pdf
#import "../../lib.typ": thesis

#show: thesis.with(
  title: "Synthetic Creative Output Example",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  font_theme: "classic",
  show_logo: false,
  include_bibliography: false,
  creative_outputs: (
    (
      id: "synthetic-video",
      description: "Synthetic creative example: a short video exploring patterns of light.",
    ),
  ),
  // The pair is explicitly supplied; it is never inferred from record proportions.
  // Omit both values for a neutral declaration without an aggregate share.
  percentage_dissertation: 70,
  percentage_creative: 30,
)

= Creative output example

This synthetic example shows a public creative-output description and an explicit
percentage pair. It does not represent an actual submitted work or establish
committee agreement. A publication record alone does not create a creative clause.

Identifiers describe records; this example does not package media, establish rights,
verify an approval or create an archival deposit. Those steps need separate review.
