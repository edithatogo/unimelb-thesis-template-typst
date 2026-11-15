// Appendix helpers for enforcing ordering and creative output descriptors

// State for appendix counter
#let appendix-counter = state("appendix-counter", 0)

// Reset appendix counter (call at start of appendices)
#let reset-appendix-counter() = {
  appendix-counter.update(0)
}

// Shared native heading numbers: Appendix A: at level one, A.1 below it.
#let appendix-numbering(..numbers) = {
  let values = numbers.pos()
  let formatted = numbering("A.1.1", ..values)
  if values.len() == 1 { "Appendix " + formatted + ":" } else { formatted }
}

// Appendix macro that enforces ordering
// Usage: appendix("Title of Appendix")[content]
#let appendix(title, content) = {
  appendix-counter.update(count => count + 1)
  context {
    // Keep the public appendix sequence independent of preceding chapters,
    // while letting the native heading counter number appendix subsections.
    counter(heading).update(appendix-counter.get() - 1)
    set heading(numbering: appendix-numbering)
    heading(title, level: 1, outlined: true)
    v(1em)
    content
  }
}

// Creative output descriptor for theses with creative works
// Usage: creative-output-descriptor(medium: "Oil on canvas", dimensions: "100cm x 80cm", description: "Abstract landscape...")
#let creative-output-descriptor(
  medium: none,
  dimensions: none,
  duration: none,
  description: none,
) = {
  let fields = ()
  if medium != none { fields.push(("Medium", medium)) }
  if dimensions != none { fields.push(("Dimensions", dimensions)) }
  if duration != none { fields.push(("Duration", duration)) }
  if description != none { fields.push(("Description", description)) }

  if fields.len() > 0 {
    heading(level: 2, "Creative Output Descriptor")
    v(0.5em)
    table(
      columns: 2,
      column-gutter: 1em,
      [*Attribute*], [*Details*],
      ..fields.flatten(),
    )
    v(1em)
  }
}

// Helper to list appendices in table of contents or summary
#let appendix-summary(entries) = {
  if entries.len() > 0 {
    heading(level: 2, "Appendix Summary")
    v(0.5em)
    table(
      columns: 2,
      column-gutter: 1em,
      [*Appendix*, *Title*],
      ..entries
        .enumerate()
        .map(((i, title)) => [
          "Appendix " + ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z").at(i),
          title
        ]),
    )
  }
}
