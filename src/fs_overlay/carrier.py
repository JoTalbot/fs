"""Explicit carrier boundary for future filesystem/storage placements."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class CarrierAdapter(Protocol):
    """A carrier owns approved storage locations; it never expands their scope."""
    name: str
    root: Path

    def put(self, relative_name: str, data: bytes) -> str: ...
    def get(self, relative_name: str) -> bytes: ...
    def delete(self, relative_name: str) -> None: ...
    def contains(self, relative_name: str) -> bool: ...


class LocalDirectoryCarrier:
    """Safe reference carrier restricted to one explicitly configured root."""
    name = "local-directory"

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_name: str) -> Path:
        candidate = (self.root / relative_name).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("carrier path escapes configured root")
        return candidate

    def put(self, relative_name: str, data: bytes) -> str:
        target = self._resolve(relative_name); target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.tmp")
        with temporary.open("wb") as handle:
            handle.write(data); handle.flush()
            import os
            os.fsync(handle.fileno())
        temporary.replace(target)
        return str(target.relative_to(self.root))

    def get(self, relative_name: str) -> bytes:
        return self._resolve(relative_name).read_bytes()

    def delete(self, relative_name: str) -> None:
        target = self._resolve(relative_name)
        if target.exists(): target.unlink()

    def contains(self, relative_name: str) -> bool:
        return self._resolve(relative_name).is_file()
