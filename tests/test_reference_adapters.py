from fs_overlay.reference_adapters import HmacReferenceSigner, InMemoryNodeAdmission, MemoryKeyProvider


def test_hmac_reference_signer_round_trip_and_tamper_rejection() -> None:
    signer = HmacReferenceSigner({"k1": b"test-key"})
    payload = b"envelope"
    signature = signer.sign(payload, "k1")
    assert signer.verify(payload, signature, "k1")
    assert not signer.verify(b"tampered", signature, "k1")
    assert not signer.verify(payload, signature, "missing")


def test_memory_key_provider_is_explicit_and_deterministic() -> None:
    provider = MemoryKeyProvider({"k1": b"key"}, {"node-a": "k1"})
    assert provider.active_key_id("node-a") == "k1"
    assert provider.public_key_fingerprint("k1")


def test_node_admission_requires_matching_fingerprint_and_revocation() -> None:
    admission = InMemoryNodeAdmission()
    assert not admission.is_admitted("node-a", "fp")
    assert admission.admit("node-a", "fp")
    assert admission.is_admitted("node-a", "fp")
    assert not admission.is_admitted("node-a", "other")
    admission.revoke("node-a", "test")
    assert not admission.is_admitted("node-a", "fp")
    assert not admission.admit("node-a", "fp")
