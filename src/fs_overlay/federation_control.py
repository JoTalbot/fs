"""Explicit node identity, trust, federation reconciliation, and bootstrap primitives.

This module intentionally stops at the protocol boundary: it never opens sockets,
changes host configuration, or treats possession of an identifier as trust.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class NodeIdentity:
    node_id: str
    public_key_fingerprint: str
    created_ns: int
    protocol_version: int = 1

    def unsigned(self) -> dict[str, object]:
        return {"node_id": self.node_id, "public_key_fingerprint": self.public_key_fingerprint,
                "created_ns": self.created_ns, "protocol_version": self.protocol_version}

    def identity_hash(self) -> str:
        return hashlib.sha256(_canonical(self.unsigned())).hexdigest()


@dataclass(frozen=True)
class TrustEntry:
    node_id: str
    fingerprint: str
    approved: bool
    expires_ns: int | None = None
    reason: str = ""


class TrustStore:
    """Explicit allowlist. Unknown or expired identities are never trusted."""

    def __init__(self, entries: Iterable[TrustEntry] = ()) -> None:
        self.entries = {entry.node_id: entry for entry in entries}

    def admit(self, identity: NodeIdentity, *, now_ns: int | None = None) -> bool:
        entry = self.entries.get(identity.node_id)
        if entry is None or not entry.approved or entry.fingerprint != identity.public_key_fingerprint:
            return False
        now = time.time_ns() if now_ns is None else now_ns
        return entry.expires_ns is None or now < entry.expires_ns

    def add(self, entry: TrustEntry) -> None:
        current = self.entries.get(entry.node_id)
        if current is not None and current.fingerprint != entry.fingerprint:
            raise ValueError("identity fingerprint change requires explicit replacement")
        self.entries[entry.node_id] = entry

    def revoke(self, node_id: str, reason: str = "revoked") -> None:
        current = self.entries.get(node_id)
        if current is None:
            return
        self.entries[node_id] = TrustEntry(current.node_id, current.fingerprint, False, current.expires_ns, reason)


@dataclass(frozen=True)
class NodeAdvertisement:
    identity: NodeIdentity
    capabilities: tuple[str, ...]
    carrier_ids: tuple[str, ...] = ()
    observed_ns: int = 0
    signature: bytes | None = None

    def canonical_bytes(self) -> bytes:
        return _canonical({
            "identity": self.identity.unsigned(),
            "capabilities": tuple(sorted(set(self.capabilities))),
            "carrier_ids": tuple(sorted(set(self.carrier_ids))),
            "observed_ns": self.observed_ns,
        })

    def verify_signature(self, verifier: Callable[[bytes, bytes, str], bool] | None) -> bool:
        if verifier is None or self.signature is None:
            return False
        return verifier(self.canonical_bytes(), self.signature, self.identity.public_key_fingerprint)


class FederationDirectory:
    """Last-observation directory gated by explicit trust and optional signature verification."""

    def __init__(self, trust: TrustStore, verifier: Callable[[bytes, bytes, str], bool] | None = None):
        self.trust = trust
        self.verifier = verifier
        self.nodes: dict[str, NodeAdvertisement] = {}

    def observe(self, advertisement: NodeAdvertisement, *, now_ns: int | None = None) -> bool:
        if not self.trust.admit(advertisement.identity, now_ns=now_ns):
            return False
        if not advertisement.verify_signature(self.verifier):
            return False
        previous = self.nodes.get(advertisement.identity.node_id)
        if previous is not None and advertisement.observed_ns <= previous.observed_ns:
            return False
        self.nodes[advertisement.identity.node_id] = advertisement
        return True

    def available(self) -> tuple[NodeAdvertisement, ...]:
        return tuple(self.nodes[node_id] for node_id in sorted(self.nodes))


@dataclass(frozen=True)
class ReconciliationDecision:
    object_id: str
    source_node: str
    target_node: str
    action: str
    reason: str


class FederationReconciler:
    """Deterministically plans replica repair; execution is deliberately separate."""

    def __init__(self, directory: FederationDirectory):
        self.directory = directory

    def plan_repairs(self, object_id: str, *, present_on: Iterable[str], desired_copies: int = 2) -> tuple[ReconciliationDecision, ...]:
        if desired_copies <= 0:
            raise ValueError("desired_copies must be positive")
        present = sorted(set(present_on))
        trusted = {node.identity.node_id for node in self.directory.available()}
        sources = [node for node in present if node in trusted]
        if not sources:
            return ()
        targets = [node.identity.node_id for node in self.directory.available() if node.identity.node_id not in present]
        needed = max(0, desired_copies - len(present))
        return tuple(
            ReconciliationDecision(object_id, sources[0], target, "REPLICATE", "restore desired replica count")
            for target in sorted(targets)[:needed]
        )


@dataclass(frozen=True)
class BootstrapConfig:
    node_id: str
    root: str
    protocol_version: int = 1
    initialized_ns: int = 0


class MinimalBootstrap:
    """Smallest safe initiator: create only an explicitly selected FS root/config."""

    def __init__(self, config_path: str | Path):
        self.config_path = Path(config_path)

    def initialize(self, *, root: str | Path, node_id: str | None = None) -> BootstrapConfig:
        root_path = Path(root).expanduser().resolve()
        root_path.mkdir(parents=True, exist_ok=True)
        identity = node_id or secrets.token_hex(16)
        if not identity or "/" in identity or "\\" in identity:
            raise ValueError("invalid node id")
        config = BootstrapConfig(identity, str(root_path), initialized_ns=time.time_ns())
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".fs-bootstrap-", dir=self.config_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(asdict(config), handle, sort_keys=True, separators=(",", ":"))
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.config_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return config

    def load(self) -> BootstrapConfig:
        raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        return BootstrapConfig(str(raw["node_id"]), str(raw["root"]), int(raw.get("protocol_version", 1)),
                               int(raw["initialized_ns"]))
