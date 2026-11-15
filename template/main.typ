// Licensed under the repository Apache-2.0 licence. All personal data are synthetic.
#import "@local/unimelb-thesis-template:0.2.1": thesis

#show: thesis.with(
  title: "A synthetic starter thesis",
  author: "Synthetic Student",
  supervisor: "Synthetic Supervisor",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "University of Melbourne",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [
    This small synthetic example demonstrates the author project boundary.
    Replace the text and metadata with your own reviewed thesis material.
  ],
  declaration: [
    This is synthetic demonstration content. Replace it with your own reviewed
    declaration; this example does not certify authorship or institutional approval.
  ],
  // This starter selects a theme with a font embedded in the pinned compiler.
  // The package's other theme definitions remain available and unchanged.
  font_theme: "classic",
  show_logo: false,
  bibliography_path: path("references.bib"),
  bibliography_style: "apa",
)

#include "chapters/introduction.typ"
