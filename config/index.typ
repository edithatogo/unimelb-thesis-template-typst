// =================================
// Modular Config Layer
// =================================

// Import all config modules
#import "metadata.typ": *
#import "publications.typ": *
#import "abbreviations.typ": *
#import "appendix.typ": *
#import "contributions.typ": *

// =================================
// Unified Config Interface
// =================================

// Main config dictionary exposing all modules
#let config = (
  // Metadata configuration
  metadata: (
    required-fields: required-fields,
    resolve: resolve,
  ),

  // Publications configuration
  publications: (
    statuses: statuses,
    validate: validate,
    publication-footnote: publication-footnote,
    publication-status-table: publication-status-table,
  ),

  // Abbreviations configuration
  abbreviations: (
    list: abbreviations,
  ),

  // Appendix configuration
  appendix: (
    appendix-counter: appendix-counter,
    reset-appendix-counter: reset-appendix-counter,
    appendix: appendix,
    creative-output-descriptor: creative-output-descriptor,
    appendix-summary: appendix-summary,
  ),

  // Contributions configuration
  contributions: (
    validate: validate-contribution,
    simple-table: simple-contribution-table,
    detailed-table: detailed-contribution-table,
    percentage-table: percentage-breakdown-table,
    ai-table: ai-contribution-table,
    matrix: contribution-matrix,
    sample: sample-contributions,
  ),
)

// =================================
// Helper Functions
// =================================

// Get a specific config module
#let get-config-module(name) = {
  config.at(name, default: none)
}

// Validate entire config against requirements
#let validate-config(metadata, publications: (), appendices: ()) = {
  // Validate metadata
  let resolved-metadata = config.metadata.resolve(metadata)

  // Validate publications
  let valid-publications = publications.map(config.publications.validate)

  // Validate appendices structure (basic validation)
  let valid-appendices = appendices

  (
    metadata: resolved-metadata,
    publications: valid-publications,
    appendices: valid-appendices,
  )
}