#!/usr/bin/env python3
"""Dependency-free consumer for published FS federation conformance vectors.

This intentionally does not import fs_overlay. It verifies published data using
only the declared protocol canonicalization rules and SHA-256.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


SUPPORTED_PROTOCOL_VERSION = 1


def canonical_envelope(vector: dict[str, object]) -> bytes:
    envelope = vector.get("envelope")
    if not isinstance(envelope, dict):
        raise ValueError("envelope must be an object")

    canonicalization = vector.get("canonicalization")
    if not isinstance(canonicalization, dict):
        raise ValueError("canonicalization must be an object")
    if canonicalization.get("format") != "json":
        raise ValueError("unsupported canonicalization format")
    if canonicalization.get("sort_keys") is not True:
        raise ValueError("sort_keys must be true")
    if canonicalization.get("separators") != [",", ":"]:
        raise ValueError("unsupported separators")
    if canonicalization.get("ensure_ascii") is not False:
        raise ValueError("ensure_ascii must be false")
    if canonicalization.get("signature_included") is not False:
        raise ValueError("signed canonical vectors are unsupported")

    return json.dumps(
        envelope,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def validate(path: Path) -> bool:
    vector = json.loads(path.read_text(encoding="utf-8"))
    if vector.get("protocol_version") != SUPPORTED_PROTOCOL_VERSION:
        raise ValueError(f"unsupported protocol version in {path.name}")
    if not isinstance(vector.get("vector_id"), str) or not vector["vector_id"]:
        raise ValueError(f"missing vector_id in {path.name}")

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
    failed = []
    for path in paths:
        try:
            if not validate(path):
                failed.append(path.name)
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(f"FAIL: {path.name}: {exc}")
            failed.append(path.name)
    if failed:
        print(f"FAIL: {', '.join(failed)}")
        return 1
    print(f"PASS: {len(paths)} vector(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
