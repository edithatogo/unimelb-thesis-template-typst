#let statuses = (
  "unpublished",
  "submitted",
  "in revision",
  "accepted",
  "published",
)

#let validate(entry) = {
  if type(entry) != dictionary {
    panic("Publication entry must be a dictionary: " + repr(entry))
  }
  let status = entry.at("status", default: none)
  if status == none or not statuses.contains(status) {
    panic("Publication entry missing valid status (" + statuses.join(", ") + "): " + repr(entry))
  }
  entry
}

#let publication-footnote(entry) = {
  let v = validate(entry)
  let appendix = v.at("appendix", default: none)
  footnote([
    v.at("citation", default: ""),
    " (status: ", v.at("status", default: ""),
    ", consent: ", if v.at("consent", default: false) {"yes"} else {"no"},
    if appendix != none { ", appendix: " + appendix } else { "" },
    ")"
  ])
}

#let publication-status-table(entries) = {
  if entries.len() == 0 {
    none
  } else {
    table(
      columns: 4,
      column-gutter: 1em,
      [*Citation*, *Status*, *Consent*, *Appendix Ref*],
      ..entries.map(entry => {
        let v = validate(entry)
        [
          v.at("citation", default: ""),
          v.at("status", default: ""),
          if v.at("consent", default: false) {"Yes"} else {"No"},
          v.at("appendix", default: "")
        ]
      })
    )
  }
}

#let publication-appendix-entries(entries) = entries.filter(entry => entry.at("appendix", default: none) != none)

// =================================
// Publication registry helpers
// =================================

// Find a publication entry by citation text or index
#let find-publication(entries, key) = {
  if type(key) == "integer" {
    if key >= 0 and key < entries.len() { entries.at(key) } else { none }
  } else if type(key) == "string" {
    entries.find(e => e.at("citation", default: "") == key)
  } else {
    none
  }
}

// Attach a footnote to the current chapter referring to a publication.
// `key` may be an integer index or a citation string.
#let publication-chapter-footnote(entries, key) = context {
  let candidate = find-publication(entries, key)
  if candidate == none {
    // Render a lightweight note indicating missing entry, but do not fail.
    footnote(["Publication: (missing entry)"])
  } else {
    publication-footnote(candidate)
  }
}

// Render a link to the appendix specified in the publication entry (if present).
// If the appendix name is provided (e.g., "Appendix A"), this creates a textual
// cross-reference suitable for the listings and status table.
#let publication-appendix-link(entry, anchor: none) = {
  // Render a reference to the publication's appendix. If `anchor` is
  // provided, emit a proper clickable link()/anchor() pair; otherwise try
  // to infer a link target from the `appendix` text when it looks like an
  // anchor (e.g. "#app-b" or "app-b"). Otherwise fall back to plain text.
  let v = validate(entry)
  let appendix = v.at("appendix", default: none)
  if appendix == none {
    none
  } else {
    // Normalize appendix text
    let atext = appendix
    // If an explicit anchor parameter was passed, prefer it
    if anchor != none {
      // Emit a link to the named anchor
      link(atext, href: "#" + str(anchor))
    } else if atext.str().starts_with("#") {
      // Looks like a fragment already
      link(atext, href: str(atext))
    } else if atext.str().matches("^[A-Za-z0-9_-]+$") {
      // Looks like a simple id; create fragment
      link("See " + atext, href: "#" + str(atext))
    } else {
      // Fallback to plain textual reference (e.g., "See Appendix A")
      ["See ", atext]
    }
  }
}

// Pure helper that returns a new entry with an updated status. Useful in
// programmatic updates when generating status reports.
#let publication-status-update(entry, new_status) = {
  let v = validate(entry)
  if not statuses.contains(new_status) {
    panic("Invalid status: " + repr(new_status))
  }
  // Return a shallow updated dictionary
  (
    citation: v.at("citation", default: ""),
    status: new_status,
    consent: v.at("consent", default: false),
    appendix: v.at("appendix", default: none),
  )
}

// Extended status table with optional appendix link rendering
#let publication-status-table(entries, show_links: false) = {
  if entries.len() == 0 {
    none
  } else {
    table(
      columns: if show_links { 4 } else { 3 },
      column-gutter: 1em,
      if show_links { [*Citation*, *Status*, *Consent*, *Appendix Ref*] } else { [*Citation*, *Status*, *Consent*] },
      ..entries.map(entry => {
        let v = validate(entry)
        if show_links {
          [
            v.at("citation", default: ""),
            v.at("status", default: ""),
            if v.at("consent", default: false) {"Yes"} else {"No"},
            publication-appendix-link(v) ?: ""
          ]
        } else {
          [
            v.at("citation", default: ""),
            v.at("status", default: ""),
            if v.at("consent", default: false) {"Yes"} else {"No"}
          ]
        }
      })
    )
  }
}
