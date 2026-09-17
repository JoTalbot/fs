"""Evidence registry for ``docs/ROADMAP.md`` completion claims.

A roadmap checkbox is a claim that something exists and is exercised. This tool
makes that claim checkable: every registered roadmap item must name the modules
that define it, the top-level symbols that constitute it, and at least one test
file that references those symbols.

Usage::

    python tools/roadmap_evidence.py

Exits non-zero and prints every inconsistency, so the check can run in CI and in
an agent's local loop.
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
ROADMAP_PATH = REPOSITORY_ROOT / "docs" / "ROADMAP.md"


@dataclass(frozen=True)
class RoadmapEvidence:
    """One roadmap item bound to verifiable repository evidence."""

    item: str
    modules: tuple[str, ...]
    symbols: tuple[str, ...]
    tests: tuple[str, ...]


ROADMAP_EVIDENCE: tuple[RoadmapEvidence, ...] = (
    # Phase 1 - local reference engine
    RoadmapEvidence(item="manifest model", modules=("src/fs_overlay/storage_engine.py",), symbols=("Manifest",), tests=("tests/test_storage_primitives.py",)),
    RoadmapEvidence(item="deterministic chunker", modules=("src/fs_overlay/storage_engine.py",), symbols=("DeterministicChunker",), tests=("tests/test_storage_primitives.py",)),
    RoadmapEvidence(item="authenticated encryption interface", modules=("src/fs_overlay/storage_engine.py",), symbols=("AuthenticatedEncryption", "HMACIntegrityEnvelope"), tests=("tests/test_storage_primitives.py", "tests/test_storage_crypto_boundary.py")),
    RoadmapEvidence(item="erasure-coding interface", modules=("src/fs_overlay/storage_engine.py",), symbols=("ErasureCoder",), tests=("tests/test_storage_primitives.py",)),
    RoadmapEvidence(item="carrier adapter interface", modules=("src/fs_overlay/carrier.py",), symbols=("CarrierAdapter", "LocalDirectoryCarrier"), tests=("tests/test_carrier.py",)),
    RoadmapEvidence(item="atomic append protocol", modules=("src/fs_overlay/storage_engine.py",), symbols=("AppendJournal",), tests=("tests/test_append_journal_durability.py",)),
    RoadmapEvidence(item="inventory database with redundant recovery records", modules=("src/fs_overlay/storage_engine.py",), symbols=("Inventory",), tests=("tests/test_storage_primitives.py",)),
    RoadmapEvidence(item="content-addressed object store", modules=("src/fs_overlay/storage_engine.py",), symbols=("ContentAddressedStore",), tests=("tests/test_storage_engine.py",)),
    RoadmapEvidence(item="Merkle DAG implementation", modules=("src/fs_overlay/storage_engine.py",), symbols=("MerkleDAG",), tests=("tests/test_storage_primitives.py",)),
    RoadmapEvidence(item="event log", modules=("src/fs_overlay/event_log.py",), symbols=("EventLog",), tests=("tests/test_event_log_recovery.py",)),
    RoadmapEvidence(item="audit command", modules=("src/fs_overlay/storage_engine.py", "src/fs_overlay/cli.py"), symbols=("LocalStorageEngine", "main"), tests=("tests/test_cli.py", "tests/test_storage_integrity.py")),
    RoadmapEvidence(item="recovery command", modules=("src/fs_overlay/storage_engine.py", "src/fs_overlay/cli.py"), symbols=("LocalStorageEngine", "main"), tests=("tests/test_cli.py", "tests/test_storage_transaction_recovery.py")),
    RoadmapEvidence(item="transaction engine implementation", modules=("src/fs_overlay/storage_engine.py",), symbols=("StorageTransaction",), tests=("tests/test_storage_transaction_recovery.py", "tests/test_storage_transaction_commit_failure.py")),
    RoadmapEvidence(item="state/reconciliation engine implementation", modules=("src/fs_overlay/state_primitives.py", "src/fs_overlay/federation_control.py"), symbols=("reconcile", "ControlLoopResult", "safe_stop", "FederationReconciler", "ReconciliationDecision"), tests=("tests/test_state_primitives.py", "tests/test_federation_control.py")),
    RoadmapEvidence(item="resource ownership/lease primitives", modules=("src/fs_overlay/state_primitives.py", "src/fs_overlay/resource_control.py"), symbols=("Lease", "ResourceLease"), tests=("tests/test_state_primitives.py", "tests/test_resource_control.py")),
    RoadmapEvidence(item="causal event metadata", modules=("src/fs_overlay/event_log.py",), symbols=("EventLog",), tests=("tests/test_event_log_recovery.py",)),
    RoadmapEvidence(item="universal object contract implementation", modules=("src/fs_overlay/state_primitives.py",), symbols=("ObjectContract",), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="provenance records", modules=("src/fs_overlay/state_primitives.py",), symbols=("ProvenanceRecord",), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="dependency graph primitives", modules=("src/fs_overlay/state_primitives.py",), symbols=("DependencyGraph", "Dependency"), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="knowledge record primitives", modules=("src/fs_overlay/state_primitives.py",), symbols=("KnowledgeRecord",), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="decision record primitives", modules=("src/fs_overlay/state_primitives.py",), symbols=("DecisionRecord",), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="world-state snapshot primitives", modules=("src/fs_overlay/state_primitives.py",), symbols=("WorldStateSnapshot",), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="unified control-loop primitives", modules=("src/fs_overlay/state_primitives.py",), symbols=("ControlLoopResult", "safe_stop"), tests=("tests/test_state_primitives.py",)),
    RoadmapEvidence(item="capability negotiation", modules=("src/fs_overlay/capability_negotiation.py",), symbols=("CapabilitySet", "NegotiatedCapabilities", "negotiate"), tests=("tests/test_capability_negotiation.py", "tests/test_capability_negotiation_extra.py")),
    RoadmapEvidence(item="local node identity store", modules=("src/fs_overlay/node_identity_store.py",), symbols=("LocalNodeIdentityStore", "SCHEMA_VERSION"), tests=("tests/test_node_identity_store.py",)),
    RoadmapEvidence(item="versioned backend contracts", modules=("src/fs_overlay/backend_contract.py",), symbols=("BackendContract", "BACKEND_CONTRACT_VERSION"), tests=("tests/test_backend_contract.py",)),
    RoadmapEvidence(item="hardware abstraction adapter", modules=("src/fs_overlay/hardware_profile.py",), symbols=("HardwareCapabilityAdapter", "HardwareProfile"), tests=("tests/test_hardware_profile.py",)),
    RoadmapEvidence(item="hardware capability fingerprint", modules=("src/fs_overlay/hardware_profile.py",), symbols=("hardware_capability_fingerprint",), tests=("tests/test_hardware_profile.py",)),
    RoadmapEvidence(item="platform time adapter", modules=("src/fs_overlay/time_fabric.py",), symbols=("PlatformTimeAdapter",), tests=("tests/test_time_fabric.py",)),
    RoadmapEvidence(item="monotonic/logical time adapter", modules=("src/fs_overlay/time_fabric.py",), symbols=("LogicalClock",), tests=("tests/test_time_fabric.py",)),
    # Phase 3 - managed workspaces
    RoadmapEvidence(item="workspace registration", modules=("src/fs_overlay/workspace_registry.py",), symbols=("WorkspaceRegistry", "WorkspaceRecord"), tests=("tests/test_workspace_registry.py",)),
    RoadmapEvidence(item="workspace health state", modules=("src/fs_overlay/workspace_registry.py", "src/fs_overlay/workspace_state.py"), symbols=("WorkspaceHealth", "workspace_health", "WorkspaceState"), tests=("tests/test_workspace_registry.py", "tests/test_workspace_state.py")),
    RoadmapEvidence(item="migration/import workflow", modules=("src/fs_overlay/workspace_migration.py",), symbols=("plan_import", "plan_export", "plan_registered_migration"), tests=("tests/test_workspace_migration.py",)),
    RoadmapEvidence(item="workspace snapshots", modules=("src/fs_overlay/storage_resilience.py",), symbols=("Snapshot", "SnapshotStore"), tests=("tests/test_snapshot_provenance.py",)),
    RoadmapEvidence(item="transactional rollback", modules=("src/fs_overlay/storage_engine.py",), symbols=("StorageTransaction",), tests=("tests/test_storage_transaction_recovery.py",)),
    # Phase 5 - resilience
    RoadmapEvidence(item="self-healing", modules=("src/fs_overlay/self_healing.py",), symbols=("SelfHealingPlanner", "ReplicaObservation"), tests=("tests/test_self_healing.py",)),
    RoadmapEvidence(item="carrier quarantine", modules=("src/fs_overlay/storage_resilience.py",), symbols=("QuarantineLedger", "QuarantineRecord"), tests=("tests/test_storage_resilience.py", "tests/test_quarantine_ledger_json_boundary.py")),
    RoadmapEvidence(item="recovery graph", modules=("src/fs_overlay/storage_resilience.py",), symbols=("RecoveryGraph", "RecoveryNode"), tests=("tests/test_storage_resilience.py",)),
    RoadmapEvidence(item="deterministic recovery planner", modules=("src/fs_overlay/storage_resilience.py",), symbols=("PlacementPlanner", "recovery_state"), tests=("tests/test_storage_resilience.py",)),
    RoadmapEvidence(item="transactional recovery journal", modules=("src/fs_overlay/storage_engine.py",), symbols=("AppendJournal", "StorageTransaction"), tests=("tests/test_storage_transaction_recovery.py", "tests/test_append_journal_durability.py")),
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
    """Map roadmap item text to its checked state."""
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
    roadmap_text = ROADMAP_PATH.read_text(encoding="utf-8")
    roadmap_items = _roadmap_items(roadmap_text)
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
