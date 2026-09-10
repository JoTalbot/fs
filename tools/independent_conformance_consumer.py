#!/usr/bin/env python3
"""Dependency-free consumer for published FS federation conformance vectors.

This intentionally does not import fs_overlay. It verifies the published data
using only the protocol's declared canonical JSON rules and SHA-256.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical_envelope(vector: dict[str, object]) -> bytes:
    envelope = vector["envelope"]
    if not isinstance(envelope, dict):
        raise ValueError("envelope must be an object")
    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def validate(path: Path) -> bool:
    vector = json.loads(path.read_text(encoding="utf-8"))
    actual = hashlib.sha256(canonical_envelope(vector)).hexdigest()
    expected = vector.get("expected_sha256")
    return isinstance(expected, str) and actual == expected


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    vector_dir = root / "conformance" / "v1"
    paths = sorted(vector_dir.glob("*.json"))
    if not paths:
        print("no conformance vectors found")
        return 2
    failed = [path.name for path in paths if not validate(path)]
    if failed:
        print(f"FAIL: {', '.join(failed)}")
        return 1
    print(f"PASS: {len(paths)} vector(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
