// =================================
// Example Configuration for University of Melbourne Thesis Template
// =================================

// This file shows how to configure the thesis template with your information
// and demonstrates modern Typst features

#show: thesis.with(
  // Basic Information
  title: "Advancing Machine Learning Interpretability for Healthcare Applications",
  subtitle: "A Novel Framework for Explainable AI in Medical Diagnosis",
  author: "Dylan A Mordaunt",

  // Academic Information
  degree: "Doctor of Philosophy",
  department: "Department of Computing and Information Systems",
  school: "School of Computing and Information Systems",
  university: "The University of Melbourne",

  // Supervision
  supervisor: "Professor Maria Rodriguez",
  co_supervisor: "Dr. James Thompson",

  // Submission Details (using datetime for better formatting)
  submission_date: datetime(year: 2024, month: 12, day: 15),

  // Abstract
  abstract: [
    This thesis presents a comprehensive framework for improving the interpretability of machine learning models in healthcare applications. The research addresses the critical challenge of balancing model performance with clinical explainability requirements.

    Through theoretical analysis and empirical evaluation, we develop novel techniques for generating interpretable explanations of complex deep learning models. Our approach combines feature attribution methods with domain-specific knowledge integration to provide clinically meaningful insights.

    The framework is evaluated on multiple medical imaging datasets, demonstrating significant improvements in both prediction accuracy and explanation quality compared to existing methods. We also address important ethical considerations and provide guidelines for responsible AI deployment in healthcare settings.

    The contributions include: (1) a novel multi-modal explanation framework, (2) comprehensive evaluation on real-world medical datasets, (3) open-source implementation for reproducibility, and (4) clinical validation studies demonstrating practical utility.
  ],

  // Keywords
  keywords: (
    "machine learning",
    "interpretability",
    "healthcare",
    "explainable AI",
    "medical imaging",
    "deep learning"
  ),

  // Acknowledgements
  acknowledgements: [
    I would like to express my deepest gratitude to my supervisors, Professor Maria Rodriguez and Dr. James Thompson, for their invaluable guidance, support, and mentorship throughout this research journey.

    I am grateful to the University of Melbourne for providing the resources and environment that made this work possible. Special thanks to the members of the Health AI Lab for their collaborative spirit and constructive feedback.

    This research was supported by the Australian Research Council Discovery Project grant and the University of Melbourne's Research Training Program scholarship.

    Finally, I would like to thank my family and friends for their unwavering support and encouragement during the challenging yet rewarding process of completing this thesis.
  ],

  // Declaration
  declaration: [
    This thesis is submitted in partial fulfilment of the requirements for the degree of Doctor of Philosophy at The University of Melbourne.

    This thesis is my own work and contains no material which has been accepted for the award of any other degree or diploma in any university. To the best of my knowledge, this thesis contains no material previously published or written by another person, except where due reference is made in the text of the thesis.

    Some of the work in Chapter 4 has been published as: Mordaunt, D. A., Rodriguez, M., & Thompson, J. (2024). "Interpretable Deep Learning for Medical Image Analysis". In Proceedings of the International Conference on Medical Image Computing and Computer Assisted Intervention (MICCAI).

    The thesis contains approximately #word-count(lorem(10000)) words.
  ],

  // Preface (optional)
  preface: [
    The rapid advancement of artificial intelligence and machine learning has transformed numerous fields, with healthcare standing out as both a major beneficiary and a domain requiring particular caution. The "black box" nature of many state-of-the-art machine learning models presents significant challenges in medical applications where interpretability and trust are paramount.

    This thesis explores the intersection of machine learning interpretability and healthcare applications, seeking to bridge the gap between cutting-edge AI performance and clinical requirements for transparency and explainability.

    The work presented here builds upon my background in computer science and growing interest in healthcare applications, combining theoretical foundations with practical implementation to address real-world challenges.
  ],

  // Modern Features (uncomment to enable)
  // blind: true,                    // Blind review mode
  // double_sided: true,             // Double-sided printing
)
