// Typed options for the legacy thesis entry point. The shared JSON contract
// adapter is separate; this module preserves the legacy metadata layer.
#import "../utils/fonts.typ": font-themes
#import "../utils/locales.typ": available-locales

#let profiles = ("default", "draft", "screen", "print")

#let validate-choice(name, value, choices) = {
  if type(value) != str or value not in choices {
    panic("Invalid " + name + ": expected one of " + choices.join(", ") + ".")
  }
  value
}

#let validate-thesis-logo(value) = {
  if type(value) != bool {
    panic(
      "Invalid show_logo: expected a boolean; use false for this thesis template.",
    )
  }
  if value {
    panic(
      "show_logo=true is not permitted: University of Melbourne thesis preparation "
        + "clause 3.6 prohibits the University logo in a thesis. Use show_logo=false.",
    )
  }
  false
}

#let parse-cli(inputs) = {
  let parsed = (:)
  // Other sys.inputs belong to caller documents and are deliberately untouched.
  for (name, choices) in (
    profile: profiles,
    font_theme: font-themes(),
    locale: available-locales(),
  ) {
    if name in inputs {
      parsed.insert(name, validate-choice(name, inputs.at(name), choices))
    }
  }
  if "show_logo" in inputs {
    let raw = inputs.at("show_logo")
    if raw != "true" and raw != "false" {
      panic("Invalid CLI show_logo: expected exactly true or false.")
    }
    parsed.insert("show_logo", validate-thesis-logo(raw == "true"))
  }
  parsed
}

#let resolve-double-sided(value, profile: "default") = {
  let selected = validate-choice("profile", profile, profiles)
  if value == auto {
    selected == "print"
  } else {
    if type(value) != bool {
      panic(
        "Invalid double_sided: expected a boolean or auto for the profile default.",
      )
    }
    value
  }
}

#let resolve(
  profile: "default",
  font_theme: "unimelb",
  locale: "en",
  show_logo: false,
  double_sided: auto,
) = {
  let selected = validate-choice("profile", profile, profiles)
  (
    profile: selected,
    font_theme: validate-choice("font_theme", font_theme, font-themes()),
    locale: validate-choice("locale", locale, available-locales()),
    show_logo: validate-thesis-logo(show_logo),
    double_sided: resolve-double-sided(double_sided, profile: selected),
  )
}
