# Thesis evidence profile v1

This directory owns the thesis-specific request/status sidecar profile. Its
manifest pins exactly four machine files: request schema, sidecar schema,
adapter registry and source ledger. `scripts/requirement_evidence.py` pins that
manifest's SHA-256.

The central wrapper schema is reused from the existing canonical contract
snapshot; it is not copied or redefined here. See
[the guide](../../docs/requirement-evidence.md) for the central ownership and
trust boundaries.

The profile can produce only partial or failed whole-programme results.
Unregistered sidecars remain unsupported, missing artifact/configuration/human
provenance is not invented, and the bundle is not blind-safe.
