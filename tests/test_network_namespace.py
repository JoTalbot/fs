from fs_overlay.network_namespace import plan_network_namespace


def test_host_network_is_explicit():
    plan = plan_network_namespace(requested="host")
    assert plan.admitted
    assert "host-network" in plan.guarantees


def test_unknown_network_policy_fails_closed():
    plan = plan_network_namespace(requested="isolated")
    assert not plan.admitted
    assert "unsupported_network_policy" in plan.reasons


def test_deny_plan_does_not_claim_runtime_success():
    plan = plan_network_namespace(requested="deny")
    if plan.admitted:
        assert "network-namespace" in plan.guarantees
        assert "kernel_policy_may_reject_unprivileged_network_namespace" in plan.reasons
