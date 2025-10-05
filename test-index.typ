#import "lib.typ": *

// Test configuration for index feature
#show: thesis.with(
  title: "Test Thesis with Index",
  author: "Test Author",
  degree: "Doctor of Philosophy",
  department: "Test Department",
  school: "Test School",
  university: "Test University",
  submission_date: datetime(year: 2024, month: 12, day: 15),
  abstract: [This is a test thesis to verify index functionality.],
  keywords: ("test", "index"),
  acknowledgements: [Thanks for testing.],
  declaration: [This is a test declaration.],
  preface: [This thesis tests the index feature.],

  // Enable index feature with custom entries
  include_index: true,
  index_entries: (
    "Machine Learning": "15, 23, 45",
    "Neural Networks": "12, 34",
    "Deep Learning": "23, 67-69",
    "Algorithms": "18, 25",
    "Support Vector Machines": "28, 35",
    "Random Forests": "30, 38"
  ),
  include_glossary: false,
  include_abbreviations: false,
)

// Main content
= Introduction

This chapter introduces the main concepts of the thesis. We discuss machine learning algorithms and their applications.

== Background

The background section provides context for the research. Neural networks have become increasingly important in recent years.

= Methods

Our methodology involves several steps:

- Data collection
- Model training
- Evaluation metrics

== Algorithms

We implemented various algorithms including support vector machines and random forests.

= Results

The results show promising outcomes for the proposed approach.

= Conclusion

In conclusion, this work contributes to the field of machine learning.