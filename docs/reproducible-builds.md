# Bounded, network-disabled replay

`scripts/replay_build.py` can capture and replay one declared synthetic Typst
input closure. It copies that closure into two fresh directories, builds both
with the same fixed settings, and requires identical PDF bytes and SHA-256s.
Every actual compiler run uses a new Linux network namespace. A populated cache
alone cannot satisfy this check.

This implements a bounded part of [issue #20](https://github.com/edithatogo/unimelb-thesis-template-typst/issues/20).
It does not qualify every thesis profile, cross-environment repeatability, a
complete operating-system image, or a release bundle. It does not change normal
thesis defaults, publish artifacts, or replace the separate offline-security
provisioning conditions in [PR #9](https://github.com/edithatogo/unimelb-thesis-template-typst/pull/9).

## Run the declared specimen

Use the repository's supported Python and installed development dependencies,
the exact Typst version in `typst.toml`, qpdf, Poppler's `pdftotext` and `pdffonts`,
and util-linux `unshare`. The host must allow an unprivileged user/network
namespace. Put these executables on `PATH`; `--compiler /absolute/path/to/typst`
can select the compiler explicitly. Its binary must retain the name `typst` for
the shared native dependency validator.

Package acquisition is a separate provisioning action. Supply an already
prepared ordinary Typst preview package cache containing the inputs needed by
the fixture. Neither command below obtains missing packages successfully:
their compiler runs have no external network interface. A missing package stops
capture or replay and remains a failure.

```sh
python scripts/replay_build.py lock \
  --root . \
  --recipe replay/synthetic.json \
  --package-cache /absolute/path/to/prepared-package-cache \
  --output build/replay-lock

python scripts/replay_build.py replay \
  --bundle build/replay-lock \
  --lock-sha256 THE_EXACT_SHA256_PRINTED_BY_LOCK \
  --output build/replay-check
```

Both output directories must be new. Existing paths, symlink components and
previous outputs are rejected; use a new directory for another attempt so that
earlier failures remain available. Preserve the lock digest through a trusted
channel. Hashes detect changes relative to that digest; they do not authenticate
an attacker-supplied replacement lock. Keep the exact producer checkout too:
the lock requires the same replay helper, native dependency validator, package
input list and canonical runner bytes.

The supplied digest is checked against the same byte buffer that is parsed. A
later file replacement cannot substitute a different lock under that digest.
Capture likewise requires the parsed recipe bytes to match the recipe identity
in the copied project before compilation.

Successful commands return zero. Failure returns one. An unavailable or rejected
namespace backend returns two with `result: "unsupported"`; there is no online
fallback and an unsupported run is not a pass. Compiler and PDF commands retain
the canonical 60-second budget and bounded five-second process-group cleanup.
The worker probes the new namespace and then uses `execve` for the compiler, so
it remains in the command runner's process group.

## What the lock binds

The version-1 recipe is [replay/synthetic.json](../replay/synthetic.json). It
declares the entrypoint, native input paths, CLI inputs, creation time, selected
font files and licences, expected PDF font names, visible sentinels and scope.
Unknown fields, wrong types, unsafe relative paths, duplicate entries and an
incomplete required-input list fail validation. The supported dependency layout
is the ordinary `preview/name/version` package cache; this increment does not
support private namespaces or local package overrides.

| Input or condition | Retained identity and check |
| --- | --- |
| Project source and resources | SHA-256 and byte length for every copied runtime, fixture, configuration, image, bibliography and CSL input; the native dependency report must include the declared required inputs. |
| Preview packages | Native observed file hashes plus a separate inventory of **all files** in each observed package/version directory, including its matching manifest and retained licence files. The complete inventory has its own digest. |
| Fonts | Exact bytes for regular, bold and italic Source Serif Pro files, their original source paths and retained licence. The actual PDF must contain the three expected embedded faces. |
| Compiler and validators | Exact executable SHA-256s and observed version strings for Typst, qpdf, pdftotext, pdffonts and unshare. Typst must match the repository version before capture. |
| Python and host observations | Python executable hash/version, jsonschema version, platform, architecture, kernel and libc version. These observations must match on replay; they are not an operating-system or shared-library lock. |
| Producer and source observations | Hashes of the four Python producer/validation files, plus observed Git revision, tree and dirty state when a checkout is available. A dirty source observation is retained as dirty. |
| Deterministic settings | Fixed creation timestamp, explicit document date, synthetic seed, CLI inputs, one compiler job, UTC and C.UTF-8, explicit font directory, and disabled system/embedded font discovery. |
| Output | Actual successful compiler command/log, native input/output report, PDF hash and size, qpdf check, extracted text hash and PDF font observations. |

The fixture imports the public `thesis-image` helper and exercises an authored
image, JSON configuration, bibliography and custom CSL style. It is a single
synthetic document, not a complete thesis. Its imports currently reach 18 preview
package/version trees; this work records that actual closure without changing
which template imports are unconditional.

Each replay copies the locked project, complete package trees and selected fonts
into distinct directories. It supplies an empty local-package directory and the
copied package cache explicitly. The compiler receives only `TZ`, `LANG`,
`LC_ALL` and `SOURCE_DATE_EPOCH` in its environment, with explicit CLI flags for
fonts, packages, time and job count. Inputs are checked before copying, after
copying and after compilation; original bundle files are checked again after
both builds. Changed or missing inputs cannot earn a replay pass. Actual native
input identities must equal the discovery closure in both relocated builds.

The native dependency list does not identify every glyph's source file. Font
scope is therefore established separately by disabling system and embedded
fonts, offering only the three locked font files, using `fallback: false` in the
fixture, and inspecting the actual embedded PDF font names. This does not qualify
unselected font families or a general per-glyph font provenance mechanism.
Source Serif Pro's existing SIL Open Font License and reserved name remain
unchanged; the helper copies that licence with the selected font bytes.

## Evidence that the compiler cannot use the network

The parent establishes a listening loopback socket and successfully connects to
it before entering the isolated run. The worker then checks a different
`/proc/self/ns/net` identity and the namespace's `/proc/net/dev` inventory. Only
the loopback interface may exist, and a connection to the parent's proven
listener must fail. The compiler is executed in that same namespace immediately
after the checks. The receipt retains the namespace identities, native interface
inventory hash, connection result, compiler argv and minimal environment.

The independent native controls also compile with an **empty package cache** in
that boundary. This invocation must fail for the missing package, retain no PDF,
download nothing, and finish within the unchanged command budget. It is recorded
as an expected failed compiler attempt, not as a successful document build.

Linux network namespaces isolate network devices, protocol stacks, routing and
socket namespaces; see the [Linux network namespace manual](https://man7.org/linux/man-pages/man7/network_namespaces.7.html).
This is a network boundary for the trusted pinned compiler, not a general sandbox
for hostile executables or a claim that the host filesystem is inaccessible.

## Run the behavioral and native controls

The maintenance tests use real temporary file identities and explicitly mocked
compiler outcomes. They exercise malformed locks, source/package/font/tool
tampering, missing inputs, independent copies, changes during copying/building,
fresh failure receipts, first/second build failures, namespace controls, and
different output bytes. They do not claim native rendering evidence.

```sh
python -m unittest discover -s tests/maintenance -p test_replay_build.py -v

python tests/replay/qualify.py \
  --root . \
  --package-cache /absolute/path/to/prepared-package-cache \
  --output build/replay-native-controls
```

For the complete canonical gate with these native controls, run:

```sh
make verify VERIFY_ARGS="--replay-package-cache /absolute/path/to/prepared-package-cache"
```

The existing `Verify template and properties` CI job opts in with an explicit
cache prepared during the earlier online document checks. Local `make verify`
without this option records the replay section as unexecuted. An opted-in run
fails when namespace isolation is unsupported; it never substitutes an online
compile. Each run captures a fresh lock from the actual producer source and
uses a new output directory. The sidecar stays distinct from the 209 preceding
rendering/native/package cases and 64 policy-data scenarios. The replay helper
is the ninth measured coverage helper; both existing 80% floors remain.

The standalone command runs 11 bounded controls. Four are actual compiler attempts:
one discovery build, two independent replay builds, and the expected empty-cache
failure. Seven source/asset/package/font/lock/compiler/missing-package controls
reject before compilation. A final control appends a PDF comment to a successful
PDF, proves that the two extracted texts still match, and requires byte comparison
to reject it. The replay builds also run while ambient font, cache, timestamp and
timezone environment variables contain values different from the recipe.

Reports start in a failed state and retain actual commands, failures and output
identities. A successful pair reports `byte_replay_qualified: true` while keeping
release, complete-environment and cross-environment qualification false. Compile
receipts are versioned `isolated-typst-compile` objects; capture and pair receipts
are separately versioned `replay-lock-capture` and `bounded-two-build-replay`
objects. They remain separately scoped evidence rather than a future release or
repository-wide acceptance receipt.

## Remaining issue #20 work

This increment does not lock dynamic shared libraries, the entire Python
dependency installation, an OS/container image, every template feature/profile,
or dependency archive origin/authenticity. It records complete extracted package
trees, not upstream archive digests. It does not prove cross-environment semantic
repeatability, remove all optional imports, or establish platform-independent
binary equality.

Release bundle manifests, SBOM/provenance signing or attestation, tag publication,
same-run artifact transport, release dry-run rejection controls and rollback
remain separate work. The helper neither uploads nor publishes the copied source,
font or package bundle. Local native command logs and raw dependency captures
retain absolute paths and are not a reviewer-safe public manifest; prepare any
public evidence through the separate evidence/packaging process.

The [Typst text reference](https://typst.app/docs/reference/text/text/) documents
font selection and fallback, and the [datetime reference](https://typst.app/docs/reference/foundations/datetime/)
distinguishes explicit dates from `datetime.today`. This fixture chooses explicit
values. Normal draft convenience behavior has not been redefined as release
determinism.
