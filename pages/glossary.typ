// =================================
// Glossary Page
// =================================

#import "../utils/style.typ": *

#let glossary-page() = {
  // Page setup
  set page(
    margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm)
  )

  // Page header
  align(center)[
    #text(size: 18pt, weight: "bold", fill: colors.primary)[
      Glossary
    ]
  ]

  v(1cm)

  // Introduction
  [This glossary provides definitions for key terms and concepts used throughout this thesis. Terms are listed in alphabetical order.]

  v(0.5cm)

  // Create and print glossary directly
  let glossary-entries = (
    (
      key: "Machine Learning",
      short: "ML",
      long: "A subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. ML algorithms build mathematical models based on training data to make predictions or decisions.",
      desc: "Fundamental concept in modern data analysis and computational intelligence."
    ),
    (
      key: "Deep Learning",
      short: "DL",
      long: "A subset of machine learning based on artificial neural networks with multiple layers. DL models can automatically learn hierarchical representations of data through nonlinear transformations.",
      desc: "Advanced ML technique using neural network architectures."
    ),
    (
      key: "Feature Engineering",
      short: "FE",
      long: "The process of selecting, transforming, and creating features from raw data to improve machine learning model performance. This involves domain knowledge and statistical techniques to extract meaningful information.",
      desc: "Critical preprocessing step in ML pipeline development."
    ),
    (
      key: "Gradient Descent",
      short: "GD",
      long: "An optimization algorithm used to minimize the loss function in machine learning models. It iteratively adjusts model parameters in the direction of the steepest descent of the gradient.",
      desc: "Core optimization technique for training ML models."
    ),
    (
      key: "Overfitting",
      short: "OF",
      long: "A modeling error that occurs when a model learns the training data too well, capturing noise and random fluctuations rather than the underlying pattern. This leads to poor generalization on unseen data.",
      desc: "Common problem in ML model training requiring regularization techniques."
    ),
    (
      key: "Regularization",
      short: "REG",
      long: "A technique used to prevent overfitting by adding a penalty term to the loss function. Common methods include L1 (Lasso) and L2 (Ridge) regularization.",
      desc: "Method to improve model generalization and prevent overfitting."
    ),
    (
      key: "Cross-Validation",
      short: "CV",
      long: "A resampling technique used to evaluate machine learning models on limited data samples. It involves dividing the dataset into training and validation sets multiple times to assess model performance.",
      desc: "Statistical method for model evaluation and hyperparameter tuning."
    ),
    (
      key: "Hyperparameter",
      short: "HP",
      long: "Parameters that are set before the learning process begins, as opposed to model parameters that are learned during training. Examples include learning rate, number of hidden layers, and regularization strength.",
      desc: "Configuration parameters that control the learning process."
    ),
    (
      key: "Neural Network",
      short: "NN",
      long: "A computational model inspired by biological neural networks. It consists of interconnected nodes (neurons) organized in layers that process and transform input data through weighted connections.",
      desc: "Foundation of deep learning architectures."
    ),
    (
      key: "Supervised Learning",
      short: "SL",
      long: "A type of machine learning where the model learns from labeled training data to make predictions on unseen data. The algorithm learns the mapping between input features and target outputs.",
      desc: "ML paradigm requiring labeled training data."
    ),
    (
      key: "Unsupervised Learning",
      short: "UL",
      long: "A type of machine learning where the model learns patterns and structures from unlabeled data. Common tasks include clustering, dimensionality reduction, and anomaly detection.",
      desc: "ML paradigm for discovering hidden patterns in data."
    ),
    (
      key: "Reinforcement Learning",
      short: "RL",
      long: "A type of machine learning where an agent learns to make decisions by interacting with an environment. The agent receives rewards or penalties based on its actions and learns to maximize cumulative rewards.",
      desc: "ML paradigm for sequential decision-making problems."
    ),
    (
      key: "Big Data",
      short: "BD",
      long: "Extremely large datasets that cannot be processed using traditional data processing methods. Characterized by the three V's: Volume, Velocity, and Variety.",
      desc: "Modern data processing challenge requiring scalable solutions."
    ),
    (
      key: "Dimensionality Reduction",
      short: "DR",
      long: "Techniques used to reduce the number of features in a dataset while preserving important information. Common methods include Principal Component Analysis (PCA) and t-SNE.",
      desc: "Method to handle high-dimensional data and improve computational efficiency."
    ),
    (
      key: "Ensemble Learning",
      short: "EL",
      long: "A machine learning technique that combines multiple models to improve predictive performance. Common approaches include bagging, boosting, and stacking.",
      desc: "Method to improve model robustness and accuracy."
    )
  )

  // Print glossary entries manually
  for entry in glossary-entries {
    block[
      *#entry.key* (#entry.short)
      #v(0.3em)
      #entry.long
      #v(0.5em)
      #emph[#entry.desc]
    ]
    v(0.8em)
  }

  // Additional information
  v(1cm)

  block(
    fill: rgb("#F8F9FA"),
    stroke: (left: 3pt + rgb("#00539C")),
    inset: 1em,
    width: 100%
  )[
    *Glossary Usage Notes*

    - Terms marked with abbreviations (e.g., ML for Machine Learning) can be referenced using the short form after first use
    - All definitions are specific to the context of this thesis and machine learning research
    - Some terms may have broader meanings in other disciplines
    - This glossary serves as a quick reference for readers unfamiliar with machine learning terminology
  ]
}
