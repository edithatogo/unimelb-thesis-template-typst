# Preparing a registry submission

Start with the [local packaging guide](docs/packaging.md) and complete its actual
archive, installation, initialized-author, thumbnail and receiving-revision
checks. The maintained package identity remains
`unimelb-thesis-template:0.2.1`; no registry identity change is implied.

A locally valid package does not establish Universe submission approval.
Before publishing, compare the exact candidate with the current official
[manifest](https://github.com/typst/packages/blob/main/docs/manifest.md),
[categories](https://github.com/typst/packages/blob/main/docs/CATEGORIES.md),
[disciplines](https://github.com/typst/packages/blob/main/docs/DISCIPLINES.md),
[resource](https://github.com/typst/packages/blob/main/docs/resources.md) and
[licensing](https://github.com/typst/packages/blob/main/docs/licensing.md) guidance.

The naming rules require particular care for organization templates. Keep the
current local identity until an intentional migration or registry decision is
reviewed. The package is not represented as an official University publication.

Use a real thumbnail rendered from the initialized starter. Keep README and
licence metadata, identify third-party assets correctly and exclude unused fonts,
archives, private evidence and generated release artifacts from the runtime
bundle and author starter. The separate source font inventory and its licences
remain available in this repository.

The canonical packaging gate must match the committed thumbnail to a fresh
native render. The explicit recovery command only produces an unqualified image
for inspection and commit; it cannot satisfy the final gate itself.

Release/version/CFF synchronization, rights review and any registry submission
remain separate acceptance in issue #21. Existing tag-only release behavior,
repository governance and the offline-security prerequisites remain unchanged.
