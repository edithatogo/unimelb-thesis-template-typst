// Compatibility import: maintain one public Preface implementation.
#import "../pages/preface.typ": preface-page as render-preface

#let preface-page(ctx, metadata) = render-preface(ctx, metadata)
