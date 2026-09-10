from fs_overlay.self_healing import ReplicaObservation, SelfHealingPlanner


def obs(node, present, digest="abc", healthy=True):
    return ReplicaObservation(node, "obj", present, digest if present else None, healthy)


def test_planner_selects_deterministic_trusted_source_and_targets() -> None:
    observations = [obs("node-c", False), obs("node-a", True), obs("node-b", False)]
    actions = SelfHealingPlanner().plan("obj", observations, desired_copies=2, trusted_nodes={"node-a", "node-b", "node-c"})
    assert [(item.source_node, item.target_node) for item in actions] == [("node-a", "node-b")]


def test_planner_ignores_untrusted_source_and_unhealthy_target() -> None:
    observations = [obs("node-a", True), obs("node-b", False, healthy=False), obs("node-c", False)]
    actions = SelfHealingPlanner().plan("obj", observations, desired_copies=2, trusted_nodes={"node-a", "node-c"})
    assert [(item.source_node, item.target_node) for item in actions] == [("node-a", "node-c")]


def test_planner_requires_verified_present_source() -> None:
    observations = [obs("node-a", True, digest=None), obs("node-b", False)]
    assert SelfHealingPlanner().plan("obj", observations, desired_copies=2, trusted_nodes={"node-a", "node-b"}) == ()


def test_planner_does_not_repair_when_replica_count_is_satisfied() -> None:
    observations = [obs("node-a", True), obs("node-b", True), obs("node-c", False)]
    assert SelfHealingPlanner().plan("obj", observations, desired_copies=2, trusted_nodes={"node-a", "node-b", "node-c"}) == ()
