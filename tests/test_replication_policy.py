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
