// Public optional records use the shapes in contracts/thesis/v1. Reference
// identifiers are accepted for author bookkeeping; renderers do not print them.
#let private-log-migration = "Private ai_assistance logs are not a public thesis field. Migrate to assistance records with kind and description; keep prompts and output logs outside the thesis."

#let reject-private-log(value) = {
  if value != none {
    panic(private-log-migration)
  }
}

#let invalid(field, message) = panic("Invalid " + field + ": " + message)

#let nonempty-string(value, field) = {
  if type(value) != str or value.len() == 0 {
    invalid(field, "expected a nonempty string.")
  }
}

#let identifier(value, field) = {
  if (
    type(value) != str
      or value.match(regex("^[A-Za-z0-9][A-Za-z0-9._:-]*$")) == none
  ) {
    invalid(
      field,
      "expected an identifier using letters, digits, dot, underscore, colon or hyphen.",
    )
  }
}

#let percentage(value, field) = {
  if type(value) != int and type(value) != float {
    invalid(field, "expected a finite number from 0 to 100.")
  }
  if (
    float.is-nan(value)
      or float.is-infinite(value)
      or not (value >= 0 and value <= 100)
  ) {
    invalid(field, "expected a finite number from 0 to 100.")
  }
}

#let validate-records(field, values) = {
  if type(values) != array {
    invalid(field, "expected an array of public records.")
  }
  let fields = (
    funding: ("funder", "grant", "acknowledgement"),
    prior_work: ("description", "degree", "institution", "approval_ref"),
    assistance: ("kind", "description", "reference"),
    creative_outputs: ("id", "description", "proportion", "resource_ids"),
  )
  let required = (
    funding: ("funder",),
    prior_work: ("description",),
    assistance: ("kind", "description"),
    creative_outputs: ("id", "description"),
  )
  for (index, row) in values.enumerate() {
    let path = field + "[" + str(index) + "]"
    if type(row) != dictionary {
      invalid(path, "expected a public record dictionary.")
    }
    for key in row.keys() {
      if key not in fields.at(field) {
        invalid(
          path,
          "unknown field; use only the documented public record fields.",
        )
      }
    }
    for key in required.at(field) {
      if key not in row {
        invalid(path + "." + key, "required public field is missing.")
      }
    }
    for (key, value) in row {
      let member = path + "." + key
      if key in ("id", "approval_ref", "reference") {
        identifier(value, member)
      } else if key == "kind" {
        if value not in ("human", "digital", "ai") {
          invalid(member, "expected human, digital or ai.")
        }
      } else if key == "proportion" {
        percentage(value, member)
      } else if key == "resource_ids" {
        if type(value) != array {
          invalid(member, "expected an array of unique identifiers.")
        }
        let seen = ()
        for resource in value {
          identifier(resource, member)
          if resource in seen {
            invalid(member, "expected an array of unique identifiers.")
          }
          seen.push(resource)
        }
      } else if key == "acknowledgement" {
        if type(value) != str {
          invalid(member, "expected a string.")
        }
      } else {
        nonempty-string(value, member)
      }
    }
  }
}

#let validate-layer(layer) = {
  if "ai_assistance" in layer {
    panic(private-log-migration)
  }
  for field in ("funding", "prior_work", "assistance", "creative_outputs") {
    if field in layer {
      validate-records(field, layer.at(field))
    }
  }
  for field in ("percentage_dissertation", "percentage_creative") {
    let value = layer.at(field, default: none)
    if value != none {
      percentage(value, field)
    }
  }
}

#let validate-creative(creative_outputs, dissertation, creative) = {
  validate-records("creative_outputs", creative_outputs)
  if dissertation == none and creative == none {
    return
  }
  if dissertation == none or creative == none {
    invalid(
      "creative percentages",
      "supply both percentage_dissertation and percentage_creative, or neither.",
    )
  }
  percentage(dissertation, "percentage_dissertation")
  percentage(creative, "percentage_creative")
  if creative_outputs.len() == 0 {
    invalid(
      "creative percentages",
      "creative_outputs must contain at least one record.",
    )
  }
  if dissertation + creative != 100 {
    invalid(
      "creative percentages",
      "percentage_dissertation and percentage_creative must total 100.",
    )
  }
}
