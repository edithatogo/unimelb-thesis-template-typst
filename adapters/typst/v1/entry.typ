#import "document.typ": contract-document
#let envelope = json(sys.inputs.at("contract-input"))
#assert(
  envelope.schema_version == 1,
  message: "Unknown adapter input envelope.",
)
#contract-document(envelope.configuration)[
  #include sys.inputs.at("contract-body")
]
