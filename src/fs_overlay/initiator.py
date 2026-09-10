"""Minimal cross-platform federation initiator with explicit capabilities."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .federation_adapters import FederationSigner, FederationTransport, KeyProvider
from .federation_control import BootstrapConfig, MinimalBootstrap
from .federation_protocol import FederationEnvelope


@dataclass(frozen=True)
class InitiatorCapabilities:
    platform: str
    features: tuple[str, ...] = ()


class MinimalInitiator:
    """Build signed protocol messages without discovering peers or hosts."""

    def __init__(self, config: BootstrapConfig, *, key_provider: KeyProvider, signer: FederationSigner,
                 transport: FederationTransport, capabilities: InitiatorCapabilities):
        self.config = config
        self.key_provider = key_provider
        self.signer = signer
        self.transport = transport
        self.capabilities = capabilities
        self._sequence = 0

    def build_advertisement(self, message_id: str, issued_ns: int, *, capabilities: tuple[str, ...] = ()) -> FederationEnvelope:
        self._sequence += 1
        key_id = self.key_provider.active_key_id(self.config.node_id)
        payload = {"platform": self.capabilities.platform,
                   "features": tuple(sorted(set(self.capabilities.features + capabilities))),
                   "protocol_version": self.config.protocol_version,
                   "public_key_fingerprint": self.key_provider.public_key_fingerprint(key_id)}
        unsigned = FederationEnvelope(self.config.node_id, message_id, "ADVERTISE", self._sequence, issued_ns, payload)
        signature = self.signer.sign(unsigned.unsigned_bytes(), key_id)
        return FederationEnvelope(unsigned.sender_node, unsigned.message_id, unsigned.message_type,
                                  unsigned.sequence, unsigned.issued_ns, unsigned.payload, signature)

    def send(self, envelope: FederationEnvelope, peer_node: str) -> None:
        # Transport owns framing; this layer owns only protocol semantics.
        self.transport.send(peer_node, envelope.unsigned_bytes())


def bootstrap(config_path: str | Path, root: str | Path, **kwargs) -> BootstrapConfig:
    return MinimalBootstrap(config_path).initialize(root=root, **kwargs)
