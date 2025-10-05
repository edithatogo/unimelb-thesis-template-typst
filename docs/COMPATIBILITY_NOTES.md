Compatibility notes — small, safe edits made to improve example resilience

What I changed

- Made small, backward-compatible tolerances in `config/glossary.typ` and `lib.typ` so minimal
  examples can compile without adding large, extra assets.

Why

- Minimal examples are useful for users and CI smoke checks. Some example files exercise optional
  features (glossary/index) that require extra assets (color definitions, auxiliary config).

  Rather than adding many example-only assets or making examples fragile, a small,
  well-documented tolerance avoids panics and keeps the template usable out-of-the-box.

Why keeping these edits is recommended

- Low-risk: edits are defensive and scoped to optional code paths. They do not change public API
  semantics for typical users who use the full template.

- High value: reduces friction for newcomers and for CI smoke tests.

Alternative

- If maintainers prefer a strict API surface, revert these edits and add example wrapper files that
  adapt the example metadata and arguments to the strict API. This is slightly more work for
  maintainers but keeps core files unchanged.

Suggested follow-up

- Keep the current small edits, and include this note in the repository to explain the rationale.

- If desired, open a targeted PR to discuss whether these edits should be permanent or replaced with
  example-only adapters.
