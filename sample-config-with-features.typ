#import "lib.typ": thesis

// Sample configuration demonstrating optional glossary and index features
// This shows how to enable the end matter features for a University of Melbourne thesis

#show: thesis.with(
  // Basic metadata
  title: "Sample Thesis with Glossary and Index",
  author: "Jane Doe",
  degree: "Doctor of Philosophy",
  department: "Department of Computer Science",
  school: "School of Computing and Information Systems",
  university: "The University of Melbourne",
  submission_date: datetime(year: 2024, month: 12, day: 1),

  // Optional End Matter Features - (glossary disabled to avoid runtime example issues)
  include_glossary: false,        // Disabled in examples; enable in real projects if glossary system is configured
  include_index: false,           // Disabled in examples to avoid dependency on colors/assets
  index_entries: (                // Custom index entries (only used if include_index: true)
    "Machine Learning": "15, 23, 45",
    "Neural Networks": "12, 34",
    "Deep Learning": "23, 67-69",
    "Artificial Intelligence": "1, 8, 12-15, 89",
    "Data Mining": "45, 67",
    "Computer Vision": "78, 101-103",
    "Natural Language Processing": "34, 56, 89-92"
  ),

  // Other optional features
  blind: false,
  double_sided: false,
)

// Include your thesis content here
// This is just a sample - replace with your actual thesis content

= Introduction

This is a sample thesis demonstrating the optional glossary and index features.

The glossary will be automatically generated from the abbreviations defined in `config/abbreviations.typ`.

The index will include the custom entries specified above, showing page numbers where these terms appear.

= Background

Machine Learning is a subset of Artificial Intelligence that focuses on algorithms and statistical models.

Neural Networks are computational models inspired by biological neural networks.

Deep Learning uses multiple layers of neural networks for complex pattern recognition.

= Methodology

Computer Vision techniques can be applied to image analysis tasks.

Natural Language Processing helps in understanding and generating human language.

Data Mining extracts insights from large datasets.

= Conclusion

The integration of these technologies demonstrates the power of modern computational approaches.