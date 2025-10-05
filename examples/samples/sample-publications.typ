// =================================
// Sample Chapter: Publication Integration
// =================================

#import "../lib.typ": *

This sample chapter demonstrates how to integrate published works into your University of Melbourne thesis, following the University's guidelines for thesis with publications.

== Introduction to Publication Integration

The University of Melbourne allows candidates to include published works in their thesis, provided certain conditions are met. This chapter demonstrates the proper integration of publications into thesis chapters.

== Published Works Integration

=== Journal Article Integration

The following section is adapted from a published journal article:

#(config.publications.publication-footnote)(
  (citation: "Smith et al. (2024). Machine Learning Interpretability: A Comprehensive Framework. Journal of Artificial Intelligence Research, 68, 123-145.", status: "published", consent: true, appendix: "Appendix A")
)

#lorem(100)

As demonstrated in the literature, machine learning interpretability remains a critical challenge in modern AI systems.

=== Conference Paper Integration

Research findings from conference presentations can also be integrated:

#(config.publications.publication-footnote)(
  (citation: "Johnson & Smith (2023). Neural Network Explanations for Critical Applications. Proceedings of the International Conference on Machine Learning (ICML), 2023.", status: "published", consent: true, appendix: "Appendix B")
)

#lorem(80)

The conference paper presented preliminary results that informed the development of the comprehensive framework discussed in this thesis.

=== Unpublished Work Integration

Thesis chapters that have not been published can also be documented:

#(config.publications.publication-footnote)(
  (citation: "Smith (2024). Advanced Interpretability Techniques for Deep Learning Models. Chapter 3 of PhD Thesis.", status: "unpublished", consent: true)
)

#lorem(60)

This unpublished chapter develops novel techniques that extend beyond the published works.

== Publication Status Declaration

All publications included in the thesis must be declared in the preface with their current status:

- *Published*: Work that has been peer-reviewed and published
- *Accepted*: Work that has been accepted for publication but not yet published
- *Submitted*: Work that has been submitted for publication
- *In preparation*: Work that is being prepared for submission

== Integration Guidelines

=== Text Integration

When integrating published text, ensure:

- The original work is clearly identified with publication footnotes
- Any modifications are clearly indicated
- The integrated text flows naturally within the thesis narrative
- Cross-references between thesis chapters and publications are maintained

=== Figure and Table Integration

Published figures and tables should be:

- Clearly labeled with their source
- Adapted for thesis formatting if necessary
- Referenced in the publication footnotes

#figure(
  caption: [Example publication figure integration],
  // image("../figures/sample-figure.png", width: 80%) // Placeholder for actual figure
  rect(width: 80%, height: 4cm, fill: blue.lighten(80%))[Sample Figure Placeholder]
)

=== Citation Practices

- Cite your own published work using the standard citation format
- Include self-citations in the bibliography
- Ensure consistency with your chosen citation style

== Quality Assurance for Publication Integration

- [ ] All publications have been approved for inclusion by co-authors
- [ ] Publication status is accurately declared
- [ ] Text integration maintains academic integrity
- [ ] Copyright permissions have been obtained where required
- [ ] Formatting is consistent with thesis guidelines

== Chapter Summary

This chapter has demonstrated the proper integration of published works into a University of Melbourne thesis. The key requirements are clear documentation, appropriate permissions, and maintenance of academic integrity throughout the integration process.