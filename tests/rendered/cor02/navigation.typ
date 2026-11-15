#import "/lib.typ": thesis
#show: thesis.with(
  title: "Synthetic Navigation Study",
  author: "Synthetic Candidate",
  degree: "Doctor of Philosophy",
  department: "Synthetic Department",
  school: "Synthetic School",
  university: "Synthetic University",
  submission_date: datetime(year: 2026, month: 11, day: 15),
  abstract: [NAV ABSTRACT SENTINEL],
  show_logo: false,
  font_theme: "classic",
  include_bibliography: false,
  appendices: (
    (
      title: "NAV APPENDIX ALPHA",
      creative: (
        medium: "NAV SYNTHETIC VIDEO",
        dimensions: "1920 by 1080 pixels",
        duration: "00:02:30",
        description: "NAV CREATIVE DESCRIPTION SENTINEL",
      ),
      content: [
        NAV APPENDIX ALPHA BODY

        == NAV APPENDIX ALPHA SECTION
        Appendix alpha subsection content.
      ],
    ),
    (
      title: "NAV APPENDIX BETA",
      content: [
        NAV APPENDIX BETA BODY

        == NAV APPENDIX BETA SECTION
        Appendix beta subsection content.
      ],
    ),
  ),
)

= NAV CHAPTER ALPHA <nav-alpha>
NAV CHAPTER ALPHA BODY

== NAV SECTION ALPHA
Section alpha content.

=== NAV DETAIL ALPHA
Detail alpha content.

#figure(
  rect(width: 35mm, height: 8mm),
  kind: image,
  caption: [NAV FIGURE ALPHA],
)
#figure(
  table(
    columns: 2,
    [Key], [Value],
    [Alpha], [One],
  ),
  caption: [NAV TABLE ALPHA],
)
#figure(
  block[Step one.],
  kind: "algorithm",
  supplement: [Algorithm],
  caption: [NAV ALGORITHM ALPHA],
)

#link(<nav-beta>)[NAV FORWARD LINK BETA]

= NAV CHAPTER BETA <nav-beta>
NAV CHAPTER BETA BODY

== NAV SECTION BETA
Section beta content.

#link(<nav-alpha>)[NAV BACK LINK ALPHA]
