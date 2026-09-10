from fs_overlay.capabilities import discover_local_capabilities


def test_local_capability_discovery_has_safe_baseline():
    capabilities = discover_local_capabilities()
    assert capabilities.cpu_cores >= 1
    assert capabilities.platform
    assert capabilities.architecture
    payload = capabilities.to_dict()
    assert payload["cpu"]["cores"] >= 1
