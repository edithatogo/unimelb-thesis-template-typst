#import "lib.typ": *

// Test configuration for glossary and abbreviations features
#show: thesis.with(
  title: "Test Thesis with Glossary and Abbreviations",
  author: "Test Author",
  degree: "Doctor of Philosophy",
  department: "Test Department",
  school: "Test School",
  university: "Test University",
  submission_date: datetime(year: 2024, month: 12, day: 15),
  abstract: [This is a test thesis to verify glossary and abbreviations functionality.],
  keywords: ("test", "glossary", "abbreviations"),
  acknowledgements: [Thanks for testing.],
  declaration: [This is a test declaration.],
  preface: [This thesis tests the glossary and abbreviations features.],

  // Enable glossary and abbreviations features
  include_glossary: true,
  include_abbreviations: true,
  include_index: false, // We'll test this separately
)

// Main content with some text
= Introduction

This thesis explores machine learning and artificial intelligence. The field of computer vision has seen significant advances.

== Background

Machine Learning is a subset of Artificial Intelligence. Computer Vision is particularly important for visual applications.

= Methods

We used Support Vector Machine and Random Forest algorithms for comparison.

= Results

The Support Vector Machine outperformed the Random Forest model in our experiments.

= Conclusion

This work demonstrates the effectiveness of machine learning techniques in practical applications.