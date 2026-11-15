# Evidence fixture boundary

`fixture_support.py` creates a small local Git repository, copies the pinned
contract bundle, and writes synthetic native/property records with real hashes
of those fixture files. It runs Git with a 60-second timeout and never contacts a
remote or changes a real repository's refs. The synthetic `.pdf` files are plain
test bytes, not successful compiler output.

The maintenance tests use these fixtures for source/commit/tree matching,
complete requirement status, central-wrapper compatibility, strict parsing,
tamper and stale evidence rejection, output containment and command-observation
validation. They also verify that an equal-tree commit cannot inherit another
commit's execution result and that a passing native observation cannot promote
full requirement, institutional or blind-delivery acceptance.

Real compiler/report consumer evidence is captured separately from a qualified
checkout and retains its exact native revision. That evidence is not replaced by
these synthetic controls.

The new fixture text and synthetic data are dedicated to the public domain under
CC0-1.0. Copied repository and contract files retain their existing licences and
attribution.
