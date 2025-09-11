// =================================
// Declaration Page
// =================================
// Based on University of Melbourne Graduate Research Thesis Preparation Process
// Version 3 - 11 June 2025 (clause 3.10)

#let declaration-page(
  candidate_name: none,
  thesis_title: none,
  degree: none,
  word_count: none,
  includes_publications: false,
  publication_details: none,
  ai_usage: none,
  third_party_assistance: none,
) = {
  heading("Declaration", numbering: none, outlined: false)
  v(2em)

  // Required declarations per thesis guidelines 3.10
  par[
    This is to certify that:

    a) the thesis comprises only my original work towards the #degree;

    #if includes_publications [
      b) due acknowledgement has been made in the text to all other material used;
    ] else [
      b) due acknowledgement has been made in the text to all other material used;
    ]

    c) the thesis is #word_count words in length, exclusive of tables, maps, bibliographies and appendices;

    #if includes_publications [
      d) the thesis comprises XX% dissertation and YY% creative outputs as agreed by the advisory committee at confirmation, where XX and YY total to 100.
    ]
  ]

  v(2em)

  // Signature section (Note: No signatures in electronic version per guidelines 3.7)
  align(right)[
    #candidate_name \
    #datetime.today().display("[day] [month repr:long] [year]")
  ]

  pagebreak()
}
