"""Run the roadmap evidence registry as part of the ordinary test suite."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "roadmap_evidence", REPOSITORY_ROOT / "tools" / "roadmap_evidence.py"
)
assert _spec is not None and _spec.loader is not None
roadmap_evidence = importlib.util.module_from_spec(_spec)
# Register before execution: dataclass processing resolves annotations through
# sys.modules.
sys.modules[_spec.name] = roadmap_evidence
_spec.loader.exec_module(roadmap_evidence)


def test_every_roadmap_completion_claim_has_verifiable_evidence() -> None:
    assert roadmap_evidence.check() == []


def test_registry_covers_the_reconciled_baseline() -> None:
    assert len(roadmap_evidence.ROADMAP_EVIDENCE) >= 30
