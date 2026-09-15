# Agent Step: Revocation Concurrency Qualification

Date: 2026-09-15
Repository: `JoTalbot/fs`
Branch: `main`

## Change

The durable authority revocation registry was hardened against cross-process stale-state races.

- Registry replay, mutation, and read decisions are serialized with the existing OS-level `FileAdmissionCoordinator` lock.
- Writers refresh the durable journal while holding the lock before allocating the next sequence number.
- Reads refresh from the durable journal while holding the same lock, so a long-lived process does not rely on stale revocation state after another process revokes an authority.
- The lock is retained and is never treated as a stale lock that may be stolen.
- The implementation remains fail-closed on malformed or tampered durable state.

## Qualification

A multiprocessing regression test starts two independent registry instances against the same journal and revokes different authority IDs concurrently. It requires both operations to succeed, produces contiguous sequence numbers `[1, 2]`, and verifies both records after reopening the registry.

Implementation commit: `58f8d1b98d4d475c1b0135e6d781bdc72eac41aa`
Test commit: `72f816502e6db7800786d2680ec04846f304afe7`

GitHub Actions run `#517` (`34955618776`) completed successfully across all 18 configured jobs, including Python tests on Ubuntu/Windows/macOS for Python 3.11-3.13 and candidate crypto-provider qualification jobs.

## Boundary

This qualifies local cross-process serialization and restart-safe reads for the revocation registry. It does not establish authenticated principal/issuer identity, trust roots, key lifecycle, authenticated transport, or production cryptographic security.

V1 therefore remains not production-ready, and host filesystem mutation remains disabled.

## Next step

Define the authenticated principal/issuer verification boundary, trust-root model, and key lifecycle without storing secret material in repository state. Then bind authenticated provenance to policy authorization and durable revocation semantics before considering any host filesystem executor.
