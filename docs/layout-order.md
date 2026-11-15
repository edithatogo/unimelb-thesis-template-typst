# Bibliography, pagination and page margins

The thesis renders its bibliography after the core chapters and before the
appendices. The native bibliography supplies the heading, citations and
destinations; `thesis-bibliography(..., title: ...)` uses that one heading and
respects a custom title. A disabled bibliography emits neither its page nor a
reference list.

Core pages start at logical Arabic page 1. A duplex alignment page remains in
the preceding Roman-numbered front matter. Core chapter openings still use odd
physical pages in duplex mode, and an explicit `double_sided: false` still
overrides the print-profile default. Bibliography and appendix pages continue
the Arabic sequence. Appendix headings keep their own layout scope so that
chapter and appendix page-break rules cannot apply twice to the same heading.

Screen mode now uses 30 mm left and right margins, including direct appendix
layout calls. Its previous 25 mm side margins were below the requirement. All
four profiles retain A4 page size. These decisions implement the bounded
geometry and relative core/bibliography/appendix order in clauses 3.4 and 3.8
of the University's
[Preparation of Graduate Research Theses Process](https://gradresearch.unimelb.edu.au/processes/preparation-of-graduate-research-theses),
checked on 15 November 2026 (Australia/Brisbane).

## Evidence and scope

The canonical verifier runs nine synthetic cases covering the four profiles,
explicit duplex overrides, disabled bibliography, custom bibliography title
and the direct screen appendix layout. Its 184 assertions compare visible
body markers with native bookmark destinations and PDF page labels. Independent
Poppler bounding boxes measure the controlled left/right content boundaries;
all page dimensions are checked against A4. Each command retains the same
sixty-second timeout as the other rendered checks, with fresh outputs and
source/artifact digests.

The unchanged old production source fails eight cases under the same oracle;
the bibliography-disabled case is a positive control. An initial candidate
that nested appendix styling inside chapter styling was rejected because it
created an extra page and misplaced the native appendix bookmark. The repaired
composition keeps those scopes separate.

These cases establish the stated ordering, numbering and controlled geometry.
They do not establish every front-matter condition, arbitrary content fitting,
title-policy compliance, word-limit approval or full institutional submission
acceptance. The remaining policy and accessibility gates retain their own
requirements.
