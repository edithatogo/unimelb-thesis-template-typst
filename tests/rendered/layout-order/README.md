# Layout and order fixtures

The nine synthetic cases check one native bibliography heading, bibliography
before appendices, continuous Roman/Arabic page labels, duplex chapter starts
and 30 mm horizontal content boundaries. The corpus is run by `make verify`.

`oracles.py` contains independent expected content and relationships. The native
PDF parser is shared with the COR-02 test oracle, never with template rendering
code. Text/body markers, bookmarks, logical labels and bounding boxes all come
from the same newly compiled PDF. A custom bibliography title and a disabled
bibliography exercise the helper and applicability boundaries separately.

All content is synthetic and carries no scientific or institutional approval.
Geometry assertions apply to the controlled full-width boundary markers, not
arbitrary oversized content supplied by an author. Broader qualification scope
is documented in `docs/layout-order.md`.
