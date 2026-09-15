# Agent step: workspace transfer recovery evidence matrix

Date: 2026-09-15  
Repository: `JoTalbot/fs`  
Branch: `main`

## Result

Recovery qualification was expanded from individual regressions to a small evidence matrix covering the mandatory proof bits for automatic commit and abort decisions.

For `COMMIT_PROVEN`, all of the following are mandatory:

- destination matches the expected snapshot;
- destination identity/content was independently verified;
- mutation completion is evidenced;
- staging is absent.

For `ABORT_PROVEN`, all of the following are mandatory:

- destination is absent;
- rollback safety is independently evidenced;
- staging is absent;
- source preservation has already passed the global recovery guard.

Missing any mandatory proof bit remains `MANUAL_REVIEW`. An absent destination combined with `mutation_complete=True` is explicitly contradictory and also remains `MANUAL_REVIEW`.

## Change

- Test commit `6a2c0488c84e90ddb53f0c20cb240f3555ec13e9` adds parametrized coverage for incomplete matching-destination commit evidence and incomplete absent-destination rollback evidence.

No production executor was introduced and no host filesystem mutation is performed by the recovery planner.

## Validation boundary

GitHub Actions is authoritative because no local checkout/test runner is available in this session. The change must pass the existing full CI matrix before it is treated as qualified.

## Next step

Continue checking journal reopen/replay invariants and the interaction between journal recovery candidates, recovery audit replay, and evidence-derived decisions. Keep recovery decisions separate from authority and actual filesystem mutation.
