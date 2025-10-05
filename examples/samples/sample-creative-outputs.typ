// =================================
// Sample Chapter: Creative Works and Research Outputs
// =================================

#import "../lib.typ": *

This sample chapter demonstrates how to document and integrate creative works, software, educational resources, and other research outputs into your University of Melbourne thesis.

== Introduction to Creative Outputs

Beyond traditional academic publications, research can produce various creative and practical outputs. This chapter demonstrates how to document these outputs in your thesis.

== Software Development and Implementation

=== Open-Source Software Library

This research produced an open-source Python library for machine learning interpretability:

```python
# interpretable_ml/__init__.py
"""
Interpretable Machine Learning Library

A comprehensive toolkit for explaining machine learning model predictions
with support for various interpretation methods and visualization tools.
"""

__version__ = "1.0.0"
__author__ = "Researcher Name"
__license__ = "MIT"

from .explainer import ExplanationFramework
from .visualization import plot_feature_importance, plot_explanation
from .metrics import faithfulness_score, stability_score

# Example usage
def main():
    # Load your trained model
    model = load_model('trained_classifier.pkl')

    # Create explanation framework
    explainer = ExplanationFramework(model)

    # Generate explanations
    explanations = explainer.explain(X_test, y_test)

    # Visualize results
    plot_feature_importance(explanations)
```

The software is available at: `https://github.com/researcher/interpretable-ml`

#figure(
  caption: [Software architecture diagram],
  cetz.canvas({
    import cetz.draw: *

    // Core components
    let core = (0, 0)
    let explainer = (-2, 2)
    let viz = (2, 2)
    let metrics = (0, 3)

    // Draw components
    rect(core, (2, 1), fill: blue.lighten(80%), name: "core")
    content(core, [*Core Engine*])

    rect(explainer, (2, 1), fill: green.lighten(80%), name: "explainer")
    content(explainer, [*Explanation* \ *Methods*])

    rect(viz, (2, 1), fill: yellow.lighten(80%), name: "viz")
    content(viz, [*Visualization* \ *Tools*])

    rect(metrics, (2, 1), fill: orange.lighten(80%), name: "metrics")
    content(metrics, [*Evaluation* \ *Metrics*])

    // Connections
    line("core.north", "explainer.south", mark: (end: ">"))
    line("core.north", "viz.south", mark: (end: ">"))
    line("explainer.north", "metrics.south", mark: (end: ">"))
    line("viz.north", "metrics.south", mark: (end: ">"))
  })
)

=== Software Quality Assurance

The software development followed best practices:

- **Version Control**: Git with semantic versioning
- **Testing**: Comprehensive unit and integration tests (coverage > 90%)
- **Documentation**: Complete API documentation with examples
- **Licensing**: MIT license for open-source distribution
- **DOI**: Software archived with Zenodo DOI: 10.5281/zenodo.1234567

== Educational Resources and Outreach

=== Online Tutorial Series

Created a comprehensive 5-part video tutorial series on machine learning interpretability:

1. **Introduction to Model Interpretability** (15 min)
   - Covers basic concepts and importance
   - Includes real-world examples

2. **Local Explanation Methods** (20 min)
   - LIME, SHAP, and counterfactual explanations
   - Hands-on demonstrations

3. **Global Explanation Techniques** (18 min)
   - Feature importance and partial dependence plots
   - Model-agnostic approaches

4. **Evaluation and Validation** (12 min)
   - Metrics for explanation quality
   - Human-centered evaluation methods

5. **Practical Implementation** (25 min)
   - End-to-end case study
   - Best practices and common pitfalls

The tutorial series is available on YouTube: `https://youtube.com/playlist?list=PLAYLIST_ID`

=== Interactive Jupyter Notebooks

Developed educational notebooks for hands-on learning:

```python
# notebook_example.ipynb

# Machine Learning Interpretability Tutorial
# This notebook demonstrates key concepts and practical implementations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from interpretable_ml import ExplanationFramework

# Load and prepare data
data = pd.read_csv('healthcare_dataset.csv')
X = data.drop('diagnosis', axis=1)
y = data['diagnosis']

# Train model
model = RandomForestClassifier(random_state=42)
model.fit(X, y)

# Create explanations
explainer = ExplanationFramework(model)
explanations = explainer.explain(X_test, y_test)

# Interactive visualization
explainer.create_interactive_dashboard(explanations)
```

=== Workshop Materials

Conducted workshops for researchers and practitioners:

- **University Workshop Series**: 3-session workshop at University of Melbourne
- **Industry Training**: Professional development sessions for data scientists
- **Conference Tutorials**: Full-day tutorials at major conferences

== Data Visualizations and Interactive Tools

=== Web-Based Interpretability Dashboard

Developed an interactive web application for exploring model explanations:

#figure(
  caption: [Screenshot of the interpretability dashboard],
  image("../figures/dashboard-screenshot.png", width: 90%)
)

Key features:
- **Interactive Exploration**: Click to explore individual predictions
- **Comparative Analysis**: Side-by-side comparison of explanation methods
- **Real-time Updates**: Dynamic visualization as parameters change
- **Export Capabilities**: Generate reports and shareable visualizations

=== Performance Visualization Suite

Created comprehensive visualization tools for model evaluation:

```python
# visualization_suite.py

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_performance_dashboard(results_dict):
    """Create interactive performance comparison dashboard"""

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Accuracy Comparison', 'Faithfulness Scores',
                       'Stability Analysis', 'Computational Efficiency')
    )

    # Add traces for each method
    for method, results in results_dict.items():
        fig.add_trace(
            go.Bar(name=method, x=['Accuracy'], y=[results['accuracy']]),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(name=method, x=results['complexity'],
                      y=results['faithfulness'], mode='markers'),
            row=1, col=2
        )

    fig.update_layout(title='Model Interpretability Performance Dashboard')
    return fig
```

== Research Impact and Dissemination

=== Media Coverage and Public Engagement

- **Newspaper Articles**: Featured in The Age and The Australian
- **Radio Interviews**: ABC Radio National Science Show
- **Blog Posts**: Towards Data Science and Analytics Vidhya
- **Social Media**: Active dissemination on Twitter/X and LinkedIn

=== Policy and Industry Engagement

- **Government Consultations**: Contributed to AI ethics framework development
- **Industry Partnerships**: Collaborations with healthcare and finance sectors
- **Standards Development**: Participation in IEEE standards committees

== Documentation of Creative Outputs

=== Comprehensive Documentation

All creative outputs are thoroughly documented:

- **Technical Specifications**: Detailed implementation guides
- **User Manuals**: Step-by-step usage instructions
- **API References**: Complete function and class documentation
- **Installation Guides**: Platform-specific setup instructions

=== Quality Assurance Checklist

- [ ] Software functionality verified through automated testing
- [ ] Documentation accuracy confirmed by peer review
- [ ] Educational materials evaluated for clarity and effectiveness
- [ ] Interactive tools tested across different browsers and devices
- [ ] All outputs archived with persistent identifiers (DOI, URLs)

== Chapter Summary

This chapter has demonstrated the diverse creative outputs that can result from research, including software development, educational resources, interactive tools, and public engagement activities. Proper documentation and quality assurance ensure these outputs have lasting impact and value.</content>
<parameter name="filePath">/Users/doughnut/Library/CloudStorage/OneDrive-VictoriaUniversityofWellington-STAFF/unimelb-thesis-template-typst/samples/sample-creative-outputs.typ