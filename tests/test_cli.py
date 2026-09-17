"""Qualification of the ``fs-overlay`` command-line entry point."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from fs_overlay import cli
from fs_overlay.cli import main
from fs_overlay.genesis_service import ServiceResponse
from fs_overlay.storage_engine import LocalStorageEngine

_SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")


def _payload(stdout: str) -> dict[str, object]:
    return json.loads(stdout.strip().splitlines()[-1])


def test_storage_audit_reports_empty_root(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["storage", "audit", str(tmp_path)]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["operation"] == "audit"
    assert payload["ok"] is True
    assert payload["objects_checked"] == 0


def test_storage_recover_replays_journal(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    LocalStorageEngine(tmp_path).put(b"recoverable object")
    capsys.readouterr()

    assert main(["storage", "recover", str(tmp_path)]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["objects_after"] == 1


def test_storage_snapshot_publishes_snapshot_identity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    manifest = LocalStorageEngine(tmp_path).put(b"snapshot payload")
    capsys.readouterr()

    assert main(["storage", "snapshot", str(tmp_path), "--generation", "7", "--metadata", "role=carrier"]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["generation"] == 7
    assert payload["objects"] == 1
    assert payload["snapshot_id"]
    assert payload["merkle_root"]
    assert manifest.object_id


@pytest.mark.parametrize("metadata", ["missing-separator", "=empty-key"])
def test_storage_snapshot_rejects_malformed_metadata(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], metadata: str
) -> None:
    code = main(["storage", "snapshot", str(tmp_path), "--metadata", metadata])
    captured = capsys.readouterr()

    assert code == 2
    assert "Traceback" not in captured.err
    assert _payload(captured.err)["ok"] is False
    assert captured.out == ""


def test_genesis_ping_reports_unadmitted_node_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["genesis", "ping", "--node-id", "node-cli"]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["ready"] is False


def test_genesis_admit_flag_is_local_configuration(capsys: pytest.CaptureFixture[str]) -> None:
    """``--admit`` must configure the process, never travel over the transport.

    ``GenesisService`` rejects ``admit`` as an unsupported request operation, so
    a request-based implementation can only ever fail closed. Admission stays a
    local configuration decision at the process boundary.
    """
    assert main(["genesis", "ping", "--node-id", "node-cli", "--admit"]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["ready"] is True


def test_genesis_identity_reports_node_binding(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["genesis", "identity", "--node-id", "node-cli"]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["node_id"] == "node-cli"
    assert payload["protocol_version"] == "1"
    assert payload["public_key_fingerprint"]


def test_genesis_capabilities_reports_observed_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["genesis", "capabilities", "--node-id", "node-cli"]) == 0

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["platform"]


def test_failed_service_response_maps_to_nonzero_exit(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_service(node_id: str, *, admitted: bool = False):
        return SimpleNamespace(
            handle=lambda request: ServiceResponse(False, request["operation"], {}, "node is not admitted")
        )

    monkeypatch.setattr(cli, "_make_service", failing_service)

    assert main(["genesis", "ping"]) == 1

    payload = _payload(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error"] == "node is not admitted"


def test_parser_requires_a_command() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])

    assert excinfo.value.code == 2


def test_serve_announces_bound_loopback_endpoint() -> None:
    code = (
        "import sys;"
        "from fs_overlay.cli import main;"
        "sys.exit(main(['genesis', 'serve', '--node-id', 'node-cli', '--port', '0']))"
    )
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(part for part in (_SRC_PATH, os.environ.get("PYTHONPATH")) if part)}
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    try:
        assert process.stdout is not None
        announcement = process.stdout.readline()
        payload = json.loads(announcement)
        assert payload["ok"] is True
        assert payload["operation"] == "serve"
        assert payload["host"] == "127.0.0.1"
        assert payload["port"] > 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:  # pragma: no cover - defensive
            process.kill()
            process.wait(timeout=10)
