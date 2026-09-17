from fs_overlay.backend_contract import BACKEND_CONTRACT_VERSION, LINUX_CGROUP_V2_CONTRACT
from fs_overlay.capability_negotiation import CapabilitySet
from fs_overlay.semantic_abi import SemanticABIAdapter


def test_semantic_abi_adapter_requires_contract_and_feature_compatibility():
    adapter = SemanticABIAdapter(
        LINUX_CGROUP_V2_CONTRACT,
        CapabilitySet(1, frozenset({"resource.cpu", "resource.memory"})),
    )
    assert adapter.supports(contract_version=BACKEND_CONTRACT_VERSION, required_features=frozenset({"resource.cpu"}))
    assert not adapter.supports(contract_version=BACKEND_CONTRACT_VERSION + 1)
    assert not adapter.supports(contract_version=BACKEND_CONTRACT_VERSION, required_features=frozenset({"resource.network"}))


def test_semantic_abi_adapter_canonical_is_deterministic():
    adapter = SemanticABIAdapter(
        LINUX_CGROUP_V2_CONTRACT,
        CapabilitySet(1, frozenset({"b", "a"})),
    )
    assert adapter.canonical()["features"] == ["a", "b"]
    assert adapter.canonical()["backend_id"] == LINUX_CGROUP_V2_CONTRACT.backend_id
