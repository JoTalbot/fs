from fs_overlay.replication_policy import ReplicaCandidate, ReplicaPolicy


def test_policy_prefers_new_failure_domains_deterministically() -> None:
    candidates = [
        ReplicaCandidate("b", "rack-1", capacity_available=100, locality=10),
        ReplicaCandidate("c", "rack-2", capacity_available=50, locality=5),
        ReplicaCandidate("d", "rack-3", capacity_available=10, locality=1),
    ]
    assert ReplicaPolicy().plan(candidates, present_on={"a"}, desired_copies=3) == ("b", "c")


def test_policy_fills_same_domain_when_diversity_is_exhausted() -> None:
    candidates = [
        ReplicaCandidate("b", "rack-1", capacity_available=100),
        ReplicaCandidate("c", "rack-1", capacity_available=50),
    ]
    assert ReplicaPolicy().plan(candidates, present_on={"a"}, desired_copies=3) == ("b", "c")


def test_policy_recovers_unhealthy_present_replica() -> None:
    candidates = [
        ReplicaCandidate("a", "rack-1", healthy=False),
        ReplicaCandidate("b", "rack-2", capacity_available=100),
        ReplicaCandidate("c", "rack-3", capacity_available=50),
    ]
    assert ReplicaPolicy().plan(candidates, present_on={"a"}, desired_copies=2) == ("b", "c")


def test_policy_keeps_unknown_present_copy_count_compatibility() -> None:
    candidates = [
        ReplicaCandidate("b", "rack-2", capacity_available=100),
        ReplicaCandidate("c", "rack-3", capacity_available=50),
    ]
    assert ReplicaPolicy().plan(candidates, present_on={"unknown"}, desired_copies=2) == ("b",)


def test_policy_is_invariant_to_candidate_input_order() -> None:
    candidates = [
        ReplicaCandidate("c", "rack-2", capacity_available=50, locality=5),
        ReplicaCandidate("a", "rack-1", healthy=False, capacity_available=1000),
        ReplicaCandidate("d", "rack-3", capacity_available=10, locality=1),
        ReplicaCandidate("b", "rack-1", capacity_available=100, locality=10),
    ]
    policy = ReplicaPolicy()
    expected = ("b", "c", "d")
    assert policy.plan(candidates, present_on={"a"}, desired_copies=3) == expected
    assert policy.plan(reversed(candidates), present_on={"a"}, desired_copies=3) == expected


def test_policy_never_selects_unhealthy_or_present_targets() -> None:
    candidates = [
        ReplicaCandidate("a", "rack-1", healthy=True, capacity_available=999),
        ReplicaCandidate("b", "rack-2", healthy=False, capacity_available=999),
        ReplicaCandidate("c", "rack-3", healthy=True, capacity_available=10),
    ]
    assert ReplicaPolicy().plan(candidates, present_on={"a"}, desired_copies=2) == ("c",)


def test_policy_does_not_use_negative_capacity_targets() -> None:
    candidates = [
        ReplicaCandidate("b", "rack-1", capacity_available=-1),
        ReplicaCandidate("c", "rack-2", capacity_available=0),
    ]
    assert ReplicaPolicy().plan(candidates, present_on=set(), desired_copies=1) == ("c",)
