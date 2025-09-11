// =================================
// Landscape Sample Page
// =================================

#import "../utils/style.typ": *

#let landscape-sample-page() = {
  // Set landscape orientation
  set page(
    height: auto,
    width: auto,
    margin: (top: 2.5cm, bottom: 2.5cm, left: 2cm, right: 2cm),
    flipped: true
  )

  // Page header
  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Sample Landscape Page: Advanced Equations and Diagrams
    ]
  ]

  v(1cm)

  // Complex mathematical equations
  [= Advanced Mathematical Formulations]

  [This page demonstrates the template's capability to handle complex mathematical equations and diagrams in landscape orientation, which is particularly useful for displaying wide equations, matrices, and detailed diagrams.]

  // Key mathematical results box
  block(
    fill: colors.primary.lighten(95%),
    inset: 1em,
    radius: 0.5em,
    stroke: colors.primary,
    width: 100%
  )[
    *Key Mathematical Results*

    The following equations demonstrate the theoretical foundations of the research methodology:
  ]

  // Complex equations
  align(center)[
    $ integral_(-oo)^(+oo) e^(-x^2) dif x = sqrt(pi) $
    v(0.5cm)
    $ lim_(n->oo) (1 + 1/n)^n = e $
    v(0.5cm)
    $ sum_(k=1)^oo 1/k^2 = pi^2/6 $
  ]

  // Matrix equations
  [= Matrix Formulations]

  align(center)[
    $ A = mat(
      a_11, a_12, dots.h, a_(1n);
      a_21, a_22, dots.h, a_(2n);
      dots.v, dots.v, dots.down, dots.v;
      a_(m 1), a_(m 2), dots.h, a_(m n)
    ) $
  ]

  // System of equations
  [= System of Linear Equations]

  align(center)[
    $ cases(
      a_11 x_1 + a_12 x_2 + dots.h + a_(1n) x_n = b_1,
      a_21 x_1 + a_22 x_2 + dots.h + a_(2n) x_n = b_2,
      dots.v,
      a_(m 1) x_1 + a_(m 2) x_2 + dots.h + a_(m n) x_n = b_m
    ) $
  ]

  // Advanced calculus
  [= Advanced Calculus]

  align(center)[
    $ nabla dot E = rho/epsilon_0 $
    v(0.5cm)
    $ nabla dot B = 0 $
    v(0.5cm)
    $ nabla times E = - partial B / partial t $
    v(0.5cm)
    $ nabla times B = mu_0 J + mu_0 epsilon_0 partial E / partial t $
  ]

  // Statistical formulations
  [= Statistical Models]

  align(center)[
    $ P(Y=1|X) = 1/(1 + e^(-beta_0 - beta_1 X_1 - dots.h - beta_p X_p)) $
    v(0.5cm)
    $ hat(theta) = arg max_theta L(theta|X) $
  ]

  // Algorithm demonstration
  [= Algorithm Example]

  figure(
    caption: [Gradient descent algorithm for optimization.]
  )[
    algo(
      title: "Gradient Descent Algorithm",
      parameters: (
        ($f$, "Objective function"),
        ($x_0$, "Initial point"),
        ($alpha$, "Learning rate"),
        ($epsilon$, "Convergence tolerance")
      )
    )[
      Initialize $x <- x_0$\
      *while* $norm(nabla f(x)) > epsilon$ *do*\
      $quad x <- x - alpha nabla f(x)$\
      *end while*\
      *return* $x$
    ]
  ]

  // Complex diagram
  [= Complex System Architecture]

  figure(
    caption: [Complex system architecture diagram showing data flow and processing pipeline.]
  )[
    fletcher.diagram(
      node-stroke: 1pt,
      spacing: (2cm, 1cm),

      node((0,0), [Data\nSources], shape: rect, fill: colors.secondary.lighten(80%)),
      edge((0,0), (1,0), "->", label: "Raw Data"),

      node((1,0), [Preprocessing\nModule], shape: rect, fill: colors.accent.lighten(80%)),
      edge((1,0), (2,0), "->", label: "Clean Data"),

      node((2,0), [Feature\nEngineering], shape: rect, fill: colors.primary.lighten(80%)),
      edge((2,0), (3,0), "->", label: "Features"),

      node((3,0), [Model\nTraining], shape: rect, fill: colors.success.lighten(80%)),
      edge((3,0), (4,0), "->", label: "Trained Model"),

      node((4,0), [Validation\n& Testing], shape: rect, fill: colors.warning.lighten(80%)),
      edge((4,0), (5,0), "->", label: "Validated Model"),

      node((5,0), [Deployment\n& Monitoring], shape: rect, fill: colors.error.lighten(80%)),
      edge((5,0), (3,0), "->", label: "Feedback", bend: -30deg),

      node((2.5,-1), [Model\nRegistry], shape: circle, fill: colors.info.lighten(80%)),
      edge((3,0), (2.5,-1), "->", label: "Store"),
      edge((2.5,-1), (5,0), "->", label: "Retrieve"),
    )
  ]

  // Performance metrics table
  [= Performance Metrics]

  figure(
    caption: [Comparative performance metrics across different models and datasets.]
  )[
    tablex(
      columns: (auto, auto, auto, auto, auto),
      align: center + horizon,
      auto-vlines: false,
      header-rows: 1,

      // Header
      [*Model*], [*Dataset*], [*Accuracy*], [*Precision*], [*F1-Score*],

      // Data rows
      [Logistic Regression], [Dataset A], [85.2%], [83.1%], [84.1%],
      [Random Forest], [Dataset A], [91.7%], [90.3%], [90.9%],
      [SVM], [Dataset A], [88.9%], [87.5%], [88.2%],
      [Neural Network], [Dataset A], [94.3%], [93.8%], [94.0%],

      [Logistic Regression], [Dataset B], [79.8%], [78.2%], [79.0%],
      [Random Forest], [Dataset B], [89.1%], [88.7%], [88.9%],
      [SVM], [Dataset B], [85.4%], [84.9%], [85.1%],
      [Neural Network], [Dataset B], [92.6%], [92.1%], [92.3%],

      [Logistic Regression], [Dataset C], [82.3%], [81.7%], [82.0%],
      [Random Forest], [Dataset C], [87.9%], [87.2%], [87.5%],
      [SVM], [Dataset C], [86.1%], [85.8%], [85.9%],
      [Neural Network], [Dataset C], [90.8%], [90.4%], [90.6%],
    )
  ]

  // Reset to portrait orientation for next pages
  set page(
    height: auto,
    width: auto,
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
    flipped: false
  )
}
