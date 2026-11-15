#import "../utils/style.typ": *
#import "../config/publications.typ": (
  publication-appendix-entries, publication-status-table,
)

#let contribution-table(contributions) = {
  if contributions.len() == 0 {
    none
  } else {
    // Normalize contributions into rows of (name, role, percent)
    let rows = contributions.map(row => if type(row) == dictionary {
      (
        row.at("name", default: ""),
        row.at("role", default: ""),
        row.at("percentage", default: ""),
      )
    } else {
      (
        row.at(0, default: ""),
        row.at(1, default: ""),
        row.at(2, default: ""),
      )
    })

    table(
      columns: 3,
      column-gutter: 1em,
      table.header([*Name*], [*Role*], [*Contribution (%)*]),
      ..rows.map(r => ([#r.at(0)], [#r.at(1)], [#r.at(2)])).flatten(),
    )
  }
}

// The legacy helper accepted private prompts and output logs. Empty calls stay
// harmless; nonempty data must be migrated explicitly to public descriptions.
#import "../config/optional.typ": private-log-migration, validate-records

#let ai-usage-note(ai_entries) = {
  if ai_entries != none and ai_entries != () {
    panic(private-log-migration)
  }
}

#let assistance-section(entries) = {
  validate-records("assistance", entries)
  if entries.len() > 0 {
    heading(level: 2, "Assistance")
    let labels = (
      human: "Human assistance",
      digital: "Digital assistance",
      ai: "AI assistance",
    )
    for entry in entries {
      par[#strong(labels.at(entry.kind)): #entry.description]
    }
    v(1em)
  }
}

#let prior-work-section(entries) = {
  validate-records("prior_work", entries)
  if entries.len() > 0 {
    heading(level: 2, "Prior Work")
    for entry in entries {
      par(entry.description)
      if "degree" in entry { par[Degree: #entry.degree] }
      if "institution" in entry { par[Institution: #entry.institution] }
      v(0.5em)
    }
    v(1em)
  }
}

#let creative-output-section(entries) = {
  validate-records("creative_outputs", entries)
  if entries.len() > 0 {
    heading(level: 2, "Creative Outputs")
    for entry in entries {
      par(entry.description)
      if "proportion" in entry {
        par[Declared record proportion: #entry.proportion%.]
      }
      v(0.5em)
    }
    v(1em)
  }
}

#let preface-publications_section(entries) = {
  if entries.len() == 0 {
    none
  } else {
    heading(level: 2, "Publication Register")
    v(0.5em)
    // Preserve supplied appendix references in the single real register.
    publication-status-table(
      entries,
      show_links: publication-appendix-entries(entries).len() > 0,
    )
  }
}
