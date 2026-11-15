# UMTHESIS execution evidence

This branch preserves execution receipts separately from the tested source
trees. The executable qualification always belongs to the exact commit named
inside a receipt; this archive branch is not itself a qualified release.

Source and receiving results are separate. Failed and unexecuted observations
are retained, including the missing COR04 fixture in the first clean checkout.
Receipt hashes do not convert an unavailable check or artifact inspection into
a pass. GitHub Actions artifact links retain their configured retention limits.
