// Thumbnail generator for Typst package listing
// Compile with: typst compile thumbnail.typ thumbnail.png

#set page(
  width: 512pt,
  height: 512pt,
  margin: 20pt,
  fill: rgb("#f8f8f8")
)

#set text(font: "Liberation Sans", size: 11pt)

#import "assets/colors/unimelb-colors.typ": *

// Create a simple representative thumbnail
#align(center + horizon)[
  #block(
    width: 100%,
    height: 100%,
    fill: white,
    inset: 30pt,
    radius: 8pt,
    stroke: 2pt + rgb("#ddd")
  )[
    #align(center)[
      // Title area with university color
      #block(
        width: 100%,
        fill: traditional-heritage-100,
        inset: 15pt,
        radius: 4pt
      )[
        #text(fill: white, size: 18pt, weight: "bold")[
          University of Melbourne
        ]
      ]
      
      #v(20pt)
      
      // Template name
      #text(size: 24pt, weight: "bold", fill: traditional-heritage-100)[
        Thesis Template
      ]
      
      #v(10pt)
      
      // Subtitle
      #text(size: 12pt, fill: gray)[
        Modern Typst Template
      ]
      
      #v(30pt)
      
      // Sample content blocks
      #grid(
        columns: (1fr, 1fr),
        gutter: 10pt,
        block(
          width: 100%,
          height: 60pt,
          fill: magpie-light-25,
          radius: 3pt,
          inset: 8pt
        )[
          #text(size: 8pt, fill: magpie-dark-100)[
            *Chapter 1*\
            Introduction...
          ]
        ],
        block(
          width: 100%,
          height: 60pt,
          fill: magpie-light-25,
          radius: 3pt,
          inset: 8pt
        )[
          #text(size: 8pt, fill: magpie-dark-100)[
            *Chapter 2*\
            Methodology...
          ]
        ]
      )
      
      #v(15pt)
      
      // Features list
      #align(left)[
        #text(size: 9pt, fill: gray)[
          ✓ Official UoM Branding\
          ✓ Automated Front Matter\
          ✓ Bibliography Support\
          ✓ Professional Formatting
        ]
      ]
      
      #v(20pt)
      
      // Footer
      #text(size: 8pt, fill: gray)[
        Version 0.2.0 • Apache-2.0 License
      ]
    ]
  ]
]
