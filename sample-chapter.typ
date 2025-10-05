// =================================
// Sample Chapter: Introduction to Modern Machine Learning
// =================================

#import "lib.typ": *

This chapter provides an overview of the research context, problem statement, and thesis structure, demonstrating various modern Typst features.

== Research Context

#lorem(200)

The field of #emph[artificial intelligence] has seen rapid advancement in recent years, with applications spanning multiple domains including healthcare, finance, and autonomous systems.

=== Historical Development

The evolution of machine learning can be traced through several key phases:

1. *Statistical Learning* (1950s-1980s): Focus on probabilistic models and pattern recognition
2. *Neural Networks Renaissance* (1980s-1990s): Backpropagation and multi-layer perceptrons
3. *Deep Learning Era* (2010s-present): Large-scale neural architectures and big data

=== Current Challenges

Despite these advances, several challenges remain:

- Limited interpretability of complex models
- Data privacy and security concerns
- Computational resource requirements
- Ethical considerations in AI deployment

== Problem Statement

#lorem(150)

Penguin quantum supremacy was first hinted at in recent work.#(config.publications.publication-footnote)(
  (citation: "Featherstone et al. (2024)", status: "published", consent: true, appendix: "Appendix A")
)

#theorem(title: "Central Research Problem")[
  Given the increasing complexity of modern machine learning models and their widespread deployment in critical applications, there is an urgent need for methods that can provide interpretable, reliable, and ethically sound decision-making processes.
]

== Research Objectives

The primary objectives of this research are:

1. To develop a novel approach for improving model interpretability
2. To evaluate the proposed method on real-world datasets
3. To assess the computational efficiency and scalability
4. To address ethical considerations in the implementation

== Research Questions

This thesis addresses the following research questions:

+ How can we improve the interpretability of deep learning models?
+ What are the trade-offs between model complexity and explainability?
+ How do different interpretation methods perform on various data types?

== Methodology Overview

#lorem(100)

#figure(
  caption: [Research methodology flowchart],
  cetz.canvas({
    import cetz.draw: *

    // Define nodes
    let problem = (0, 0)
    let theory = (3, 2)
    let method = (6, 0)
    let evaluation = (9, 2)
    let results = (12, 0)

    // Draw nodes
    circle(problem, radius: 0.8, fill: blue.lighten(80%))
    content(problem, [*Problem* \ Formulation])

    circle(theory, radius: 0.8, fill: green.lighten(80%))
    content(theory, [*Theoretical* \ Framework])

    circle(method, radius: 0.8, fill: yellow.lighten(80%))
    content(method, [*Methodology* \ Development])

    circle(evaluation, radius: 0.8, fill: orange.lighten(80%))
    content(evaluation, [*Evaluation* \ & Analysis])

    circle(results, radius: 0.8, fill: red.lighten(80%))
    content(results, [*Results* \ & Conclusions])

    // Draw arrows
    line(problem, theory, mark: (end: ">"))
    line(theory, method, mark: (end: ">"))
    line(method, evaluation, mark: (end: ">"))
    line(evaluation, results, mark: (end: ">"))
  })
)

The research methodology combines theoretical analysis with empirical evaluation, utilizing both synthetic and real-world datasets.

== Mathematical Foundations

Consider a supervised learning problem where we have input-output pairs $(x_i, y_i)_(i=1)^n$. The goal is to learn a function $f: X -> Y$ that minimizes some loss function $cal(L)$.

#definition(title: "Empirical Risk Minimization")[
  The empirical risk minimization principle states that the best predictor is obtained by minimizing the empirical risk:

  $ hat(f) = arg min_(f in cal(F)) 1/n sum_(i=1)^n cal(L)(f(x_i), y_i) $
]

#theorem(title: "Generalization Bound")[
  Under certain assumptions, with probability $1 - delta$, the following holds for any $f in cal(F)$:

  $ cal(R)(f) <= hat(cal(R))(f) + 2 sqrt( (log(|cal(F)|) + log(1/delta))/(2n) ) $
]

#proof[
  The proof follows from Hoeffding's inequality and the union bound argument. For a detailed derivation, see Vapnik (1999).
]

== Algorithm Example

=== Algorithm Outline

#enum[
  [*Input:* Training data $cal(D) = {(x_i, y_i)}_{i=1}^n$]
  [*Output:* Learned model $hat(f)$]
  [*Parameters:* Learning rate $eta$, number of iterations $T$]
  [Initialize weights $w_0$ randomly]
  [Iteratively update $w_t = w_(t-1) - eta nabla cal(L)(w_(t-1))$]
  [Return $w_T$]
]

=== Pseudocode Example

#algorithm(
  caption: [Gradient descent algorithm for linear regression],
  title: [Linear Regression Training],
  [
    + *Input:* Training data $cal(D) = {(x_i, y_i)}_{i=1}^n$, learning rate $eta$, max iterations $T$
    + *Output:* Learned weights $w$
    + Initialize $w <- 0^d$
    + *for* $t <- 1$ *to* $T$ *do*
      + $y_"pred" <- X w$
      + $nabla cal(L) <- -2/X^T (y - y_"pred")$
      + $w <- w - eta nabla cal(L)$
      + *if* convergence criteria met *then*
        + *break*
    + *return* $w$
  ]
)

== Code Example

#code-block(
  caption: [Python implementation of gradient descent for linear regression],
  ```python
  import numpy as np
  from sklearn.model_selection import train_test_split

  class GradientDescent:
      def __init__(self, learning_rate=0.01, n_iterations=1000):
          self.lr = learning_rate
          self.n_iter = n_iterations
          self.weights = None

      def fit(self, X, y):
          # Initialize weights
          self.weights = np.zeros(X.shape[1])

          for _ in range(self.n_iter):
              # Compute predictions
              y_pred = self.predict(X)

              # Compute gradient
              gradient = -2 * X.T.dot(y - y_pred) / len(X)

              # Update weights
              self.weights -= self.lr * gradient

      def predict(self, X):
          return X.dot(self.weights)
  ```,
  lang: "python"
)

== Thesis Structure

This thesis is structured as follows:

- *Chapter 2* reviews the relevant literature and theoretical foundations
- *Chapter 3* presents the proposed methodology in detail
- *Chapter 4* describes the experimental setup and results
- *Chapter 5* discusses the findings and implications
- *Chapter 6* concludes the thesis and suggests future work

== Publications and Research Outputs

This research has resulted in several peer-reviewed publications and conference presentations that form the foundation of this thesis.

=== Published Works

The following publications have been derived from this research:

#(config.publications.publication-footnote)(
  (citation: "Smith et al. (2024). Deep Learning Interpretability Framework. Journal of Machine Learning Research.", status: "published", consent: true, appendix: "Appendix A")
)

#(config.publications.publication-footnote)(
  (citation: "Smith & Johnson (2023). Neural Network Explanations for Critical Applications. Proceedings of ICML.", status: "published", consent: true, appendix: "Appendix B")
)

#(config.publications.publication-footnote)(
  (citation: "Smith (2023). Towards Responsible AI: Interpretability in Deep Learning. PhD Thesis Chapter.", status: "unpublished", consent: true)
)

=== Conference Presentations

Research findings have been presented at international conferences:

- *International Conference on Machine Learning (ICML)*, 2024
  - Paper: "Interpretable Deep Learning for Healthcare Applications"
  - Presented preliminary results on model interpretability

- *Neural Information Processing Systems (NeurIPS)*, 2023
  - Workshop: "Explainable AI in Critical Systems"
  - Presented methodology and early validation results

== Creative Works and Outputs

Beyond traditional academic publications, this research has produced several creative and practical outputs.

=== Software Implementation

An open-source Python library has been developed to implement the proposed interpretability framework:

```python
# Example usage of the interpretability library
from interpretable_ml import ExplanationFramework

# Load trained model
model = load_model('trained_classifier.pkl')

# Create explanation framework
explainer = ExplanationFramework(model)

# Generate explanations for predictions
explanations = explainer.explain(X_test, y_test)

# Visualize feature importance
explainer.plot_feature_importance(explanations)
```

The software is available at: `https://github.com/researcher/interpretable-ml`

=== Educational Resources

Created comprehensive educational materials for teaching AI interpretability:

- **Online Tutorial Series**: 5-part video series on YouTube covering theoretical foundations and practical implementation
- **Interactive Jupyter Notebooks**: Hands-on tutorials with real datasets
- **Documentation Website**: Complete API documentation and usage examples

=== Data Visualizations

Developed interactive data visualizations to communicate research findings:

- **Model Interpretability Dashboard**: Web-based tool for exploring model explanations
- **Comparative Analysis Plots**: Visual comparisons of different interpretation methods
- **Performance Metrics Visualizations**: Interactive charts showing model performance across different datasets

== AI Usage and Disclosure

This thesis acknowledges the responsible use of artificial intelligence tools in the research and writing process.

=== AI Assistance in Research

AI tools were used in the following research activities:

- **Literature Review**: ChatGPT-4 was used to identify relevant papers and summarize key findings from initial database searches
- **Code Development**: GitHub Copilot assisted in writing boilerplate code and suggesting algorithmic improvements
- **Data Analysis**: Automated scripts using scikit-learn and pandas for initial data preprocessing and exploratory analysis

=== AI in Writing and Editing

AI assistance in manuscript preparation:

- **Text Polishing**: Grammarly and ChatGPT were used to improve clarity and readability of draft sections
- **Reference Formatting**: Automated tools helped format citations and ensure consistency
- **Figure Generation**: AI-assisted creation of diagrams and visualizations for complex concepts

=== AI Usage Log

#table(
  columns: (auto, auto, auto, auto),
  align: (left, left, left, left),
  table.header([*Date*], [*AI Tool*], [*Purpose*], [*Output Verification*]),
  [2024-01-15], [ChatGPT-4], [Literature search assistance], [Manual review of all recommendations],
  [2024-02-20], [GitHub Copilot], [Code suggestions], [Code review and testing],
  [2024-03-10], [Grammarly], [Text editing], [Final human proofreading],
  [2024-04-05], [DALL-E], [Figure conceptualization], [Manual redrawing and validation]
)

=== Ethical Considerations

All AI usage adhered to University of Melbourne guidelines:

- AI tools were used as assistants, not replacements for human judgment
- All AI-generated content was reviewed and verified by the researcher
- Original contributions and interpretations remain the author's work
- AI usage is transparently disclosed in all outputs

== Quality Assurance Checklist

This chapter and thesis have undergone rigorous quality assurance processes to ensure academic integrity and research quality.

=== Research Methodology QA

- [x] Research questions clearly defined and addressable
- [x] Methodology appropriate for research questions
- [x] Sample size justified and adequate
- [x] Data collection methods reliable and valid
- [x] Analysis methods correctly applied
- [x] Results accurately reported
- [ ] Limitations clearly acknowledged
- [ ] Alternative explanations considered

=== Academic Writing QA

- [x] Thesis structure follows standard format
- [x] Arguments logically developed and supported
- [x] Citations complete and accurately formatted
- [x] References correspond to in-text citations
- [x] Academic language appropriate and consistent
- [ ] Plagiarism check completed (iThenticate score < 15%)
- [ ] Proofreading completed by multiple reviewers

=== Technical QA

- [x] Code syntax validated and functional
- [x] Statistical analyses verified
- [x] Figures and tables correctly labeled
- [x] Data visualizations accurate and clear
- [x] Software dependencies documented
- [ ] Reproducibility confirmed by independent reviewer

=== Ethical Compliance QA

- [x] Human research ethics approval obtained (if applicable)
- [x] Animal ethics approval obtained (if applicable)
- [x] Data privacy and confidentiality maintained
- [x] Conflicts of interest declared
- [x] Research misconduct policies followed
- [ ] Authorship contributions accurately represented

=== Final Submission QA

- [ ] Word count within specified limits
- [ ] Formatting meets university requirements
- [ ] All required sections included
- [ ] Final proofreading completed
- [ ] Digital accessibility standards met
- [ ] Print-ready formatting validated

== Chapter Summary

#lorem(80)

This chapter has established the research context and outlined the structure of the thesis. The following chapters will delve deeper into each aspect of the research.
