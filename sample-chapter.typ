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

#theorem("Central Research Problem")[
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

#definition("Empirical Risk Minimization")[
  The empirical risk minimization principle states that the best predictor is obtained by minimizing the empirical risk:

  $ hat(f) = arg min_(f in cal(F)) 1/n sum_(i=1)^n cal(L)(f(x_i), y_i) $
]

#theorem("Generalization Bound")[
  Under certain assumptions, with probability $1 - delta$, the following holds for any $f in cal(F)$:

  $ cal(R)(f) <= hat(cal(R))(f) + 2 sqrt( (log(|cal(F)|) + log(1/delta))/(2n) ) $
]

#proof[
  The proof follows from Hoeffding's inequality and the union bound argument. For a detailed derivation, see @vapnik1999nature.
]

== Algorithm Example

#algorithm(
  pseudocode(
    no-number,
    [*Input:* Training data $cal(D) = {(x_i, y_i)}_{i=1}^n$],
    [*Output:* Learned model $hat(f)$],
    [*Parameters:* Learning rate $eta$, number of iterations $T$],
    indent-size: 1em,
    line-gap: 0.8em,
    [*Algorithm:* Gradient Descent],
    block(
      numbering: none,
      [Initialize $w_0$ randomly],
      [*for* $t = 1$ *to* $T$ *do*],
      block(
        numbering: none,
        [Compute gradient $nabla cal(L)(w_(t-1))$],
        [Update weights $w_t = w_(t-1) - eta nabla cal(L)(w_(t-1))$],
      ),
      [*end for*],
      [*return* $w_T$],
    )
  ),
  caption: [Basic gradient descent algorithm]
)

== Code Example

#code-block(
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

== Contributions

The main contributions of this research include:

1. A novel interpretation framework for deep neural networks
2. Comprehensive evaluation on multiple benchmark datasets
3. Open-source implementation for reproducibility
4. Guidelines for responsible AI development

== Chapter Summary

#lorem(80)

This chapter has established the research context and outlined the structure of the thesis. The following chapters will delve deeper into each aspect of the research.

#display-word-count(lorem(1000))
#display-char-count(lorem(1000))

- *Chapter 2* reviews the relevant literature and theoretical foundations
- *Chapter 3* presents the proposed methodology in detail
- *Chapter 4* describes the experimental setup and results
- *Chapter 5* discusses the findings and implications
- *Chapter 6* concludes the thesis and suggests future work

== Contributions

The main contributions of this research include:

1. A novel interpretation framework for deep neural networks
2. Comprehensive evaluation on multiple benchmark datasets
3. Open-source implementation for reproducibility
4. Guidelines for responsible AI development

== Chapter Summary

#lorem(80)

This chapter has established the research context and outlined the structure of the thesis. The following chapters will delve deeper into each aspect of the research.
