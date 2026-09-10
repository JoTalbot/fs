#!/usr/bin/env python3
"""Dependency-free validator for published admission-negative semantics.

This validates the machine-readable contract without importing fs_overlay. It
checks that every required negative case is explicit, fail-closed, and assigned
to one documented admission gate/reason pair. Crypto verification itself stays
provider-specific and is covered by implementation-level tests.
"""
from __future__ import annotations

import json
from pathlib import Path

REQUIRED = {
    "changed-payload": ("signature", "invalid_signature"),
    "changed-sender": ("signature", "invalid_signature"),
    "changed-sequence": ("signature", "invalid_signature"),
    "duplicate-message-id": ("replay", "duplicate_message_id"),
    "sequence-rollback": ("replay", "non_increasing_sequence"),
    "stale-timestamp": ("freshness", "stale_timestamp"),
    "future-timestamp": ("freshness", "future_timestamp"),
    "missing-signature": ("signature", "missing_signature"),
    "unknown-or-revoked-key": ("trust", "untrusted_key"),
    "fingerprint-mismatch": ("trust", "fingerprint_mismatch"),
}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    path = root / "conformance" / "v1" / "admission-negative-v1.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("protocol_version") != 1:
            raise ValueError("unsupported protocol version")
        cases = data.get("cases")
        if not isinstance(cases, list):
            raise ValueError("cases must be a list")
        seen = set()
        for case in cases:
            if not isinstance(case, dict):
                raise ValueError("case must be an object")
            case_id = case.get("case_id")
            if case_id in seen:
                raise ValueError(f"duplicate case: {case_id}")
            seen.add(case_id)
            if case_id not in REQUIRED:
                raise ValueError(f"unexpected case: {case_id}")
            gate, reason = REQUIRED[case_id]
            if case.get("gate") != gate or case.get("reason") != reason:
                raise ValueError(f"incorrect contract for {case_id}")
            if case.get("expected") != "reject":
                raise ValueError(f"case is not fail-closed: {case_id}")
            if not isinstance(case.get("mutation"), str) or not case["mutation"]:
                raise ValueError(f"missing mutation: {case_id}")
        if seen != set(REQUIRED):
            raise ValueError(f"missing cases: {sorted(set(REQUIRED) - seen)}")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"FAIL: {path.name}: {exc}")
        return 1
    print(f"PASS: {len(cases)} admission-negative case(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
