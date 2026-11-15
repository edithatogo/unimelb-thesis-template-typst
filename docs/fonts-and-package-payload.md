# Fonts and distributable payload

The source font tree remains intact. At source
`3086863a1ddc3a699d172a10132a183b22979192`, its Git tree still contains **222 files and
72,805,272 bytes**. [The inventory](package-font-inventory.json) records every
path, byte count and Git blob identity. These are Git object hashes, not a new
claim of runtime SHA-256 measurement for every font.

| Source format or support file | Files | Bytes |
| --- | ---: | ---: |
| OTF | 76 | 19,228,672 |
| TTF | 76 | 19,502,716 |
| WOFF | 32 | 5,074,620 |
| WOFF2 | 28 | 2,480,072 |
| ZIP-named files | 4 | 26,503,066 |
| Licence, README, CSS and metadata | 6 | 16,126 |
| **Total** | **222** | **72,805,272** |

The earlier actual audit identified Source Serif Pro 3.001 and Source Serif
4.005 assets in multiple formats and archived distributions, including variable
instances. It also found that `fraunces.zip` contained HTML and
`source-serif-4.005R.zip` contained a nine-byte `Not Found` response.
Those original source bytes and observations are retained. The malformed files
must not be treated as installed fonts or reproducible download sources.

## Distribution decision

The explicit local archive and the six-file author starter include **zero font
files**. This separates 72.8 MB of optional source assets from the downloadable
runtime/starter without deleting them or changing their rights. Native archive
and starter byte counts must be reported from the new executed candidate.

The official [resource guidance](https://github.com/typst/packages/blob/76fcf18ad1d1f5fed315dcca23c64d8a0c62f814/docs/resources.md)
does not permit distributing fonts inside registry packages/templates. For
additional fonts, authors need an appropriate installation or explicit font
path. The retained Source Serif metadata identifies its
[upstream repository](https://github.com/adobe-fonts/source-serif-pro). Review
the particular release, licence and source bytes used before installing it.

The retained licence files and package metadata remain authoritative for their
assets. For example, the existing Source Serif Pro package metadata declares
OFL-1.1; this does not convert those fonts to the repository's Apache-2.0 code
licence. The package/starter keeps the existing code licence and the original
synthetic SVG's licence. No third-party asset is bulk-relicensed.

## Theme and evidence boundary

The existing `unimelb`, `classic` and `modern` theme lists are unchanged.
A requested family name in those lists does not establish that its font files
are installed or that every listed weight/script is supported.

The new starter selects `classic`. The historical native packaging prototype
observed embedded Libertinus Serif Regular, Bold and Italic with system fonts
disabled. Its retained unknown-font warnings were not suppressed. The new
candidate must report its own observed font names/embedding and environment
flags; it cannot inherit the historical PDF result.

The bounded native gate checks the synthetic Latin starter. It does not
qualify per-face font hashes, all themes, all weights, CJK/multilingual coverage,
maths coverage or complete rendering replay. Those require their own explicit
fixtures and qualified font inputs. The separate native-evidence increment
likewise keeps per-face font source bytes and full environment replay open.
