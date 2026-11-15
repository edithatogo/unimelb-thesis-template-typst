#import "part.typ": native-heading

#let data = json("data.json")
#let mode = sys.inputs.at("native_mode", default: "valid")
#let record = if mode == "malformed" { (title: false) } else { data }

#set text(font: "Libertinus Serif")
#set heading(numbering: "1.1")

#if mode != "missing" [#metadata(record)<native-metadata>]
#if mode == "duplicate" [#metadata(data)<native-metadata>]

= #native-heading
<native-heading>
NATIVE BODY SENTINEL.
See @native-heading.

#data.literal
