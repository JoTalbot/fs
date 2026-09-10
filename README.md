# FS Overlay Storage

FS is a user-controlled, failure-tolerant storage overlay that places encrypted container fragments into explicitly configured carrier files while preserving the host file's normal semantics.

> **Safety boundary:** FS never silently scans or modifies the whole operating system. Carrier roots are explicit configuration, protected/system paths are denied, and every mutation is opt-in and auditable.

## Concept

```text
container data
    -> compress (optional)
    -> encrypt/authenticate
    -> chunk
    -> erasure-code
    -> place shards into approved carriers
    -> verify

carrier loss
    -> audit
    -> reconstruct
    -> choose approved replacement
    -> repair redundancy
```

The design uses erasure coding rather than relying on identical copies. A container can therefore survive loss of multiple carrier fragments, subject to its configured `data_shards` / `parity_shards` policy.

## Repository layout

- `docs/ARCHITECTURE.md` - normative architecture and invariants
- `docs/FORMAT.md` - FSOV carrier and manifest format
- `src/fs_overlay/` - Python reference implementation scaffold
- `tests/` - unit/integration test plan
- `config.example.toml` - explicit-root configuration example

## Non-goals

- stealth persistence
- modification of arbitrary OS/system files
- bypassing access controls
- pretending arbitrary file formats remain valid after unsafe mutation
- a single central metadata database as a recovery dependency

## Initial implementation status

The repository currently contains the architecture and a safe reference scaffold. Production cryptography and Reed-Solomon implementation must be supplied and tested before real data is stored.
