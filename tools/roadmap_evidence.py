"""Evidence registry for ``docs/ROADMAP.md`` completion claims."""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPOSITORY_ROOT / "docs" / "ROADMAP.md"


@dataclass(frozen=True)
class RoadmapEvidence:
    item: str
    modules: tuple[str, ...]
    symbols: tuple[str, ...]
    tests: tuple[str, ...]


ROADMAP_EVIDENCE: tuple[RoadmapEvidence, ...] = (
    RoadmapEvidence("manifest model", ("src/fs_overlay/storage_engine.py",), ("Manifest",), ("tests/test_storage_primitives.py",)),
    RoadmapEvidence("deterministic chunker", ("src/fs_overlay/storage_engine.py",), ("DeterministicChunker",), ("tests/test_storage_primitives.py",)),
    RoadmapEvidence("authenticated encryption interface", ("src/fs_overlay/storage_engine.py",), ("AuthenticatedEncryption", "HMACIntegrityEnvelope"), ("tests/test_storage_primitives.py", "tests/test_storage_crypto_boundary.py")),
    RoadmapEvidence("erasure-coding interface", ("src/fs_overlay/storage_engine.py",), ("ErasureCoder",), ("tests/test_storage_primitives.py",)),
    RoadmapEvidence("carrier adapter interface", ("src/fs_overlay/carrier.py",), ("CarrierAdapter", "LocalDirectoryCarrier"), ("tests/test_carrier.py",)),
    RoadmapEvidence("atomic append protocol", ("src/fs_overlay/storage_engine.py",), ("AppendJournal",), ("tests/test_append_journal_durability.py",)),
    RoadmapEvidence("inventory database with redundant recovery records", ("src/fs_overlay/storage_engine.py",), ("Inventory",), ("tests/test_storage_primitives.py",)),
    RoadmapEvidence("content-addressed object store", ("src/fs_overlay/storage_engine.py",), ("ContentAddressedStore",), ("tests/test_storage_engine.py",)),
    RoadmapEvidence("Merkle DAG implementation", ("src/fs_overlay/storage_engine.py",), ("MerkleDAG",), ("tests/test_storage_primitives.py",)),
    RoadmapEvidence("event log", ("src/fs_overlay/event_log.py",), ("EventLog",), ("tests/test_event_log_recovery.py",)),
    RoadmapEvidence("audit command", ("src/fs_overlay/storage_engine.py", "src/fs_overlay/cli.py"), ("LocalStorageEngine", "main"), ("tests/test_cli.py", "tests/test_storage_integrity.py")),
    RoadmapEvidence("recovery command", ("src/fs_overlay/storage_engine.py", "src/fs_overlay/cli.py"), ("LocalStorageEngine", "main"), ("tests/test_cli.py", "tests/test_storage_transaction_recovery.py")),
    RoadmapEvidence("transaction engine implementation", ("src/fs_overlay/storage_engine.py",), ("StorageTransaction",), ("tests/test_storage_transaction_recovery.py", "tests/test_storage_transaction_commit_failure.py")),
    RoadmapEvidence("state/reconciliation engine implementation", ("src/fs_overlay/state_primitives.py", "src/fs_overlay/federation_control.py"), ("reconcile", "ControlLoopResult", "safe_stop", "FederationReconciler", "ReconciliationDecision"), ("tests/test_state_primitives.py", "tests/test_federation_control.py")),
    RoadmapEvidence("resource ownership/lease primitives", ("src/fs_overlay/state_primitives.py", "src/fs_overlay/resource_control.py"), ("Lease", "ResourceLease"), ("tests/test_state_primitives.py", "tests/test_resource_control.py")),
    RoadmapEvidence("causal event metadata", ("src/fs_overlay/event_log.py",), ("EventLog",), ("tests/test_event_log_recovery.py",)),
    RoadmapEvidence("universal object contract implementation", ("src/fs_overlay/state_primitives.py",), ("ObjectContract",), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("provenance records", ("src/fs_overlay/state_primitives.py",), ("ProvenanceRecord",), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("dependency graph primitives", ("src/fs_overlay/state_primitives.py",), ("DependencyGraph", "Dependency"), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("knowledge record primitives", ("src/fs_overlay/state_primitives.py",), ("KnowledgeRecord",), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("decision record primitives", ("src/fs_overlay/state_primitives.py",), ("DecisionRecord",), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("world-state snapshot primitives", ("src/fs_overlay/state_primitives.py",), ("WorldStateSnapshot",), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("unified control-loop primitives", ("src/fs_overlay/state_primitives.py",), ("ControlLoopResult", "safe_stop"), ("tests/test_state_primitives.py",)),
    RoadmapEvidence("capability negotiation", ("src/fs_overlay/capability_negotiation.py",), ("CapabilitySet", "NegotiatedCapabilities", "negotiate"), ("tests/test_capability_negotiation.py", "tests/test_capability_negotiation_extra.py")),
    RoadmapEvidence("local node identity store", ("src/fs_overlay/node_identity_store.py",), ("LocalNodeIdentityStore", "SCHEMA_VERSION"), ("tests/test_node_identity_store.py",)),
    RoadmapEvidence("versioned backend contracts", ("src/fs_overlay/backend_contract.py",), ("BackendContract", "BACKEND_CONTRACT_VERSION"), ("tests/test_backend_contract.py",)),
    RoadmapEvidence("hardware abstraction adapter", ("src/fs_overlay/hardware_profile.py",), ("HardwareCapabilityAdapter", "HardwareProfile"), ("tests/test_hardware_profile.py",)),
    RoadmapEvidence("hardware capability fingerprint", ("src/fs_overlay/hardware_profile.py",), ("hardware_capability_fingerprint",), ("tests/test_hardware_profile.py",)),
    RoadmapEvidence("platform time adapter", ("src/fs_overlay/time_fabric.py",), ("PlatformTimeAdapter",), ("tests/test_time_fabric.py",)),
    RoadmapEvidence("monotonic/logical time adapter", ("src/fs_overlay/time_fabric.py",), ("LogicalClock",), ("tests/test_time_fabric.py",)),
    RoadmapEvidence("semantic ABI adapters", ("src/fs_overlay/semantic_abi.py",), ("SemanticABIAdapter",), ("tests/test_semantic_abi.py",)),
    RoadmapEvidence("semantic verification adapters", ("src/fs_overlay/semantic_verification.py",), ("SemanticVerificationAdapter",), ("tests/test_semantic_verification.py",)),
    RoadmapEvidence("Genesis bootstrap executable", ("src/fs_overlay/cli.py",), ("main",), ("tests/test_cli.py",)),
    RoadmapEvidence("structured JSON logs", ("src/fs_overlay/json_logging.py",), ("JsonLogFormatter", "configure_json_logging", "log_event"), ("tests/test_json_logging.py",)),
    RoadmapEvidence("local IPC control API", ("src/fs_overlay/ipc.py",), ("UnixSocketServer", "UnixSocketTransport"), ("tests/test_ipc.py",)),
    RoadmapEvidence("foreground runtime", ("src/fs_overlay/foreground_runtime.py",), ("ForegroundRuntime",), ("tests/test_foreground_runtime.py",)),
    RoadmapEvidence("workspace registration", ("src/fs_overlay/workspace_registry.py",), ("WorkspaceRegistry", "WorkspaceRecord"), ("tests/test_workspace_registry.py",)),
    RoadmapEvidence("workspace health state", ("src/fs_overlay/workspace_registry.py", "src/fs_overlay/workspace_state.py"), ("WorkspaceHealth", "workspace_health", "WorkspaceState"), ("tests/test_workspace_registry.py", "tests/test_workspace_state.py")),
    RoadmapEvidence("migration/import workflow", ("src/fs_overlay/workspace_migration.py",), ("plan_import", "plan_export", "plan_registered_migration"), ("tests/test_workspace_migration.py",)),
    RoadmapEvidence("workspace snapshots", ("src/fs_overlay/storage_resilience.py",), ("Snapshot", "SnapshotStore"), ("tests/test_snapshot_provenance.py",)),
    RoadmapEvidence("transactional rollback", ("src/fs_overlay/storage_engine.py",), ("StorageTransaction",), ("tests/test_storage_transaction_recovery.py",)),
    RoadmapEvidence("self-healing", ("src/fs_overlay/self_healing.py",), ("SelfHealingPlanner", "ReplicaObservation"), ("tests/test_self_healing.py",)),
    RoadmapEvidence("carrier quarantine", ("src/fs_overlay/storage_resilience.py",), ("QuarantineLedger", "QuarantineRecord"), ("tests/test_storage_resilience.py", "tests/test_quarantine_ledger_json_boundary.py")),
    RoadmapEvidence("failure-domain aware placement", ("src/fs_overlay/storage_resilience.py",), ("PlacementPlanner", "CarrierState"), ("tests/test_storage_resilience.py",)),
    RoadmapEvidence("power-loss recovery tests", ("src/fs_overlay/storage_engine.py",), ("ContentAddressedStore", "AppendJournal", "StorageTransaction"), ("tests/test_storage_integrity.py", "tests/test_storage_transaction_commit_failure.py", "tests/test_append_journal_durability.py")),
    RoadmapEvidence("corruption/fuzz tests", ("src/fs_overlay/storage_engine.py",), ("Manifest", "AppendJournal", "JournalCorruption"), ("tests/test_storage_corruption_fuzz.py",)),
    RoadmapEvidence("metadata redundancy", ("src/fs_overlay/metadata_redundancy.py",), ("MetadataRedundancy", "MetadataReplica", "MetadataCorruption"), ("tests/test_metadata_redundancy.py",)),
    RoadmapEvidence("Reed-Solomon implementation or audited dependency", ("src/fs_overlay/reed_solomon.py",), ("ReedSolomonCoder",), ("tests/test_reed_solomon.py",)),
    RoadmapEvidence("workspace disaster recovery", ("src/fs_overlay/workspace_disaster_recovery.py",), ("WorkspaceDisasterRecovery", "WorkspaceRecoveryResult", "WorkspaceRecoveryError"), ("tests/test_workspace_disaster_recovery.py",)),
    RoadmapEvidence("recovery graph", ("src/fs_overlay/storage_resilience.py",), ("RecoveryGraph", "RecoveryNode"), ("tests/test_storage_resilience.py",)),
    RoadmapEvidence("deterministic recovery planner", ("src/fs_overlay/storage_resilience.py",), ("PlacementPlanner", "recovery_state"), ("tests/test_storage_resilience.py",)),
    RoadmapEvidence("transactional recovery journal", ("src/fs_overlay/storage_engine.py",), ("AppendJournal", "StorageTransaction"), ("tests/test_storage_transaction_recovery.py", "tests/test_append_journal_durability.py")),
    RoadmapEvidence("failure injection suite", ("src/fs_overlay/failure_injection.py",), ("FailureInjector", "InjectedFailure"), ("tests/test_failure_injection.py",)),
)


def _top_level_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _roadmap_items(text: str) -> dict[str, bool]:
    items: dict[str, bool] = {}
    for line in text.splitlines():
        stripped = line.strip()
        for marker, checked in (("- [x] ", True), ("- [ ] ", False)):
            if stripped.startswith(marker):
                items[stripped[len(marker):].strip()] = checked
                break
    return items


def check() -> list[str]:
    problems: list[str] = []
    roadmap_items = _roadmap_items(ROADMAP_PATH.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for entry in ROADMAP_EVIDENCE:
        if entry.item in seen:
            problems.append(f"{entry.item}: duplicate evidence entry")
        seen.add(entry.item)
        checked = roadmap_items.get(entry.item)
        if checked is None:
            problems.append(f"{entry.item}: not present in {ROADMAP_PATH.name}")
        elif checked is False:
            problems.append(f"{entry.item}: evidence registered but roadmap item is unchecked")
        defined: set[str] = set()
        for module in entry.modules:
            module_path = REPOSITORY_ROOT / module
            if not module_path.is_file():
                problems.append(f"{entry.item}: missing module {module}")
                continue
            defined |= _top_level_names(module_path.read_text(encoding="utf-8"))
        for symbol in entry.symbols:
            if symbol not in defined:
                problems.append(f"{entry.item}: no listed module defines {symbol}")
        for test in entry.tests:
            test_path = REPOSITORY_ROOT / test
            if not test_path.is_file():
                problems.append(f"{entry.item}: missing test file {test}")
                continue
            source = test_path.read_text(encoding="utf-8")
            if not any(symbol in source for symbol in entry.symbols):
                problems.append(f"{entry.item}: {test} references none of {', '.join(entry.symbols)}")
    return problems


def main() -> int:
    problems = check()
    if problems:
        print(f"roadmap evidence check failed with {len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(f"roadmap evidence check passed: {len(ROADMAP_EVIDENCE)} items bound to modules and tests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
