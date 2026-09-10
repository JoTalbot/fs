"""Command-line entry point for FS Genesis and local storage operations."""
from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path

from .genesis_runtime import build_local_service
from .genesis_server import GenesisServer
from .identity import NodeIdentity
from .storage_engine import LocalStorageEngine
from .storage_resilience import SnapshotStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fs-overlay")
    sub = parser.add_subparsers(dest="command", required=True)

    genesis = sub.add_parser("genesis", help="inspect or operate the local Genesis boundary")
    genesis.add_argument("operation", choices=("ping", "identity", "capabilities", "serve"))
    genesis.add_argument("--node-id", default="local")
    genesis.add_argument("--admit", action="store_true")
    genesis.add_argument("--port", type=int, default=0, help="loopback TCP port; 0 selects an ephemeral port")

    storage = sub.add_parser("storage", help="audit, recover, or snapshot a local FS storage root")
    storage.add_argument("operation", choices=("audit", "recover", "snapshot"))
    storage.add_argument("root", type=Path)
    storage.add_argument("--generation", type=int, default=0)
    storage.add_argument("--metadata", action="append", default=[], metavar="KEY=VALUE")
    return parser


def _make_service(node_id: str):
    identity = NodeIdentity.from_public_key(node_id, node_id.encode("utf-8"))
    return build_local_service(identity, None)


def _print_response(response) -> int:
    payload = {"ok": response.ok, "operation": response.operation, **response.data}
    if response.error:
        payload["error"] = response.error
    print(json.dumps(payload, sort_keys=True))
    return 0 if response.ok else 1


def _metadata(values: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ValueError("metadata must use KEY=VALUE")
        key, item = value.split("=", 1)
        if not key:
            raise ValueError("metadata key must not be empty")
        result[key] = item
    return result


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "storage":
        engine = LocalStorageEngine(args.root)
        if args.operation == "snapshot":
            metadata = _metadata(args.metadata)
            snapshot = SnapshotStore(args.root / "snapshots").create(
                engine.inventory.records.keys(), generation=args.generation,
                metadata=metadata or None,
            )
            print(json.dumps({"operation": "snapshot", "ok": True,
                              "snapshot_id": snapshot.snapshot_id,
                              "generation": snapshot.generation,
                              "objects": len(snapshot.objects),
                              "merkle_root": snapshot.merkle_root}, sort_keys=True))
            return 0
        result = getattr(engine, args.operation)()
        print(json.dumps({"operation": args.operation, **result}, sort_keys=True))
        return 0 if result.get("ok") else 1

    service = _make_service(args.node_id)
    if args.operation == "serve":
        if args.admit:
            admission = service.handle({"operation": "admit", "node_id": args.node_id})
            if not admission.ok:
                print(json.dumps({"ok": False, "error": admission.error}), file=sys.stderr)
                return 1
        server = GenesisServer(service, port=args.port)
        host, port = server.start()
        print(json.dumps({"ok": True, "operation": "serve", "host": host, "port": port}, sort_keys=True), flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            return 0
        finally:
            server.stop()
        return 0

    if args.admit:
        admission = service.handle({"operation": "admit", "node_id": args.node_id})
        if not admission.ok:
            print(json.dumps({"ok": False, "error": admission.error}), file=sys.stderr)
            return 1
    return _print_response(service.handle({"operation": args.operation}))
