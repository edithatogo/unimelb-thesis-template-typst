# Quick start

Use the [maintained README workflow](README.md#start-an-independent-author-project)
to build the audited local archive, verify/install it, initialize a six-file
author project and compile that project with Typst 0.15.1.

The current package identity is `unimelb-thesis-template:0.2.1`. This is a local
package workflow; it does not assume a published `@preview` package.

Edit the initialized `main.typ`, chapter and bibliography. Keep the installed
package path when compiling or watching. Caller images and bibliography values
use native `path(...)` values so moving the author project does not redirect
resources into the package.

The larger repository `thesis.typ` is a synthetic demonstration. Do not replace
it with private research when preparing a contribution to this public repository.

[Optional public records](docs/optional-sections.md),
[fonts](docs/fonts-and-package-payload.md),
[verification and current limitations](docs/packaging.md), and
[contributor setup](CONTRIBUTING.md) provide the detailed boundaries.
