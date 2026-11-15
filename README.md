# University of Melbourne Thesis Template

A Typst thesis library with a small author starter. The package identity remains
`unimelb-thesis-template:0.2.1`; use the repository's pinned **Typst 0.15.1**.

The starter contains synthetic text, a synthetic reference and an original
geometric illustration. Replace them before academic use. The larger
`thesis.typ` remains a deliberately fictional demonstration.

## Start an independent author project

Install Typst 0.15.1 and Python 3.11 or later. From this repository's root:

```sh
python3 scripts/package_template.py build --archive build/package/template.tar.gz --receipt build/package/inventory.json
python3 scripts/package_template.py install --archive build/package/template.tar.gz --receipt build/package/inventory.json --cache build/package/packages
typst init --package-path "$PWD/build/package/packages" @local/unimelb-thesis-template:0.2.1 ../my-thesis
typst compile --package-path "$PWD/build/package/packages" --root ../my-thesis ../my-thesis/main.typ ../my-thesis/thesis.pdf
```

The installer verifies the retained archive/member hashes and refuses to replace
an existing installed version. Use a fresh package directory for another
candidate. This is a local installation; no Universe publication is implied.

The project starts with six files:

| File | Purpose |
| --- | --- |
| `main.typ` | Metadata, package import and chapter includes |
| `chapters/introduction.typ` | Synthetic chapter and nested figure example |
| `assets/figures/example.svg` | Original synthetic illustration |
| `references.bib` | Clearly labeled synthetic reference |
| `README.md` | Author instructions |
| `LICENSE` | Existing Apache-2.0 licence |

Keep the installed package path available when moving the project. The starter
imports the installed package and passes caller-owned resources as native
`path(...)` values; it does not import source files from this checkout.

## Edit, watch and choose a profile

Edit `main.typ`, replace the sample reference, and add chapter files with
`#include "chapters/your-chapter.typ"`. To watch the author project:

```sh
typst watch --package-path "$PWD/build/package/packages" --root ../my-thesis ../my-thesis/main.typ ../my-thesis/thesis.pdf
typst compile --package-path "$PWD/build/package/packages" --root ../my-thesis --input profile=draft ../my-thesis/main.typ ../my-thesis/draft.pdf
```

The available legacy profiles are `default`, `draft`, `screen` and `print`.
The starter selects the existing `classic` font theme; other theme definitions
and qualified rendering defaults remain unchanged. Fonts are installed
separately. See [font and payload scope](docs/fonts-and-package-payload.md).

Initial compilation can download ordinary Typst dependencies. A previous cold
cache exceeded the unchanged 60-second verification budget; separate provisioning
and a later successful retry did not establish a cold-start or offline guarantee.
See [the packaging evidence boundary](docs/packaging.md).

## Metadata and optional sections

The public Typst `thesis(...)` function accepts the fields demonstrated in the
starter. The [configuration guide](docs/cor03-configuration.md) describes resolved
overrides and native bibliography paths. The [optional-section guide](docs/optional-sections.md)
documents public `publications`, `assistance`, `prior_work`, `funding` and
`creative_outputs` records, and the rejected private prompt-log interface.

Executable public examples include
[safe assistance disclosures](examples/samples/sample-ai-disclosure.typ) and
[creative outputs](examples/samples/sample-creative-outputs.typ).
The [terms guide](docs/terms-rendered-correctness.md) covers explicit glossary and
index data. [Image examples](docs/native-images.md) describe native resource input.
The [shared JSON contract](docs/thesis-contract.md) has a separate adapter and
acceptance boundary; its fields are not implicit aliases for Typst arguments.

Blind output projects structured template-owned identity fields. Authored prose,
self-citations, index entries, URLs and image alternative text still require
author review. A failed residual-identity scan remains failed evidence.
Read [the blind corpus scope](tests/rendered/cor04/README.md) before sharing a PDF.

## Verify the source and outputs

Contributors use the existing canonical entry point:

```sh
make verify
make coverage
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for pinned dependencies and native tools.
The packaging extension builds an actual archive, installs it into a fresh local
package directory, initializes an author project and checks relocation, resource
edits, bibliography replacement, watch mode, required failures and the committed
thumbnail. Its report belongs to `build/verification/report.json`; successful
commands, output identities and actual errors are retained.

The reconstructed packaging candidate requires fresh source and receiving CI.
Earlier prototype passes remain historical observations, as described in
[docs/packaging.md](docs/packaging.md). Required checks and the 80% Python coverage
floors remain in place.

## Before submission or distribution

Review the actual PDF, applicable University requirements, accessibility, rights,
authorship declarations and required deposit files. Compilation alone does not
certify those outcomes. Keep private author projects and approval material out of
the public template repository. Full deposit packaging remains separate work.

For local archive rules and thumbnail generation, see
[the package guide](docs/packaging.md). For a future registry submission, see
[SUBMITTING_TO_TYPST_PACKAGES.md](SUBMITTING_TO_TYPST_PACKAGES.md).
Source protection, provider identities and the offline-security prerequisites are
documented in [Maintenance](docs/maintenance.md) and [SECURITY.md](SECURITY.md).
