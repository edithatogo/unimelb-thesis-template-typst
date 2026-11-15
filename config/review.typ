// Reviewer projection for the legacy thesis entry point. The original resolved
// metadata stays private to the caller; this is not a packaging implementation.
#let validate-blind(value) = {
  if type(value) != bool {
    panic("Invalid blind: expected a boolean.")
  }
  value
}

#let review-notice = "Author review required: inspect authored text, references, images and links before sharing."

#let review-fields = (
  "title",
  "subtitle",
  "abstract",
  "body",
  "declaration",
  "preface",
  "preface_sections",
  "preface_contributions.role",
  "ai_usage",
  "third_party_assistance",
  "third_party_items",
  "appendices",
  "bibliography",
  "alternative_text",
  "link_targets",
  "index_entries",
  "raw_helper_calls",
)

#let project(resolved, labels: (:), show_logo: false, blind: false) = {
  let enabled = validate-blind(blind)
  if not enabled {
    return (
      metadata: resolved,
      labels: labels,
      show_logo: show_logo,
      notice: none,
      diagnostics: (),
    )
  }

  // Typst values are copied on modification. Never mutate the caller's values
  // or let a later page fall back to the original identifying metadata.
  let projected = resolved
  projected.author = "Author"
  projected.department = "Department withheld for review"
  projected.school = "School withheld for review"
  projected.university = "Institution withheld for review"
  projected.supervisor = "Withheld for review"
  projected.co_supervisor = none
  projected.keywords = ()
  projected.acknowledgements = none

  projected.preface_contributions = resolved
    .at(
      "preface_contributions",
      default: (),
    )
    .enumerate()
    .map(((index, row)) => {
      let role = if type(row) == dictionary {
        row.at("role", default: "")
      } else { row.at(1, default: "") }
      let percentage = if type(row) == dictionary {
        row.at("percentage", default: "")
      } else { row.at(2, default: "") }
      (
        name: "Contributor " + str(index + 1),
        role: role,
        percentage: percentage,
      )
    })

  // Keep publication status and consent, but do not forward citation strings,
  // original appendix/link targets, or unrecognized identity-bearing fields.
  projected.publications = resolved
    .at(
      "publications",
      default: (),
    )
    .enumerate()
    .map(((index, entry)) => (
      citation: "Publication "
        + str(index + 1)
        + " (details withheld for review)",
      status: entry.at("status", default: none),
      consent: entry.at("consent", default: false),
      appendix: none,
    ))

  let projected-labels = labels
  projected-labels.university_name = "Blind review copy"
  (
    metadata: projected,
    labels: projected-labels,
    show_logo: false,
    notice: review-notice,
    diagnostics: (
      (
        code: "author-review-required",
        message: review-notice,
        fields: review-fields,
      ),
    ),
  )
}

// A static, queryable boundary notice contains no original identifiers. It
// does not certify prose, citations, embedded resources, or reviewer packaging.
#let diagnostic-marker(diagnostics) = [
  #metadata((
    code: "blind-review-boundary",
    diagnostics: diagnostics,
  )) <blind-review-diagnostics>
]
