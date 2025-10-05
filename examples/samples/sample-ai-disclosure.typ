// =================================
// Sample Chapter: AI Usage Disclosure and Academic Integrity
// =================================

#import "../lib.typ": *

This sample chapter demonstrates how to transparently document AI usage in research and writing, following University of Melbourne guidelines for academic integrity and digital assistance tools.

== Introduction to AI Usage in Research

The University of Melbourne acknowledges that AI tools can enhance research productivity while maintaining academic integrity. This chapter demonstrates proper disclosure and documentation of AI assistance.

== AI in Literature Review and Research Design

=== Literature Search Assistance

AI tools were used to enhance the efficiency of literature review processes:

#lorem(50)

**AI Tool Usage:**
- **ChatGPT-4**: Assisted in identifying relevant search terms and databases
- **Semantic Scholar API**: Automated paper recommendations based on initial seed papers
- **Connected Papers**: Visual exploration of citation networks

**Human Verification:**
- All AI-suggested papers were manually reviewed for relevance
- Citation accuracy was verified against original sources
- Research gaps were independently identified by the researcher

=== Research Methodology Development

AI assistance in developing research methodology:

#lorem(40)

**AI Contributions:**
- **GitHub Copilot**: Suggested algorithmic approaches and code structures
- **Wolfram Alpha**: Assisted with mathematical derivations and formula validation
- **Jupyter AI**: Generated initial data analysis scripts

**Researcher Responsibility:**
- All methodological decisions were made by the researcher
- AI suggestions were evaluated for appropriateness and validity
- Final methodology reflects researcher's expert judgment

== AI in Data Analysis and Processing

=== Automated Data Processing

AI tools enhanced data preprocessing and initial analysis:

```python
# AI-assisted data preprocessing script
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import KNNImputer

# Load dataset (AI suggested efficient loading method)
data = pd.read_csv('research_dataset.csv', low_memory=True)

# Automated missing value imputation (AI recommended KNN approach)
imputer = KNNImputer(n_neighbors=5)
data_imputed = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)

# Feature scaling (AI suggested standardization for ML algorithms)
scaler = StandardScaler()
data_scaled = pd.DataFrame(scaler.fit_transform(data_imputed), columns=data.columns)

print(f"Data preprocessing completed. Shape: {data_scaled.shape}")
```

**AI Tool Usage:**
- **GitHub Copilot**: Generated initial code structure and error handling
- **DataRobot**: Suggested preprocessing pipelines and feature engineering approaches
- **AutoML Tools**: Provided baseline model comparisons

**Quality Assurance:**
- All preprocessing steps were validated manually
- Data integrity was verified through statistical checks
- Results were reproducible without AI tools

== AI in Writing and Academic Communication

=== Text Generation and Editing

AI assistance in manuscript preparation:

#lorem(30)

**AI Tools Used:**
- **Grammarly**: Grammar and style checking
- **ChatGPT**: Initial draft generation for complex explanations
- **QuillBot**: Paraphrasing assistance for clarity

**Academic Integrity Measures:**
- All AI-generated text was substantially rewritten by the researcher
- Original ideas and interpretations remain the author's work
- AI was used as an editing tool, not content generator

=== Figure and Visualization Creation

AI assistance in creating visual materials:

#figure(
  caption: [AI-assisted diagram of research methodology],
  cetz.canvas({
    import cetz.draw: *

    // Research process flowchart
    let start = (0, 0)
    let literature = (0, 2)
    let design = (0, 4)
    let implementation = (0, 6)
    let analysis = (0, 8)
    let conclusion = (0, 10)

    // Draw process steps
    circle(start, radius: 0.7, fill: blue.lighten(80%))
    content(start, [*Research* \ *Question*])

    circle(literature, radius: 0.7, fill: green.lighten(80%))
    content(literature, [*Literature* \ *Review*])

    circle(design, radius: 0.7, fill: yellow.lighten(80%))
    content(design, [*Methodology* \ *Design*])

    circle(implementation, radius: 0.7, fill: orange.lighten(80%))
    content(implementation, [*Implementation*])

    circle(analysis, radius: 0.7, fill: red.lighten(80%))
    content(analysis, [*Analysis*])

    circle(conclusion, radius: 0.7, fill: purple.lighten(80%))
    content(conclusion, [*Conclusion*])

    // Flow arrows
    line(start, literature, mark: (end: ">"))
    line(literature, design, mark: (end: ">"))
    line(design, implementation, mark: (end: ">"))
    line(implementation, analysis, mark: (end: ">"))
    line(analysis, conclusion, mark: (end: ">"))
  })
)

**AI Tool Usage:**
- **DALL-E/Midjourney**: Initial concept visualization
- **Canva**: Layout and design assistance
- **BioRender**: Scientific diagram templates

**Human Verification:**
- All diagrams were manually redrawn and customized
- Scientific accuracy was verified by domain experts
- Final versions reflect researcher's creative input

== Comprehensive AI Usage Log

=== Detailed Usage Documentation

#table(
  columns: (auto, auto, auto, auto, auto),
  align: (left, left, left, left, left),
  table.header([*Date*], [*AI Tool*], [*Purpose*], [*Output Description*], [*Verification Method*]),
  [2024-01-15], [ChatGPT-4], [Literature search], [Search term suggestions], [Manual review of all recommendations],
  [2024-02-01], [GitHub Copilot], [Code generation], [Initial algorithm implementations], [Code review and testing],
  [2024-02-15], [Grammarly], [Text editing], [Grammar and style corrections], [Final human proofreading],
  [2024-03-01], [Wolfram Alpha], [Mathematical verification], [Formula validation], [Independent derivation],
  [2024-03-15], [DALL-E], [Figure conceptualization], [Initial diagram sketches], [Manual redrawing],
  [2024-04-01], [Jupyter AI], [Data analysis], [Initial statistical scripts], [Manual validation of results],
  [2024-04-15], [Connected Papers], [Citation network], [Paper recommendations], [Expert review of relevance],
  [2024-05-01], [DataRobot], [Feature engineering], [Preprocessing suggestions], [Domain expertise validation]
)

=== Usage Categories and Impact Assessment

**Research Process Enhancement:**
- **Efficiency Gains**: AI tools reduced literature review time by ~30%
- **Idea Generation**: AI suggested novel approaches for consideration
- **Error Prevention**: Automated tools caught formatting and grammatical errors

**Quality Assurance:**
- **Independence**: All critical decisions made by researcher
- **Verification**: AI outputs validated through multiple methods
- **Originality**: Core contributions remain author's work

== Ethical Considerations and Guidelines Compliance

=== University of Melbourne AI Guidelines

All AI usage complied with University policies:

- **Transparency**: All AI assistance is fully disclosed
- **Academic Integrity**: AI used as tools, not replacements for human judgment
- **Originality**: Research contributions are authentic and original
- **Accountability**: Researcher takes full responsibility for all work

=== Best Practices Implemented

- **Proportional Use**: AI used for routine tasks, human expertise for critical decisions
- **Documentation**: Comprehensive logging of all AI interactions
- **Verification**: Multiple validation methods for AI-generated content
- **Education**: Understanding of AI limitations and appropriate use

== AI Usage Quality Assurance Checklist

=== Research Integrity QA

- [x] All AI usage is transparently documented
- [x] AI tools used as assistants, not replacements
- [x] Critical thinking and decision-making remain human
- [x] Original contributions are author's work
- [x] AI limitations are acknowledged and addressed

=== Technical Validation QA

- [x] AI-generated code has been reviewed and tested
- [x] Data analysis results verified independently
- [x] Mathematical derivations checked manually
- [x] Visual materials validated for accuracy

=== Documentation QA

- [x] Complete AI usage log maintained
- [x] Usage categories clearly defined
- [x] Impact assessment conducted
- [x] Compliance with university guidelines confirmed

== Chapter Summary

This chapter has demonstrated comprehensive disclosure of AI usage in research, following University of Melbourne guidelines for academic integrity. The key principles are transparency, verification, and maintaining human judgment in all critical research decisions.</content>
<parameter name="filePath">/Users/doughnut/Library/CloudStorage/OneDrive-VictoriaUniversityofWellington-STAFF/unimelb-thesis-template-typst/samples/sample-ai-disclosure.typ