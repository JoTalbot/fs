"""Command-line entry point for the minimal FS Genesis runtime."""
from __future__ import annotations

import argparse
import json
import sys

from .genesis_runtime import build_local_service
from .identity import NodeIdentity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fs-overlay")
    sub = parser.add_subparsers(dest="command", required=True)

    genesis = sub.add_parser("genesis", help="inspect or operate the local Genesis boundary")
    genesis.add_argument("operation", choices=("ping", "identity", "capabilities"))
    genesis.add_argument("--node-id", default="local")
    genesis.add_argument("--admit", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    identity = NodeIdentity.from_public_key(args.node_id, args.node_id.encode("utf-8"))
    service = build_local_service(identity, {})
    if args.admit:
        admission = service.handle({"operation": "admit", "node_id": args.node_id})
        if not admission.ok:
            print(json.dumps({"ok": False, "error": admission.error}), file=sys.stderr)
            return 1
    response = service.handle({"operation": args.operation})
    payload = {"ok": response.ok, "operation": response.operation, **response.data}
    if response.error:
        payload["error"] = response.error
    print(json.dumps(payload, sort_keys=True))
    return 0 if response.ok else 1
