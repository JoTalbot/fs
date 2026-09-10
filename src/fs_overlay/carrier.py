"""Explicit carrier boundary for filesystem/storage placements."""
from __future__ import annotations

import os
import tempfile
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
        if not relative_name or Path(relative_name).is_absolute():
            raise ValueError("carrier name must be a non-empty relative path")
        candidate = (self.root / relative_name).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise ValueError("carrier path escapes configured root")
        return candidate

    def put(self, relative_name: str, data: bytes) -> str:
        target = self._resolve(relative_name)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            self._fsync_directory(target.parent)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return str(target.relative_to(self.root))

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        try:
            fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        except OSError:
            pass

    def get(self, relative_name: str) -> bytes:
        return self._resolve(relative_name).read_bytes()

    def delete(self, relative_name: str) -> None:
        target = self._resolve(relative_name)
        if target.exists():
            target.unlink()
            self._fsync_directory(target.parent)

    def contains(self, relative_name: str) -> bool:
        return self._resolve(relative_name).is_file()
