#import "../../../utils/style.typ": thesis-image
#set page(paper: "a4", margin: 2cm)
#set text(font: "Libertinus Serif")
#let resource = sys.inputs.at("resource", default: "png")
#let image-source = if resource == "native" {
  path("assets/control.jpg")
} else if resource == "bytes" {
  read("assets/control.jpg", encoding: none)
} else { "/tests/rendered/images/assets/control." + resource }
IMAGE INPUT CONTROL

#thesis-image(
  image-source,
  width: 3cm,
  alt: "Synthetic geometric colour squares",
)
